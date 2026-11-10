/** Cliente del API de Hashly. La web es el primer cliente del mismo API público. */

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

const TOKEN_KEY = "hashly.token";

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* almacenamiento bloqueado: la sesión dura lo que dure la pestaña */
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export type Seal = {
  status: "creating" | "pending" | "confirmed" | "failed";
  bitcoin_block_height: number | null;
  confirmed_at: string | null;
} | null;

export type ManifestEntry = { index: number; filename: string; hash: string };

export type PackageSummary = {
  id: number;
  name: string;
  created_at: string;
  merkle_root: string;
  verification_method: string;
  seal: Seal;
};

export type PackageDetail = PackageSummary & { manifest: ManifestEntry[] };

export type PublicPackage = {
  id: number;
  created_at: string;
  verification_method: string;
  seal: Seal;
};

export type SearchResult = { found: boolean; merkle_root: string; packages: PublicPackage[] };

export type ApiKeyRow = {
  id: number;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
  revoked: boolean;
};

export type FileProof = {
  filename: string;
  leaf_hash: string;
  merkle_root: string;
  proof: { hash: string; position: "left" | "right" }[];
};

function detailOf(body: unknown): string {
  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d?.msg).filter(Boolean).join(". ");
  return "Algo salió mal";
}

async function request<T>(path: string, init: RequestInit = {}, auth = true): Promise<T> {
  const headers = new Headers(init.headers);
  const token = auth ? getToken() : null;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el API. ¿Está corriendo?");
  }

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, detailOf(body));
  return body as T;
}

const json = (data: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

function filesForm(files: File[], extra: Record<string, string> = {}) {
  const form = new FormData();
  for (const [k, v] of Object.entries(extra)) form.append(k, v);
  for (const f of files) form.append("files", f, f.name);
  return form;
}

export const api = {
  register: (email: string, password: string) => request("/v1/users/register", json({ email, password }), false),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/v1/users/login", json({ email, password }), false),
  me: () => request<{ id: number; email: string }>("/v1/users/me"),

  packages: () => request<PackageSummary[]>("/v1/packages/"),
  createPackage: (name: string, files: File[]) =>
    request<PackageDetail>("/v1/packages/", { method: "POST", body: filesForm(files, { name, method: "ots" }) }),
  package: (id: number) => request<PackageDetail>(`/v1/packages/${id}`),
  fileProof: (id: number, filename: string) =>
    request<FileProof>(`/v1/packages/${id}/proof/${encodeURIComponent(filename)}`),
  otsProofUrl: (id: number) => `${API_URL}/v1/packages/${id}/ots-proof`,

  keys: () => request<ApiKeyRow[]>("/v1/keys/"),
  createKey: (name: string) => request<ApiKeyRow & { key: string }>("/v1/keys/", json({ name })),
  revokeKey: (id: number) => request<void>(`/v1/keys/${id}`, { method: "DELETE" }),

  joinWaitlist: (email: string, interest: "contrato" | "bitcoin" = "contrato") =>
    request<{ ok: boolean }>("/v1/waitlist/", json({ email, interest }), false),

  searchRoot: (merkle_root: string) =>
    request<SearchResult>("/v1/packages/search/merkle-root", json({ merkle_root }), false),
  searchFiles: (files: File[]) =>
    request<SearchResult>("/v1/packages/search/package", { method: "POST", body: filesForm(files) }, false),
};
