/**
 * Las formas que toman las partículas, una por etapa de la historia.
 * Cada forma es un Float32Array de N vec4 (x, y, z, tamaño) y otro de N vec4 (r, g, b, brillo).
 * Se calculan una vez en la CPU; la GPU solo interpola entre ellas.
 *
 * Unidades de mundo: la cámara está en z = 10 con fov 35, así que se ven ~6,3 unidades de alto.
 */

export const STAGES = ["cristal", "archivo", "huella", "arbol", "raiz", "sello", "verificacion"] as const;
export type StageName = (typeof STAGES)[number];

type RGB = [number, number, number];

// Colores en espacio lineal; los valores > 1 son los que toma el bloom.
const ICE: RGB = [0.78, 0.9, 1.15];
const ICE_DIM: RGB = [0.32, 0.4, 0.58];
const DUST: RGB = [0.16, 0.2, 0.32];
const AMBER: RGB = [1.9, 0.86, 0.16];
const AMBER_DIM: RGB = [0.7, 0.34, 0.08];
const GREEN: RGB = [0.45, 1.6, 0.8];

/** Pseudoaleatorio determinista (mulberry32): la escena es igual en cada visita. */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

class Writer {
  pos: Float32Array;
  col: Float32Array;
  i = 0;
  constructor(public n: number) {
    this.pos = new Float32Array(n * 4);
    this.col = new Float32Array(n * 4);
  }
  put(x: number, y: number, z: number, size: number, c: RGB, glow = 1) {
    if (this.i >= this.n) return;
    const k = this.i * 4;
    this.pos[k] = x;
    this.pos[k + 1] = y;
    this.pos[k + 2] = z;
    this.pos[k + 3] = size;
    this.col[k] = c[0] * glow;
    this.col[k + 1] = c[1] * glow;
    this.col[k + 2] = c[2] * glow;
    this.col[k + 3] = 1;
    this.i++;
  }
  get left() {
    return this.n - this.i;
  }
}

/** El ~8 % de las partículas es polvo de fondo, en el mismo lugar en todas las etapas: el espacio no se vacía nunca. */
function dust(w: Writer, count: number) {
  const r = rng(7);
  for (let j = 0; j < count; j++) {
    const x = (r() - 0.5) * 22;
    const y = (r() - 0.5) * 13;
    const z = -2 - r() * 8;
    w.put(x, y, z, 0.6 + r() * 1.4, DUST, 0.6 + r() * 0.8);
  }
}

/* ------------------------------------------------------------------ */
/* Geometrías auxiliares */

