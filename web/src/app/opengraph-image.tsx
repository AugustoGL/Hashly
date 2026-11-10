import { ImageResponse } from "next/og";

export const alt = "Hashly: Probá que existía. Un cristal de luz sellado en ámbar.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#070b16",
          color: "#eef2fa",
          padding: 64,
          fontFamily: "serif",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 30, letterSpacing: 2 }}>
          <span>HASHLY</span>
          <span style={{ color: "#a3adc2", fontFamily: "sans-serif", fontSize: 26, letterSpacing: 0 }}>Sellado en Bitcoin</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: 120, lineHeight: 1 }}>PROBÁ QUE</span>
          <div style={{ width: 260, height: 170, background: "#0e1424", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 70, height: 70, background: "#f7931a", transform: "rotate(45deg)" }} />
          </div>
          <span style={{ fontSize: 120, lineHeight: 1 }}>EXISTÍA.</span>
        </div>
        <div style={{ display: "flex", fontFamily: "sans-serif", fontSize: 30, color: "#eef2fa", maxWidth: 800 }}>
          Una huella de 32 bytes, sellada en Bitcoin. Los archivos nunca se guardan.
        </div>
      </div>
    ),
    size,
  );
}
