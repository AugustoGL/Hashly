import * as THREE from "three/webgpu";
import {
  Fn,
  float,
  instanceIndex,
  instancedArray,
  mix,
  mx_noise_vec3,
  smoothstep,
  time,
  uniform,
  uv,
  vec3,
  vec4,
  pass,
  clamp,
  sin,
} from "three/tsl";
import { bloom } from "three/addons/tsl/display/BloomNode.js";
import { buildShapes } from "./shapes";

/**
 * Motor de partículas en WebGPU (con caída automática a WebGL 2):
 * - las 7 formas viven en dos buffers de almacenamiento en la GPU;
 * - un compute shader mueve cada partícula hacia la mezcla de dos formas,
 *   con turbulencia de ruido a mitad de camino;
 * - se dibujan como sprites instanciados con mezcla aditiva y bloom.
 * La etapa es un número continuo (0..6) que maneja el scroll.
 */

export type Engine = {
  setStage: (stage: number) => void;
  setPointer: (x: number, y: number) => void;
  /** Inclinación del teléfono: gira la escena, sin empujar partículas. */
  setTilt: (x: number, y: number) => void;
  /** Dónde se dibuja la escena: desplazamiento en unidades de mundo y escala. */
  setLayout: (x: number, y: number, scale: number) => void;
  /** Media altura visible en el plano z = 0, en unidades de mundo (para encuadrar desde el DOM). */
  viewHalfHeight: () => number;
  setRunning: (running: boolean) => void;
  dispose: () => void;
  backend: "webgpu" | "webgl";
};