const PHI = (1 + Math.sqrt(5)) / 2;
const ICO_V: [number, number, number][] = [
  [-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0],
  [0, -1, PHI], [0, 1, PHI], [0, -1, -PHI], [0, 1, -PHI],
  [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1],
].map(([x, y, z]) => {
  const l = Math.hypot(x, y, z);
  return [x / l, y / l, z / l] as [number, number, number];
});
const ICO_F = [
  [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
  [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
  [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
  [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
];
const ICO_E: [number, number][] = (() => {
  const set = new Set<string>();
  const out: [number, number][] = [];
  for (const [a, b, c] of ICO_F) {
    for (const [p, q] of [[a, b], [b, c], [c, a]]) {
      const key = p < q ? `${p}-${q}` : `${q}-${p}`;
      if (!set.has(key)) {
        set.add(key);
        out.push([p, q]);
      }
    }
  }
  return out;
})();

/** Cristal: aristas brillantes de un icosaedro, caras tenues y un núcleo denso. */
function crystal(w: Writer, count: number, opts: { cx?: number; cy?: number; radius: number; edge: RGB; face: RGB; core: RGB; seed: number }) {
  const { cx = 0, cy = 0, radius, edge, face, core, seed } = opts;
  const r = rng(seed);
  const nEdge = Math.floor(count * 0.42);
  const nFace = Math.floor(count * 0.33);
  const nCore = count - nEdge - nFace;
  for (let j = 0; j < nEdge; j++) {
    const [a, b] = ICO_E[j % ICO_E.length];
    const t = r();
    const p = ICO_V[a].map((v, k) => v + (ICO_V[b][k] - v) * t);
    const jx = (r() - 0.5) * 0.02;
    w.put(cx + p[0] * radius + jx, cy + p[1] * radius + jx, p[2] * radius, 1.1 + r() * 0.8, edge, 1.1);
  }
  for (let j = 0; j < nFace; j++) {
    const [a, b, c] = ICO_F[j % ICO_F.length];
    let u = r();
    let v = r();
    if (u + v > 1) {
      u = 1 - u;
      v = 1 - v;
    }
    const p = [0, 1, 2].map((k) => ICO_V[a][k] + (ICO_V[b][k] - ICO_V[a][k]) * u + (ICO_V[c][k] - ICO_V[a][k]) * v);
    w.put(cx + p[0] * radius, cy + p[1] * radius, p[2] * radius, 0.7 + r() * 0.6, face, 0.6);
  }
  for (let j = 0; j < nCore; j++) {
    // Distribución concentrada en el centro: el núcleo brilla.
    const rad = Math.pow(r(), 2.2) * radius * 0.42;
    const th = r() * Math.PI * 2;
    const ph = Math.acos(2 * r() - 1);
    w.put(cx + rad * Math.sin(ph) * Math.cos(th), cy + rad * Math.cos(ph), rad * Math.sin(ph) * Math.sin(th), 1.2 + r(), core, 1.3);
  }
}

function ring(w: Writer, count: number, opts: { cx?: number; cy?: number; radius: number; tiltX: number; tiltZ: number; c: RGB; seed: number }) {
  const r = rng(opts.seed);
  const { cx = 0, cy = 0 } = opts;
  for (let j = 0; j < count; j++) {
    const a = (j / count) * Math.PI * 2 + r() * 0.01;
    const rad = opts.radius + (r() - 0.5) * 0.04;
    let x = Math.cos(a) * rad;
    let y = 0;
    let z = Math.sin(a) * rad;
    // inclinación en X
    const y1 = y * Math.cos(opts.tiltX) - z * Math.sin(opts.tiltX);
    const z1 = y * Math.sin(opts.tiltX) + z * Math.cos(opts.tiltX);
    y = y1;
    z = z1;
    // inclinación en Z
    const x2 = x * Math.cos(opts.tiltZ) - y * Math.sin(opts.tiltZ);
    const y2 = x * Math.sin(opts.tiltZ) + y * Math.cos(opts.tiltZ);
    x = x2;
    y = y2;
    w.put(cx + x, cy + y, z, 0.9 + r() * 0.5, opts.c, 1);
  }
}

function segment(w: Writer, count: number, a: number[], b: number[], c: RGB, glow: number, r: () => number, jitter = 0.018) {
  for (let j = 0; j < count; j++) {
    const t = r();
    w.put(
      a[0] + (b[0] - a[0]) * t + (r() - 0.5) * jitter,
      a[1] + (b[1] - a[1]) * t + (r() - 0.5) * jitter,
      a[2] + (b[2] - a[2]) * t + (r() - 0.5) * jitter,
      0.8 + r() * 0.6,
      c,
      glow,
    );
  }
}

function ball(w: Writer, count: number, center: number[], radius: number, c: RGB, glow: number, r: () => number) {
  for (let j = 0; j < count; j++) {
    const rad = Math.cbrt(r()) * radius;
    const th = r() * Math.PI * 2;
    const ph = Math.acos(2 * r() - 1);
    w.put(
      center[0] + rad * Math.sin(ph) * Math.cos(th),
      center[1] + rad * Math.cos(ph),
      center[2] + rad * Math.sin(ph) * Math.sin(th),
      1 + r() * 0.8,
      c,
      glow,
    );
  }
}

/* ------------------------------------------------------------------ */
/* Árbol de 8 hojas, compartido por "árbol" y "verificación" */

type TreeNode = { p: number[]; level: number; parent: number | null };

function treeNodes(): TreeNode[] {
  const ys = [-1.85, -0.6, 0.65, 1.9];
  const zs = [0.35, -0.25, 0.15, -0.4, 0.3, -0.15, 0.4, -0.3];
  const nodes: TreeNode[] = [];
  for (let i = 0; i < 8; i++) nodes.push({ p: [-2.8 + i * 0.8, ys[0], zs[i]], level: 0, parent: null });
  let start = 0;
  let size = 8;
  for (let level = 1; level <= 3; level++) {
    const next = nodes.length;
    for (let i = 0; i < size / 2; i++) {
      const a = nodes[start + i * 2];
      const b = nodes[start + i * 2 + 1];
      const idx = nodes.length;
      a.parent = idx;
      b.parent = idx;
      nodes.push({ p: [(a.p[0] + b.p[0]) / 2, ys[level], ((a.p[2] + b.p[2]) / 2) * 0.5], level, parent: null });
    }
    start = next;
    size /= 2;
  }
  return nodes;
}

const TREE = treeNodes();
const ROOT = TREE.length - 1;
/** Camino de la prueba para la hoja 3 (índice 2): hoja → nodo → nodo → raíz. */
const PROOF_LEAF = 2;
const proofPath = (() => {
  const path = new Set<number>([PROOF_LEAF]);
  let n = TREE[PROOF_LEAF].parent;
  while (n !== null) {
    path.add(n);
    n = TREE[n].parent;
  }
  return path;
})();
/** Hermanos que aporta la prueba: uno por nivel. */
const proofSiblings = (() => {
  const out = new Set<number>();
  for (const idx of proofPath) {
    const parent = TREE[idx].parent;
    if (parent === null) continue;
    const sibling = TREE.findIndex((n, i) => n.parent === parent && i !== idx);
    out.add(sibling);
  }
  return out;
})();

function tree(w: Writer, count: number, mode: "build" | "verify") {
  const r = rng(mode === "build" ? 11 : 13);
  const edges = TREE.flatMap((n, i) => (n.parent === null ? [] : [[i, n.parent] as [number, number]]));
  const nNodes = Math.floor(count * 0.45);
  const perEdge = Math.floor((count - nNodes) / edges.length);

  for (const [child, parent] of edges) {
    const onPath = mode === "verify" && proofPath.has(child) && proofPath.has(parent);
    const c = mode === "verify" ? (onPath ? GREEN : ICE_DIM) : ICE;
    segment(w, perEdge, TREE[child].p, TREE[parent].p, c, onPath ? 1.4 : mode === "verify" ? 0.7 : 0.9, r);
  }

  // Más partículas en los nodos más altos: la raíz es la más densa.
  const weights = TREE.map((n, i) => (i === ROOT ? 5 : 1 + n.level * 0.6));
  const total = weights.reduce((a, b) => a + b, 0);
  TREE.forEach((n, i) => {
    const k = i === TREE.length - 1 ? w.left : Math.floor((weights[i] / total) * nNodes);
    const radius = i === ROOT ? 0.32 : n.level === 0 ? 0.13 : 0.15;
    let c: RGB = ICE;
    let glow = i === ROOT ? 1.5 : 1.1;
    if (mode === "verify") {
      if (i === ROOT) {
        c = AMBER;
        glow = 1.2;
      } else if (proofPath.has(i)) {
        c = GREEN;
        glow = 1.3;
      } else if (proofSiblings.has(i)) {
        c = GREEN;
        glow = 0.55;
      } else {
        c = ICE_DIM;
        glow = 0.8;
      }
    }
    ball(w, k, n.p, radius, c, glow, r);
  });
}

/* ------------------------------------------------------------------ */
/* Etapas */

function stageCrystal(w: Writer) {
  const n = w.left;
  crystal(w, Math.floor(n * 0.7), { radius: 1.35, edge: ICE, face: ICE_DIM, core: AMBER, seed: 21 });
  ring(w, Math.floor(n * 0.17), { radius: 2.15, tiltX: 1.25, tiltZ: 0.25, c: AMBER_DIM, seed: 22 });
  ring(w, w.left, { radius: 2.75, tiltX: 1.1, tiltZ: -0.35, c: AMBER_DIM, seed: 23 });
}

function stageDocument(w: Writer) {
  const r = rng(31);
  const W = 2.5;
  const H = 3.3;
  const n = w.left;
  const nBorder = Math.floor(n * 0.16);
  const nFold = Math.floor(n * 0.05);
  const fold = 0.5;
  // Contorno, sin la esquina doblada.
  const outline = [
    [-W / 2, -H / 2], [W / 2, -H / 2], [W / 2, H / 2 - fold], [W / 2 - fold, H / 2], [-W / 2, H / 2], [-W / 2, -H / 2],
  ];
  const lens = outline.slice(1).map((p, i) => Math.hypot(p[0] - outline[i][0], p[1] - outline[i][1]));
  const per = lens.reduce((a, b) => a + b, 0);
  for (let j = 0; j < nBorder; j++) {
    let d = r() * per;
    let s = 0;
    while (d > lens[s]) d -= lens[s++];
    const a = outline[s];
    const b = outline[s + 1];
    const t = d / lens[s];
    w.put(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, (r() - 0.5) * 0.04, 1.1, ICE, 1.2);
  }
  // La esquina doblada.
  for (let j = 0; j < nFold; j++) {
    let u = r();
    let v = r();
    if (u + v > 1) {
      u = 1 - u;
      v = 1 - v;
    }
    const ax = W / 2 - fold;
    const ay = H / 2;
    w.put(ax + fold * u, ay - fold * v - fold * u, 0.02, 0.8, ICE_DIM, 0.9);
  }
  // Renglones de texto: un título y párrafos.
  const lines: [number, number, number][] = [];
  let y = H / 2 - 0.42;
  lines.push([y, 1.25, 1.4]);
  y -= 0.36;
  for (let p = 0; p < 4; p++) {
    const rows = 3 + Math.floor(r() * 2);
    for (let k = 0; k < rows; k++) {
      lines.push([y, k === rows - 1 ? 0.8 + r() * 0.6 : 1.85 + r() * 0.15, 0.9]);
      y -= 0.17;
    }
    y -= 0.13;
  }
  const nLines = w.left;
  const lenTotal = lines.reduce((a, l) => a + l[1], 0);
  for (const [ly, len, glow] of lines) {
    const k = Math.floor((len / lenTotal) * nLines);
    for (let j = 0; j < k; j++) {
      w.put(-W / 2 + 0.3 + r() * len, ly + (r() - 0.5) * 0.045, (r() - 0.5) * 0.03, 0.9, ICE, glow);
    }
  }
  while (w.left > 0) w.put(-W / 2 + 0.3 + r() * 1.8, -H / 2 + 0.4 + r() * 0.1, 0, 0.8, ICE_DIM, 0.8);
}

/** La huella: 64 barras, una por carácter hex del SHA-256, con la altura de su valor. */
function stageFingerprint(w: Writer, hashHex: string) {
  const r = rng(41);
  const width = 6.6;
  const step = width / 64;
  const n = w.left;
  const heights = hashHex.split("").map((ch) => 0.35 + (parseInt(ch, 16) / 15) * 2.4);
  const total = heights.reduce((a, b) => a + b, 0);
  heights.forEach((h, i) => {
    const k = i === 63 ? w.left : Math.floor((h / total) * n);
    const x = -width / 2 + step * (i + 0.5);
    for (let j = 0; j < k; j++) {
      w.put(x + (r() - 0.5) * step * 0.55, (r() - 0.5) * h, (r() - 0.5) * 0.08, 0.9 + r() * 0.5, ICE, 1 + (h / 2.75) * 0.4);
    }
  });
}

function stageRoot(w: Writer) {
  crystal(w, w.left, { radius: 1.75, edge: ICE, face: ICE_DIM, core: ICE, seed: 51 });
}

function stageSeal(w: Writer) {
  const r = rng(61);
  const n = w.left;
  // Tres bloques de la cadena; el del medio contiene la raíz.
  const size = 1.7;
  const centers = [-3.1, 0, 3.1];
  const nBlocks = Math.floor(n * 0.42);
  const corners = (cx: number) => {
    const h = size / 2;
    const c: number[][] = [];
    for (const x of [-h, h]) for (const y of [-h, h]) for (const z of [-h, h]) c.push([cx + x, y, z]);
    return c;
  };
  const cubeEdges: [number, number][] = [
    [0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7],
  ];
  centers.forEach((cx, b) => {
    const cs = corners(cx);
    const k = Math.floor(nBlocks / 3);
    const color = b === 1 ? AMBER : ICE_DIM;
    for (let j = 0; j < k; j++) {
      const [a, bb] = cubeEdges[j % 12];
      segment(w, 1, cs[a], cs[bb], color, b === 1 ? 1.1 : 0.8, r, 0.01);
    }
  });
  // Eslabones entre bloques.
  const nLinks = Math.floor(n * 0.05);
  segment(w, nLinks / 2, [centers[0] + size / 2, 0, 0], [centers[1] - size / 2, 0, 0], AMBER_DIM, 0.9, r, 0.01);
  segment(w, nLinks / 2, [centers[1] + size / 2, 0, 0], [centers[2] - size / 2, 0, 0], AMBER_DIM, 0.9, r, 0.01);
  // La raíz, ahora sellada.
  crystal(w, Math.floor(n * 0.33), { radius: 0.62, edge: AMBER, face: AMBER_DIM, core: AMBER, seed: 62 });
  ring(w, w.left, { radius: 1.3, tiltX: 1.2, tiltZ: 0.3, c: AMBER_DIM, seed: 63 });
}

/**
 * Construye las 7 etapas en dos buffers contiguos: la etapa k ocupa [k·N, (k+1)·N).
 * `hashHex` es un SHA-256 real: el de la frase del hero.
 */
export function buildShapes(n: number, hashHex: string) {
  const K = STAGES.length;
  const pos = new Float32Array(K * n * 4);
  const col = new Float32Array(K * n * 4);
  const nDust = Math.floor(n * 0.08);

  const builders: ((w: Writer) => void)[] = [
    stageCrystal,
    stageDocument,
    (w) => stageFingerprint(w, hashHex),
    (w) => tree(w, w.left, "build"),
    stageRoot,
    stageSeal,
    (w) => tree(w, w.left, "verify"),
  ];

  builders.forEach((build, k) => {
    const w = new Writer(n);
    dust(w, nDust);
    build(w);
    // Por redondeos puede quedar alguna partícula libre: va al polvo.
    const r = rng(99 + k);
    while (w.left > 0) w.put((r() - 0.5) * 22, (r() - 0.5) * 13, -3 - r() * 6, 0.8, DUST, 0.6);
    pos.set(w.pos, k * n * 4);
    col.set(w.col, k * n * 4);
  });

  return { pos, col, stages: K };
}
