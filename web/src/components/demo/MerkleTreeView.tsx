"use client";

import { useMemo } from "react";
import { motion } from "motion/react";
import clsx from "clsx";
import { flatten, treeHeight, type MerkleNode } from "@/lib/merkle";

const COL = 76;
const ROW = 92;
const PAD_X = 46;
const PAD_TOP = 40;
const PAD_BOTTOM = 56;

type Props = {
  root: MerkleNode;
  selectedId: string | null;
  onSelect: (node: MerkleNode) => void;
  reduced: boolean;
};

type Placed = MerkleNode & { x: number; y: number };

export function describeNode(node: MerkleNode, leafCount: number): string {
  if (node.kind === "leaf") return `Hoja ${node.span[0] + 1}: ${node.fileName}`;
  const [a, b] = node.span;
  const scope = `hojas ${a + 1} a ${b}`;
  return node.depth === 0 ? `Raíz: combina las ${leafCount} hojas` : `Nodo: combina las ${scope}`;
}

/**
 * Dibuja el árbol con la forma real de RFC 6962: si el número de hojas no es
 * potencia de dos, la última hoja sube de nivel en vez de duplicarse.
 */
export function MerkleTreeView({ root, selectedId, onSelect, reduced }: Props) {
  const { nodes, width, height, leafCount } = useMemo(() => {
    const all = flatten(root);
    const leafCount = root.span[1];
    const h = treeHeight(root);
    const placed = new Map<string, Placed>();
    for (const node of all) {
      const x = node.children
        ? (placed.get(node.children[0].id)!.x + placed.get(node.children[1].id)!.x) / 2
        : PAD_X + node.span[0] * COL;
      placed.set(node.id, { ...node, x, y: PAD_TOP + node.depth * ROW });
    }
    return {
      nodes: [...placed.values()],
      width: PAD_X * 2 + (leafCount - 1) * COL,
      height: PAD_TOP + h * ROW + PAD_BOTTOM,
      leafCount,
      maxDepth: h,
    };
  }, [root]);

  const maxDepth = Math.max(...nodes.map((n) => n.depth));
  // Se construye de abajo hacia arriba: primero las hojas más profundas.
  const delayFor = (depth: number) => (reduced ? 0 : (maxDepth - depth) * 0.22);
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const showLabels = leafCount <= 10;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className="mx-auto block max-w-none overflow-visible md:max-w-full"
      role="group"
      aria-label={`Árbol de Merkle con ${leafCount} ${leafCount === 1 ? "hoja" : "hojas"}`}
    >
      {nodes.flatMap((node) =>
        (node.children ?? []).map((child) => {
          const c = byId.get(child.id)!;
          return (
            <motion.line
              key={`${node.id}-${child.id}`}
              x1={c.x}
              y1={c.y}
              x2={node.x}
              y2={node.y}
              stroke="var(--ink)"
              strokeOpacity={0.45}
              strokeWidth={1.5}
              initial={reduced ? false : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.35, delay: delayFor(c.depth) + 0.12, ease: "easeOut" }}
            />
          );
        }),
      )}

      {nodes.map((node) => {
        const isRoot = node.id === root.id;
        const selected = node.id === selectedId;
        const r = isRoot ? 15 : node.kind === "leaf" ? 10 : 8;
        return (
          <motion.g
            key={node.id}
            tabIndex={0}
            role="button"
            aria-pressed={selected}
            aria-label={`${describeNode(node, leafCount)}. Hash ${node.hash}`}
            onClick={() => onSelect(node)}
            onFocus={() => onSelect(node)}
            onMouseEnter={() => onSelect(node)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(node);
              }
            }}
            className="cursor-pointer outline-none [&:focus-visible_.ring]:opacity-100"
            initial={reduced ? false : { opacity: 0, scale: 0.4 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: delayFor(node.depth), ease: [0.16, 1, 0.3, 1] }}
            style={{ transformOrigin: `${node.x}px ${node.y}px`, transformBox: "view-box" }}
          >
            {/* Área de toque generosa, invisible. */}
            <circle cx={node.x} cy={node.y} r={22} fill="transparent" />
            <circle className="ring opacity-0 transition-opacity" cx={node.x} cy={node.y} r={r + 7} stroke="var(--ink)" strokeWidth={2} fill="none" />
            {isRoot && <circle cx={node.x} cy={node.y} r={34} fill="var(--ink)" opacity={0.12} />}
            {node.kind === "leaf" ? (
              <rect
                x={node.x - r}
                y={node.y - r}
                width={r * 2}
                height={r * 2}
                rx={4}
                fill={selected ? "var(--ink)" : "var(--surface)"}
                stroke="var(--ink)"
                strokeWidth={2}
                transform={`rotate(45 ${node.x} ${node.y})`}
              />
            ) : (
              <circle cx={node.x} cy={node.y} r={r} fill={selected || isRoot ? "var(--ink)" : "var(--surface)"} stroke="var(--ink)" strokeWidth={2} />
            )}
            {showLabels && (
              <text
                x={node.x}
                y={node.kind === "leaf" ? node.y + 30 : node.y - r - 10}
                textAnchor="middle"
                className={clsx("hash pointer-events-none", selected ? "fill-ink" : "fill-muted")}
                fontSize={11}
              >
                {node.hash.slice(0, 6)}
              </text>
            )}
            {showLabels && node.kind === "leaf" && (
              <text x={node.x} y={node.y + 46} textAnchor="middle" className="pointer-events-none fill-muted" fontSize={11}>
                {truncate(node.fileName ?? "", 11)}
              </text>
            )}
          </motion.g>
        );
      })}
    </svg>
  );
}

function truncate(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}
