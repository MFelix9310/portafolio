/**
 * Capa de acotación de la planta, pintada en un `<canvas>` 2D y proyectada
 * sobre el suelo del modelo como textura.
 *
 * Por qué textura y no geometría: las cotas son *texto y flechas*, y el texto
 * en WebGL cuesta una librería entera (troika/drei `Text` ronda las 100 KB).
 * Un único canvas con todo el rotulado son cero dependencias, una llamada de
 * dibujo y una textura. Y conceptualmente es lo correcto: la acotación está
 * *impresa en el suelo*, no modelada.
 *
 * Es la pieza que hace que el gesto signifique algo. Las cotas no se extruyen:
 * se quedan en el plano, se escorzan con la cámara y siguen ahí en el estado
 * final. Son lo que ata la lectura de dibujo con la lectura de modelo.
 */

import { axisX, axisXAt, axisZ, frameDepth, frameWidth, type FrameParams } from './frame-model';

/**
 * Margen del calco alrededor de la huella, en unidades de mundo (m). Ajustado
 * para que el rótulo más exterior (los globos de eje) caiga justo dentro: cada
 * metro de calco vacío es encuadre desperdiciado en la vista cenital.
 */
export const DECAL_PAD_X = 4.8;
export const DECAL_PAD_Z = 4.6;
/** Píxeles de textura por metro. */
export const DECAL_PPU = 48;

export interface DecalPalette {
  /** Filete principal — `--text`. */
  rule: string;
  /** Cotas y rótulos secundarios — `--text-muted`. */
  muted: string;
  /** Lápiz de revisión — `--accent`. */
  accent: string;
  /** Azul de cianotipo — `--structure`. */
  structure: string;
  /** Familia monoespaciada resuelta (`--font-mono`). */
  mono: string;
}

export function decalSize(p: FrameParams) {
  return {
    w: frameWidth(p) + 2 * DECAL_PAD_X,
    d: frameDepth(p) + 2 * DECAL_PAD_Z,
  };
}

const LETTERS = 'ABCDEFGHJKLMN';

/**
 * Dibuja la acotación completa. El sistema de coordenadas de entrada es el del
 * mundo (metros, origen centrado); la conversión a píxeles es local.
 */
