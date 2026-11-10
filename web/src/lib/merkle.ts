/**
 * Árbol de Merkle según RFC 6962, igual que el núcleo de Hashly (package.py):
 * - hoja:  SHA-256(0x00 ‖ bytes del archivo)
 * - nodo:  SHA-256(0x01 ‖ izquierdo ‖ derecho)
 * - el subárbol izquierdo tiene k hojas, con k la mayor potencia de dos < n
 * - nunca se duplica el último nodo; con un solo archivo, la raíz es su hoja.
 *
 * Todo corre con Web Crypto: los bytes nunca salen del navegador.
 */

const LEAF_PREFIX = 0x00;
const NODE_PREFIX = 0x01;

export type MerkleNode = {
  id: string;
  hash: string;
  kind: "leaf" | "node";
  depth: number;
  /** Índices [inicio, fin) de las hojas que cubre. */
  span: [number, number];
  children?: [MerkleNode, MerkleNode];
  /** Solo en hojas. */
  fileName?: string;
};

export function toHex(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let out = "";
  for (let i = 0; i < bytes.length; i++) out += bytes[i].toString(16).padStart(2, "0"); // taste-skill-ignore: codificación hex
  return out;
}

function fromHex(hex: string): Uint8Array {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return out;
}

async function sha256(data: Uint8Array): Promise<string> {
  return toHex(await crypto.subtle.digest("SHA-256", data as BufferSource));
}

export async function leafHash(bytes: ArrayBuffer): Promise<string> {
  const data = new Uint8Array(bytes.byteLength + 1);
  data[0] = LEAF_PREFIX;
  data.set(new Uint8Array(bytes), 1);
  return sha256(data);
}

export async function nodeHash(leftHex: string, rightHex: string): Promise<string> {
  const data = new Uint8Array(65);
  data[0] = NODE_PREFIX;
  data.set(fromHex(leftHex), 1);
  data.set(fromHex(rightHex), 33);
  return sha256(data);
}

export function largestPowerOfTwoBelow(n: number): number {
  let k = 1;
  while (2 * k < n) k *= 2;
  return k;
}

export type Leaf = { hash: string; fileName: string };

export async function buildTree(leaves: Leaf[], depth = 0, offset = 0): Promise<MerkleNode> {
  const n = leaves.length;
  if (n === 0) throw new Error("El árbol necesita al menos una hoja");

  if (n === 1) {
    return {
      id: `l${offset}`,
      hash: leaves[0].hash,
      kind: "leaf",
      depth,
      span: [offset, offset + 1],
      fileName: leaves[0].fileName,
    };
  }

  const k = largestPowerOfTwoBelow(n);
  const [left, right] = await Promise.all([
    buildTree(leaves.slice(0, k), depth + 1, offset),
    buildTree(leaves.slice(k), depth + 1, offset + k),
  ]);

  return {
    id: `n${offset}-${offset + n}`,
    hash: await nodeHash(left.hash, right.hash),
    kind: "node",
    depth,
    span: [offset, offset + n],
    children: [left, right],
  };
}

/** Recorre el árbol en orden: primero los hijos, después el padre. */
export function flatten(root: MerkleNode): MerkleNode[] {
  const out: MerkleNode[] = [];
  const walk = (node: MerkleNode) => {
    node.children?.forEach(walk);
    out.push(node);
  };
  walk(root);
  return out;
}

export function treeHeight(root: MerkleNode): number {
  return flatten(root).reduce((max, node) => Math.max(max, node.depth), 0);
}

/** El servicio ordena los archivos por nombre sin distinguir mayúsculas. */
export function sortByName<T extends { name: string }>(files: T[]): T[] {
  return [...files].sort((a, b) => {
    const x = a.name.toLowerCase();
    const y = b.name.toLowerCase();
    return x < y ? -1 : x > y ? 1 : 0;
  });
}

/** SHA-256 simple (sin prefijo), el mismo que da `sha256sum`. */
export async function sha256Hex(bytes: ArrayBuffer | Uint8Array): Promise<string> {
  return toHex(await crypto.subtle.digest("SHA-256", bytes as BufferSource));
}