export async function createEngine(canvas: HTMLCanvasElement, opts: { count: number; hashHex: string; mobile: boolean; initialStage?: number }): Promise<Engine> {
  const N = opts.count;
  const { pos: shapePos, col: shapeCol, stages } = buildShapes(N, opts.hashHex);

  const renderer = new THREE.WebGPURenderer({ canvas, antialias: false, alpha: false, powerPreference: "high-performance" });
  await renderer.init();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, opts.mobile ? 1.5 : 1.75));
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#060a14");
  const camera = new THREE.PerspectiveCamera(35, canvas.clientWidth / canvas.clientHeight, 0.1, 60);
  camera.position.set(0, 0, 10);

  /* ---------------- buffers ---------------- */

  const targetsPos = instancedArray(shapePos, "vec4");
  const targetsCol = instancedArray(shapeCol, "vec4");
  // Arrancan ya formadas en la etapa inicial (0 salvo en depuración).
  const k0 = opts.initialStage ?? 0;
  const position = instancedArray(shapePos.slice(k0 * N * 4, (k0 + 1) * N * 4), "vec4");
  const velocity = instancedArray(N, "vec4");
  const color = instancedArray(shapeCol.slice(k0 * N * 4, (k0 + 1) * N * 4), "vec4");

  const uStage = uniform(0);
  const uDelta = uniform(1 / 60);
  // Lejos de todo hasta que el puntero se mueva de verdad.
  const uPointer = uniform(new THREE.Vector3(999, 999, 0));
  const uMaxStage = float(stages - 1);
  const uN = float(N);

  /* ---------------- compute ---------------- */

  const update = Fn(() => {
    const i = instanceIndex;
    const s = clamp(uStage, 0, uMaxStage);
    const a = s.floor();
    const b = clamp(a.add(1), 0, uMaxStage);
    const t = s.sub(a);
    // Cada partícula viaja con un pequeño desfase propio: el cambio de forma se "desgrana".
    const seed = float(i).div(uN);
    const tt = smoothstep(seed.mul(0.35), seed.mul(0.35).add(0.65), t);

    const ia = a.mul(uN).add(float(i)).toUint();
    const ib = b.mul(uN).add(float(i)).toUint();
    const pa = targetsPos.element(ia);
    const pb = targetsPos.element(ib);
    const ca = targetsCol.element(ia);
    const cb = targetsCol.element(ib);

    const target = mix(pa.xyz, pb.xyz, tt).toVar();
    // Turbulencia máxima a mitad de la transición.
    const chaos = sin(tt.mul(Math.PI)).mul(1.6);
    const noise = mx_noise_vec3(target.mul(0.55).add(vec3(0, 0, time.mul(0.25))));
    target.addAssign(noise.mul(chaos));
    // Respiración leve en reposo.
    target.addAssign(mx_noise_vec3(target.mul(1.4).add(time.mul(0.3))).mul(0.025));

    // Repulsión suave del puntero (en el plano z = 0).
    const p = position.element(i);
    const away = p.xyz.sub(uPointer);
    const d = away.length().max(0.001);
    const push = smoothstep(1.1, 0.0, d).mul(0.9);

    const v = velocity.element(i);
    const force = target.sub(p.xyz).mul(9.0).add(away.div(d).mul(push).mul(6.0));
    const vel = v.xyz.add(force.mul(uDelta)).mul(float(1).sub(uDelta.mul(5.5)));
    v.assign(vec4(vel, 0));
    p.assign(vec4(p.xyz.add(vel.mul(uDelta)), mix(pa.w, pb.w, tt)));

    const c = color.element(i);
    c.assign(mix(c, mix(ca, cb, tt), uDelta.mul(6.0).min(1)));
  })().compute(N);

  /* ---------------- render ---------------- */

  const material = new THREE.SpriteNodeMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  material.positionNode = position.toAttribute().xyz;
  const size = position.toAttribute().w;
  material.scaleNode = size.mul(opts.mobile ? 0.026 : 0.02);
  const pc = color.toAttribute();
  // Sprite redondo con borde suave.
  const disc = smoothstep(0.5, 0.15, uv().sub(0.5).length());
  material.colorNode = vec4(pc.xyz, 1);
  material.opacityNode = disc.mul(0.85);

  const particles = new THREE.Sprite(material);
  particles.count = N;
  particles.frustumCulled = false;
  const group = new THREE.Group();
  group.add(particles);
  scene.add(group);

  const pipeline = new THREE.RenderPipeline(renderer);
  const scenePass = pass(scene, camera);
  const sceneColor = scenePass.getTextureNode("output");
  pipeline.outputNode = sceneColor.add(bloom(sceneColor, opts.mobile ? 0.32 : 0.38, 0.22, 0.45));

  /* ---------------- loop ---------------- */

  let stageTarget = k0;
  const layout = new THREE.Vector3(0, 0, 1);
  const layoutTarget = new THREE.Vector3(0, 0, 1);
  let stage = k0;
  let running = true;
  const pointer = new THREE.Vector2(0, 0);
  let pointerActive = false;
  const pointerSmooth = new THREE.Vector2(0, 0);
  const timer = new THREE.Timer();
  timer.connect(document);

  const resize = () => {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    // En vertical, la cámara se aleja para que las formas anchas entren.
    camera.position.z = camera.aspect < 1 ? 10 / Math.max(camera.aspect, 0.5) : 10;
    camera.updateProjectionMatrix();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(canvas);
  resize();

  const frame = () => {
    if (!running) return;
    timer.update();
    const dt = Math.min(timer.getDelta(), 1 / 30);
    uDelta.value = dt;
    // El scroll fija el destino; la etapa lo sigue con inercia.
    stage += (stageTarget - stage) * (1 - Math.exp(-dt * 6));
    uStage.value = stage;

    pointerSmooth.lerp(pointer, 1 - Math.exp(-dt * 5));
    // Puntero en coordenadas locales del grupo (plano z = 0), para que la repulsión caiga donde está el cursor.
    const halfH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z;
    if (pointerActive) {
      uPointer.value.set(
        (pointerSmooth.x * halfH * camera.aspect - layout.x) / layout.z,
        (pointerSmooth.y * halfH - layout.y) / layout.z,
        0,
      );
    }

    const elapsed = timer.getElapsed();
    group.rotation.y = Math.sin(elapsed * 0.12) * 0.35 + pointerSmooth.x * 0.18;
    group.rotation.x = pointerSmooth.y * -0.1;
    layout.lerp(layoutTarget, 1 - Math.exp(-dt * 5));
    group.position.set(layout.x, layout.y, 0);
    group.scale.setScalar(layout.z);

    renderer.compute(update);
    pipeline.render();
  };
  renderer.setAnimationLoop(frame);

  return {
    backend: (renderer.backend as { isWebGPUBackend?: boolean }).isWebGPUBackend ? "webgpu" : "webgl",
    setStage: (s) => {
      stageTarget = s;
    },
    setTilt: (x, y) => pointer.set(x, y),
    setPointer: (x, y) => {
      pointerActive = true;
      pointer.set(x, y);
    },
    setLayout: (x, y, scale) => layoutTarget.set(x, y, scale),
    viewHalfHeight: () => Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z,
    setRunning: (value) => {
      if (value === running) return;
      running = value;
      renderer.setAnimationLoop(value ? frame : null);
    },
    dispose: () => {
      renderer.setAnimationLoop(null);
      observer.disconnect();
      timer.dispose();
      material.dispose();
      renderer.dispose();
    },
  };
}