export function drawPlanDecal(
  ctx: CanvasRenderingContext2D,
  p: FrameParams,
  palette: DecalPalette,
  ppu = DECAL_PPU,
): void {
  const { w, d } = decalSize(p);
  const xs = axisX(p);
  const zs = axisZ(p);
  const halfW = frameWidth(p) / 2;
  const halfD = frameDepth(p) / 2;

  const px = (x: number) => (x + w / 2) * ppu;
  const py = (z: number) => (z + d / 2) * ppu;
  const u = (m: number) => m * ppu;

  ctx.clearRect(0, 0, w * ppu, d * ppu);
  ctx.lineCap = 'butt';
  ctx.lineJoin = 'miter';

  const line = (x1: number, z1: number, x2: number, z2: number) => {
    ctx.beginPath();
    ctx.moveTo(px(x1), py(z1));
    ctx.lineTo(px(x2), py(z2));
    ctx.stroke();
  };

  const label = (text: string, x: number, z: number, size: number, color: string, angle = 0) => {
    ctx.save();
    ctx.translate(px(x), py(z));
    if (angle) ctx.rotate(angle);
    ctx.fillStyle = color;
    ctx.font = `500 ${u(size)}px ${palette.mono}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    if ('letterSpacing' in ctx) ctx.letterSpacing = `${u(size) * 0.08}px`;
    ctx.fillText(text, 0, 0);
    ctx.restore();
  };

  // --- Ejes de replanteo: línea de eje y globo rotulado ------------------
  const axisEndZ = halfD + DECAL_PAD_Z - 0.85;
  const axisEndX = halfW + DECAL_PAD_X - 0.85;
  const bubble = 0.62;

  ctx.strokeStyle = palette.muted;
  ctx.lineWidth = Math.max(1, u(0.022));
  ctx.setLineDash([u(1.1), u(0.34), u(0.1), u(0.34)]);
  for (const x of xs) line(x, -axisEndZ + bubble, x, axisEndZ - bubble);
  for (const z of zs) line(-axisEndX + bubble, z, axisEndX - bubble, z);
  ctx.setLineDash([]);

  const drawBubble = (x: number, z: number, text: string) => {
    ctx.beginPath();
    ctx.arc(px(x), py(z), u(bubble), 0, Math.PI * 2);
    ctx.fillStyle = palette.rule;
    ctx.globalAlpha = 0.06;
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = palette.muted;
    ctx.lineWidth = Math.max(1, u(0.026));
    ctx.stroke();
    label(text, x, z, 0.6, palette.rule);
  };

  xs.forEach((x, i) => drawBubble(x, -axisEndZ, LETTERS[i] ?? String(i + 1)));
  zs.forEach((z, k) => drawBubble(-axisEndX, z, String(k + 1)));

  // --- Cotas --------------------------------------------------------------
  const tick = 0.3;
  const fmt = (m: number) => m.toFixed(2);

  /** Cota horizontal: línea, marcas a 45° y valor sobre el trazo. */
  const dimX = (x1: number, x2: number, z: number, text: string, color: string) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(1, u(0.026));
    line(x1, z, x2, z);
    for (const x of [x1, x2]) line(x - tick / 2, z + tick / 2, x + tick / 2, z - tick / 2);
    const mid = (x1 + x2) / 2;
    label(text, mid, z - 0.52, 0.55, color);
  };

  /** Cota vertical (en Z). El texto gira con la cota, como en una lámina. */
  const dimZ = (z1: number, z2: number, x: number, text: string, color: string) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(1, u(0.026));
    line(x, z1, x, z2);
    for (const z of [z1, z2]) line(x - tick / 2, z + tick / 2, x + tick / 2, z - tick / 2);
    const mid = (z1 + z2) / 2;
    label(text, x - 0.52, mid, 0.55, color, -Math.PI / 2);
  };

  // Líneas de referencia desde la estructura hasta las cotas.
  const witnessZ = halfD + 3.9;
  ctx.strokeStyle = palette.muted;
  ctx.lineWidth = Math.max(1, u(0.018));
  ctx.globalAlpha = 0.55;
  for (const x of xs) line(x, halfD + 0.35, x, witnessZ);
  // La cota de fondo va por el lado -X: el +X queda libre para la cota vertical
  // de la altura, que en isométrica cae justo ahí.
  for (const z of zs) line(-halfW - 0.35, z, -halfW - 2.5, z);
  ctx.globalAlpha = 1;

  // Cota por vano y cota total: el mismo dato en dos escalas de lectura.
  for (let b = 0; b < p.bays; b += 1) {
    dimX(axisXAt(p, b), axisXAt(p, b + 1), halfD + 2.0, fmt(p.span), palette.muted);
  }
  // Sólo la cota total lleva unidad: es la convención del plano y ahorra un
  // cajetín suelto que, tumbado en el suelo, se leería como basura gráfica.
  dimX(-halfW, halfW, halfD + 3.7, `${fmt(frameWidth(p))} m`, palette.rule);
  dimZ(-halfD, halfD, -halfW - 2.3, fmt(frameDepth(p)), palette.muted);
}

/**
 * Etiqueta de la cota vertical, en un canvas aparte porque no vive en el suelo:
 * acompaña a la altura total y aparece cuando el pórtico termina de subir.
 */
export function drawHeightLabel(
  ctx: CanvasRenderingContext2D,
  text: string,
  palette: DecalPalette,
  width: number,
  height: number,
): void {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = palette.accent;
  ctx.font = `500 ${Math.round(height * 0.62)}px ${palette.mono}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  if ('letterSpacing' in ctx) ctx.letterSpacing = `${Math.round(height * 0.05)}px`;
  ctx.fillText(text, width / 2, height / 2);
}
