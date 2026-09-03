'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  BufferAttribute,
  BufferGeometry,
  CanvasTexture,
  Color,
  DynamicDrawUsage,
  Group,
  LineBasicMaterial,
  LineSegments,
  LinearFilter,
  Mesh,
  MeshBasicMaterial,
  OrthographicCamera,
  PlaneGeometry,
  SRGBColorSpace,
  Scene,
  Sprite,
  SpriteMaterial,
  Vector3,
  WebGLRenderer,
} from 'three';

import { ensureGsap } from '@/lib/motion';

import {
  DEFAULT_FRAME,
  type FrameParams,
  buildTrace,
  builtHeight,
  frameDepth,
  frameHeight,
  frameWidth,
  structureFloats,
  writeStructure,
} from './frame-model';
import {
  DECAL_PPU,
  type DecalPalette,
  decalSize,
  drawHeightLabel,
  drawPlanDecal,
} from './plan-decal';

/**
 * ===========================================================================
 * Escena del gesto 4. `three` a pelo, sin React Three Fiber.
 * ===========================================================================
 * R3F hace `import * as THREE from 'three'`, y eso anula el tree-shaking: el
 * motor entero entra en el chunk (~180 KB gzip) por muy poco que se use. Medido
 * con `next build`, la pieza con R3F pesaba 231,6 KB gzip contra un presupuesto
 * de 180. Sin él, webpack se queda con lo que de verdad se toca.
 *
 * Tampoco se pierde nada: la escena ya era imperativa —un `Group` construido a
 * mano y una única función `render`—, así que de R3F sólo se usaba el `<Canvas>`
 * y `invalidate()`. Aquí `frameloop="demand"` deja de ser una opción y pasa a
 * ser literal: `renderer.render()` sólo se llama cuando el scroll, un resize o
 * la rotación en reposo lo piden.
 * ===========================================================================
 */

/* ------------------------------------------------------------------ */
/* Constantes de puesta en escena                                      */
/* ------------------------------------------------------------------ */

const DEG = Math.PI / 180;
/** Casi 90°: es una planta a todos los efectos, pero sin degenerar el `up`. */
const ELEVATION = [89.5, 34] as const;
const AZIMUTH = [0, 42] as const;
const ORBIT_RADIUS = 120;
/** Rotación en reposo: ±4.5°. Contenida, no un carrusel de producto. */
const IDLE_SWING = 4.5;
const IDLE_PERIOD_MS = 19000;
/** Umbral a partir del cual la pieza se considera «en reposo». */
const IDLE_FROM = 0.985;
/** Tope de densidad de píxeles: nada de `devicePixelRatio` sin límite. */
const MAX_DPR = 1.75;

const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
/** Arranca con decisión y asienta al final; la extrusión no debe «flotar». */
const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);

type Render = (progress: number, now: number) => void;

/* ------------------------------------------------------------------ */
/* Paleta: los colores salen de los tokens, no del código              */
/* ------------------------------------------------------------------ */

export interface ScenePalette extends DecalPalette {
  structureColor: Color;
  accentColor: Color;
}

function cssVar(style: CSSStyleDeclaration, name: string, fallback: string): string {
  const raw = style.getPropertyValue(name).trim();
  if (!raw) return fallback;
  // Los tokens se guardan como tripletas «R G B» para que Tailwind aplique alfa.
  const parts = raw.split(/[\s,]+/).filter(Boolean);
  return parts.length === 3 ? `rgb(${parts.join(', ')})` : raw;
}

function readPalette(): ScenePalette {
  const style = getComputedStyle(document.documentElement);
  const rule = cssVar(style, '--text', 'rgb(15, 18, 22)');
  const muted = cssVar(style, '--text-muted', 'rgb(86, 82, 73)');
  const accent = cssVar(style, '--accent', 'rgb(216, 52, 31)');
  const structure = cssVar(style, '--structure', 'rgb(18, 49, 92)');
  const mono = style.getPropertyValue('--font-mono').trim();
  return {
    rule,
    muted,
    accent,
    structure,
    mono: mono ? `${mono}, ui-monospace, monospace` : 'ui-monospace, SFMono-Regular, monospace',
    structureColor: new Color().setStyle(structure),
    accentColor: new Color().setStyle(accent),
  };
}

const sameColours = (a: ScenePalette, b: ScenePalette) =>
  a.rule === b.rule && a.muted === b.muted && a.accent === b.accent && a.structure === b.structure;

/**
 * Relee la paleta cuando cambia el tema (atributo o preferencia del sistema).
 *
 * La identidad del objeto sólo cambia si los colores cambian de verdad: es una
 * de las claves del efecto que construye la escena, y cualquier mutación de
 * clase en `<html>` la reconstruiría entera si aquí se devolviera un objeto
 * nuevo cada vez.
 */
function usePalette(): ScenePalette {
  const [palette, setPalette] = useState<ScenePalette>(() => readPalette());
  useEffect(() => {
    const refresh = () =>
      setPalette((current) => {
        const next = readPalette();
        return sameColours(current, next) ? current : next;
      });
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    media.addEventListener('change', refresh);
    const observer = new MutationObserver(refresh);
    observer.observe(document.documentElement, { attributeFilter: ['data-theme', 'class'] });
    return () => {
      media.removeEventListener('change', refresh);
      observer.disconnect();
    };
  }, []);
  return palette;
}

/* ------------------------------------------------------------------ */
/* Modelo                                                              */
/* ------------------------------------------------------------------ */

interface Model {
  group: Group;
  positions: Float32Array;
  attribute: BufferAttribute;
  structureMat: LineBasicMaterial;
  traceMat: LineBasicMaterial;
  decalMat: MeshBasicMaterial;
  decalCanvas: HTMLCanvasElement;
  decalTexture: CanvasTexture;
  heightGroup: Group;
  heightAttr: BufferAttribute;
  heightPositions: Float32Array;
  heightMat: LineBasicMaterial;
  heightLabel: Sprite;
  labelMat: SpriteMaterial;
  labelCanvas: HTMLCanvasElement;
  labelTexture: CanvasTexture;
  fitPoints: Vector3[];
  dispose(): void;
}

function buildModel(params: FrameParams, palette: ScenePalette): Model {
  const group = new Group();

  /* --- Calco de acotación, impreso en el suelo -------------------- */
  const { w, d } = decalSize(params);
  const decalCanvas = document.createElement('canvas');
  decalCanvas.width = Math.round(w * DECAL_PPU);
  decalCanvas.height = Math.round(d * DECAL_PPU);
  const decalTexture = new CanvasTexture(decalCanvas);
  decalTexture.colorSpace = SRGBColorSpace;
  decalTexture.minFilter = LinearFilter;
  decalTexture.generateMipmaps = false;
  const decalMat = new MeshBasicMaterial({
    map: decalTexture,
    transparent: true,
    depthTest: false,
    depthWrite: false,
  });
  const decalGeom = new PlaneGeometry(w, d);
  const decal = new Mesh(decalGeom, decalMat);
  decal.rotation.x = -Math.PI / 2;
  decal.position.y = 0.005;
  decal.renderOrder = 0;
  group.add(decal);

  /* --- Trazado en planta: la huella, que no se extruye ------------ */
  const traceGeom = new BufferGeometry();
  traceGeom.setAttribute('position', new BufferAttribute(buildTrace(params), 3));
  const traceMat = new LineBasicMaterial({
    color: palette.structureColor,
    transparent: true,
    opacity: 0.55,
    depthTest: false,
  });
  const trace = new LineSegments(traceGeom, traceMat);
  trace.renderOrder = 1;
  group.add(trace);

  /* --- Estructura extruida ---------------------------------------- */
  const positions = new Float32Array(structureFloats(params));
  const attribute = new BufferAttribute(positions, 3);
  attribute.setUsage(DynamicDrawUsage);
  const structureGeom = new BufferGeometry();
  structureGeom.setAttribute('position', attribute);
  const structureMat = new LineBasicMaterial({
    color: palette.structureColor,
    transparent: true,
    opacity: 0.9,
    depthTest: false,
  });
  const structure = new LineSegments(structureGeom, structureMat);
  structure.renderOrder = 2;
  group.add(structure);

  /* --- Cota vertical: mide lo que ya está levantado ---------------- */
  const heightGroup = new Group();
  const heightPositions = new Float32Array(5 * 2 * 3);
  const heightAttr = new BufferAttribute(heightPositions, 3);
  heightAttr.setUsage(DynamicDrawUsage);
  const heightGeom = new BufferGeometry();
  heightGeom.setAttribute('position', heightAttr);
  const heightMat = new LineBasicMaterial({
    color: palette.accentColor,
    transparent: true,
    opacity: 0,
    depthTest: false,
  });
  const heightLine = new LineSegments(heightGeom, heightMat);
  heightLine.renderOrder = 3;
  heightGroup.add(heightLine);

  const labelCanvas = document.createElement('canvas');
  labelCanvas.width = 256;
  labelCanvas.height = 64;
  const labelTexture = new CanvasTexture(labelCanvas);
  labelTexture.colorSpace = SRGBColorSpace;
  labelTexture.minFilter = LinearFilter;
  labelTexture.generateMipmaps = false;
  const labelMat = new SpriteMaterial({
    map: labelTexture,
    transparent: true,
    opacity: 0,
    depthTest: false,
  });
  const heightLabel = new Sprite(labelMat);
  heightLabel.scale.set(2.9, 0.73, 1);
  heightLabel.renderOrder = 4;
  heightGroup.add(heightLabel);
  group.add(heightGroup);

  return {
    group,
    positions,
    attribute,
    structureMat,
    traceMat,
    decalMat,
    decalCanvas,
    decalTexture,
    heightGroup,
    heightAttr,
    heightPositions,
    heightMat,
    heightLabel,
    labelMat,
    labelCanvas,
    labelTexture,
    fitPoints: Array.from({ length: 12 }, () => new Vector3()),
    dispose() {
      decalGeom.dispose();
      decalMat.dispose();
      decalTexture.dispose();
      traceGeom.dispose();
      traceMat.dispose();
      structureGeom.dispose();
      structureMat.dispose();
      heightGeom.dispose();
      heightMat.dispose();
      labelMat.dispose();
      labelTexture.dispose();
    },
  };
}

/* ------------------------------------------------------------------ */
/* Componente                                                          */
/* ------------------------------------------------------------------ */

export interface ExtrusionSceneProps {
  /** Contenedor del héroe: es él quien conduce el progreso 0 → 1. */
  triggerRef: React.RefObject<HTMLElement | null>;
  params?: Partial<FrameParams>;
  /** Se llama tras el primer frame pintado, para fundir desde la planta 2D. */
  onReady?: () => void;
  /** Sin contexto WebGL o si se pierde: la pieza vuelve a la planta 2D. */
  onFail?: () => void;
}

export function ExtrusionScene({ triggerRef, params, onReady, onFail }: ExtrusionSceneProps) {
  const frame = useMemo<FrameParams>(() => ({ ...DEFAULT_FRAME, ...params }), [params]);
  const palette = usePalette();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const progressRef = useRef(0);
  const renderRef = useRef<Render | null>(null);
  const inViewRef = useRef(true);
  const idleRaf = useRef(0);
  const syncRef = useRef<() => void>(() => undefined);

  // Callbacks por referencia: no deben reconstruir la escena al re-renderizar.
  const readyRef = useRef(onReady);
  readyRef.current = onReady;
  const failRef = useRef(onFail);
  failRef.current = onFail;

  /* --- Bucle en reposo ------------------------------------------------
     Sólo corre cuando la pieza está terminada, visible y con la pestaña
     activa. En cuanto deja de cumplirse se cancela: no hay ni un frame
     de más, y sin scroll la pieza se queda quieta salvo esa oscilación. */
  useEffect(() => {
    const step = (now: number) => {
      idleRaf.current = requestAnimationFrame(step);
      renderRef.current?.(progressRef.current, now);
    };
    const sync = () => {
      const want =
        !!renderRef.current &&
        inViewRef.current &&
        !document.hidden &&
        progressRef.current >= IDLE_FROM;
      if (want && !idleRaf.current) {
        idleRaf.current = requestAnimationFrame(step);
      } else if (!want && idleRaf.current) {
        cancelAnimationFrame(idleRaf.current);
        idleRaf.current = 0;
      }
    };
    syncRef.current = sync;
    document.addEventListener('visibilitychange', sync);
    return () => {
      document.removeEventListener('visibilitychange', sync);
      if (idleRaf.current) cancelAnimationFrame(idleRaf.current);
      idleRaf.current = 0;
    };
  }, []);

  /* --- Renderizador, escena y función de pintado ---------------------- */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let renderer: WebGLRenderer;
    try {
      renderer = new WebGLRenderer({
        canvas,
        antialias: true,
        alpha: true,
        powerPreference: 'low-power',
      });
    } catch {
      failRef.current?.();
      return;
    }
    renderer.setPixelRatio(Math.min(Math.max(window.devicePixelRatio || 1, 1), MAX_DPR));

    const scene = new Scene();
    const camera = new OrthographicCamera(-1, 1, 1, -1, 0.1, 400);
    const model = buildModel(frame, palette);
    scene.add(model.group);

    const scratch = { v: new Vector3(), right: new Vector3(), up: new Vector3() };
    const halfW = frameWidth(frame) / 2;
    const halfD = frameDepth(frame) / 2;
    const totalHeight = frameHeight(frame);
    const { w, d } = decalSize(frame);
    const cotaX = halfW + 1.15;
    const labelCtx = model.labelCanvas.getContext('2d');
    const pts = model.fitPoints;
    let lastLabel = -1;
    let width = 1;
    let height = 1;

    const measure = () => {
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, Math.round(rect.width));
      height = Math.max(1, Math.round(rect.height));
      // `false`: el tamaño CSS lo pone la hoja de estilos, no el renderizador.
      renderer.setSize(width, height, false);
      camera.left = -width / 2;
      camera.right = width / 2;
      camera.top = height / 2;
      camera.bottom = -height / 2;
    };
    measure();

    const render: Render = (raw, now) => {
      const p = clamp01(raw);
      const e = ease(p);

      /* 1 · Geometría: se reescribe el buffer, no se crea nada nuevo. */
      writeStructure(model.positions, frame, p);
      model.attribute.needsUpdate = true;

      /* 2 · La acotación de la planta NO desaparece: baja a referencia. Es lo
             que ata la lectura de dibujo con la de modelo. */
      model.decalMat.opacity = lerp(1, 0.62, e);
      model.traceMat.opacity = lerp(0.55, 0.34, e);
      model.structureMat.opacity = lerp(0.82, 0.98, e);

      /* 3 · Cota vertical: crece con lo construido y su número cuenta hasta el
             valor real, igual que la acotación del gesto 1. */
      const built = builtHeight(frame, p);
      const reveal = clamp01((p - 0.42) / 0.3);
      model.heightMat.opacity = reveal * 0.9;
      model.labelMat.opacity = clamp01((p - 0.6) / 0.25);
      model.heightGroup.visible = reveal > 0.001;
      if (model.heightGroup.visible) {
        const hp = model.heightPositions;
        const t = 0.22;
        let i = 0;
        const seg = (
          ax: number, ay: number, az: number,
          bx: number, by: number, bz: number,
        ) => {
          hp[i++] = ax; hp[i++] = ay; hp[i++] = az;
          hp[i++] = bx; hp[i++] = by; hp[i++] = bz;
        };
        seg(cotaX, 0, halfD, cotaX, built, halfD);
        seg(cotaX - t, -t, halfD, cotaX + t, t, halfD);
        seg(cotaX - t, built - t, halfD, cotaX + t, built + t, halfD);
        seg(halfW + 0.3, 0, halfD, cotaX + 0.35, 0, halfD);
        seg(halfW + 0.3, built, halfD, cotaX + 0.35, built, halfD);
        model.heightAttr.needsUpdate = true;
        model.heightLabel.position.set(cotaX + 1.9, built / 2, halfD);

        const quantised = Math.round(built * 10) / 10;
        if (labelCtx && quantised !== lastLabel) {
          lastLabel = quantised;
          drawHeightLabel(labelCtx, `${quantised.toFixed(2)} m`, palette, 256, 64);
          model.labelTexture.needsUpdate = true;
        }
      }

      /* 4 · Cámara: de cenital a isométrica, conducida por el mismo progreso. */
      const idle =
        p > 0.9
          ? Math.sin((now / IDLE_PERIOD_MS) * Math.PI * 2) * IDLE_SWING * clamp01((p - 0.9) / 0.1)
          : 0;
      const elev = lerp(ELEVATION[0], ELEVATION[1], e) * DEG;
      const azim = (lerp(AZIMUTH[0], AZIMUTH[1], e) + idle) * DEG;
      const cosE = Math.cos(elev);
      camera.position.set(
        ORBIT_RADIUS * cosE * Math.sin(azim),
        ORBIT_RADIUS * Math.sin(elev),
        ORBIT_RADIUS * cosE * Math.cos(azim),
      );
      camera.lookAt(0, 0, 0);
      camera.updateMatrixWorld();

      /* 5 · Encuadre calculado del contenido real: ni la planta ni el pórtico
             final se salen del cajetín, sea cual sea la proporción. */
      let n = 0;
      const put = (x: number, y: number, z: number) => {
        pts[n]?.set(x, y, z);
        n += 1;
      };
      put(-w / 2, 0, -d / 2);
      put(w / 2, 0, -d / 2);
      put(w / 2, 0, d / 2);
      put(-w / 2, 0, d / 2);
      const top = Math.max(built, 0.001);
      // La cota vertical y su número viven fuera de la huella. El margen crece
      // con ella —y simétrico, para no descentrar la composición— en vez de
      // reservar sitio desde el principio y encoger la planta.
      const reach = halfW + 4.7 * reveal;
      for (const sx of [-1, 1]) {
        for (const sz of [-1, 1]) {
          put(sx * halfW, top, sz * halfD);
          put(sx * reach, Math.min(top, totalHeight), sz * halfD);
        }
      }
      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;
      for (const pt of pts) {
        scratch.v.copy(pt).applyMatrix4(camera.matrixWorldInverse);
        if (scratch.v.x < minX) minX = scratch.v.x;
        if (scratch.v.x > maxX) maxX = scratch.v.x;
        if (scratch.v.y < minY) minY = scratch.v.y;
        if (scratch.v.y > maxY) maxY = scratch.v.y;
      }
      scratch.right.setFromMatrixColumn(camera.matrix, 0);
      scratch.up.setFromMatrixColumn(camera.matrix, 1);
      camera.position
        .addScaledVector(scratch.right, (minX + maxX) / 2)
        .addScaledVector(scratch.up, (minY + maxY) / 2);
      camera.updateMatrixWorld();
      camera.zoom = Math.min(width / (maxX - minX), height / (maxY - minY)) * 0.94;
      camera.updateProjectionMatrix();

      renderer.render(scene, camera);
    };

    /* La textura de acotación se pinta al montar y se repinta cuando las
       fuentes terminan de cargar: las métricas de la mono han de ser reales. */
    let alive = true;
    const paintDecal = () => {
      const ctx = model.decalCanvas.getContext('2d');
      if (!alive || !ctx) return;
      drawPlanDecal(ctx, frame, palette);
      model.decalTexture.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
      model.decalTexture.needsUpdate = true;
      render(progressRef.current, performance.now());
    };
    paintDecal();
    document.fonts.ready.then(paintDecal).catch(() => undefined);

    const observer = new ResizeObserver(() => {
      measure();
      render(progressRef.current, performance.now());
    });
    observer.observe(canvas);

    const onLost = (event: Event) => {
      event.preventDefault();
      failRef.current?.();
    };
    canvas.addEventListener('webglcontextlost', onLost);

    renderRef.current = render;
    syncRef.current();
    render(progressRef.current, performance.now());
    const raf = requestAnimationFrame(() => readyRef.current?.());

    return () => {
      alive = false;
      cancelAnimationFrame(raf);
      canvas.removeEventListener('webglcontextlost', onLost);
      observer.disconnect();
      renderRef.current = null;
      syncRef.current();
      model.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
    };
  }, [frame, palette]);

  /* --- El scroll conduce la animación ---------------------------------
     No hay rAF libre animando nada: si se quita el scroll, la pieza se
     queda exactamente donde el usuario la dejó. */
  useEffect(() => {
    const el = triggerRef.current;
    if (!el) return;
    const gsap = ensureGsap();
    const proxy = { v: 0 };

    const context = gsap.context(() => {
      gsap.to(proxy, {
        v: 1,
        ease: 'none',
        scrollTrigger: {
          trigger: el,
          // El arranque va por debajo de donde la pieza cae al cargar la página
          // (~37 % del viewport con la cabecera de /civil-bim): hay que ver la
          // planta pura antes de que nada se mueva.
          start: 'top 28%',
          // Recorrido explícito en píxeles, no `'top -18%'`: el final tiene que
          // caer con la pieza todavía dentro del viewport, o el pórtico termina
          // de levantarse por encima del borde y nadie lo ve.
          end: () => `+=${Math.round(window.innerHeight * 0.3)}`,
          scrub: 0.4,
          invalidateOnRefresh: true,
        },
        onUpdate: () => {
          progressRef.current = proxy.v;
          renderRef.current?.(proxy.v, performance.now());
          syncRef.current();
        },
      });
    }, el);

    const io = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (!entry) return;
        inViewRef.current = entry.isIntersecting;
        syncRef.current();
      },
      { threshold: 0 },
    );
    io.observe(el);

    return () => {
      io.disconnect();
      context.revert();
    };
  }, [triggerRef]);

  return <canvas ref={canvasRef} className="absolute inset-0 block h-full w-full" />;
}

export default ExtrusionScene;
