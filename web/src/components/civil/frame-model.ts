/**
 * Pórtico paramétrico — la geometría del gesto 4 se *calcula*, no se descarga.
 *
 * Este módulo es aritmética pura: no importa `three` ni React, así que puede
 * razonarse (y probarse) sin motor gráfico. Escribe posiciones en un
 * `Float32Array` preasignado que la escena reutiliza en cada actualización de
 * scroll; no se crea basura por frame.
 *
 * Convenio de ejes: X = ancho (vanos), Z = fondo (pórticos), Y = arriba.
 * El modelo está centrado en el origen para que la cámara orbite alrededor de
 * su eje sin necesidad de un target desplazado.
 */

export interface FrameParams {
  /** Vanos en X. Con `bays = 3` hay 4 líneas de replanteo: A, B, C, D. */
  bays: number;
  /** Vanos en Z. Con `frames = 1` hay 2 líneas: 1 y 2. */
  frames: number;
  /** Plantas sobre rasante. */
  floors: number;
  /** Luz entre ejes en X (m). */
  span: number;
  /** Separación entre pórticos en Z (m). */
  depth: number;
  /** Altura de entrepiso (m). */
  storey: number;
  /** Lado de la sección cuadrada del soporte (m). */
  column: number;
  /** Ancho del alma de la viga (m). */
  beamWidth: number;
  /** Canto de la viga (m). */
  beamDepth: number;
}

export const DEFAULT_FRAME: FrameParams = {
  bays: 3,
  frames: 1,
  floors: 3,
  span: 6,
  depth: 6,
  storey: 3.2,
  column: 0.46,
  beamWidth: 0.28,
  beamDepth: 0.52,
};

/**
 * Retraso de las vigas respecto al soporte, en plantas. La viga de un forjado
 * termina de cerrarse cuando el soporte ya ha subido un tercio de la planta
 * siguiente: es el orden real de montaje y, gráficamente, evita que todo
 * aparezca de golpe.
 */
const BEAM_LAG = 0.32;

const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
const smooth = (v: number) => v * v * (3 - 2 * v);

export function frameWidth(p: FrameParams) {
  return p.bays * p.span;
}
export function frameDepth(p: FrameParams) {
  return p.frames * p.depth;
}
export function frameHeight(p: FrameParams) {
  return p.floors * p.storey;
}

/**
 * Coordenadas de las líneas de replanteo. Se calculan, no se indexan: así el
 * resto del módulo recorre índices sin tropezar con `noUncheckedIndexedAccess`
 * y sin sembrar `!` por todas partes.
 */
export function axisXAt(p: FrameParams, i: number): number {
  return -frameWidth(p) / 2 + i * p.span;
}
export function axisZAt(p: FrameParams, k: number): number {
  return -frameDepth(p) / 2 + k * p.depth;
}
export function axisX(p: FrameParams): number[] {
  return Array.from({ length: p.bays + 1 }, (_, i) => axisXAt(p, i));
}
export function axisZ(p: FrameParams): number[] {
  return Array.from({ length: p.frames + 1 }, (_, k) => axisZAt(p, k));
}

/**
 * Frente de montaje, medido en plantas. Un único valor continuo gobierna toda
 * la extrusión: los soportes son una sola pieza que crece desde su huella y las
 * vigas entran cuando el frente pasa por su forjado.
 *
 * Que sea continuo no es un detalle de implementación: con una caja por planta
 * quedaban secciones flotando en el aire —las plantas todavía sin empezar— y
 * eso se lee como ruido, no como un montaje.
 */
export function assemblyFront(p: FrameParams, progress: number): number {
  return smooth(clamp01(progress)) * (p.floors + BEAM_LAG);
}

/** Altura ya levantada (m) para el avance dado. Es lo que mide la cota vertical. */
export function builtHeight(p: FrameParams, progress: number): number {
  return Math.min(assemblyFront(p, progress), p.floors) * p.storey;
}

/** Nº de miembros (soportes + vigas) del modelo. */
export function memberCount(p: FrameParams): number {
  const columns = (p.bays + 1) * (p.frames + 1);
  const beamsX = p.floors * (p.frames + 1) * p.bays;
  const beamsZ = p.floors * (p.bays + 1) * p.frames;
  return columns + beamsX + beamsZ;
}

/** Cada miembro se dibuja como las 12 aristas de un prisma: 24 vértices. */
export const FLOATS_PER_MEMBER = 12 * 2 * 3;

export function structureFloats(p: FrameParams): number {
  return memberCount(p) * FLOATS_PER_MEMBER;
}

/** Escribe las 12 aristas de una caja alineada con los ejes. */
function writeBox(
  out: Float32Array,
  at: number,
  x0: number,
  y0: number,
  z0: number,
  x1: number,
  y1: number,
  z1: number,
): number {
  let i = at;
  const seg = (ax: number, ay: number, az: number, bx: number, by: number, bz: number) => {
    out[i++] = ax;
    out[i++] = ay;
    out[i++] = az;
    out[i++] = bx;
    out[i++] = by;
    out[i++] = bz;
  };
  // Cara inferior.
  seg(x0, y0, z0, x1, y0, z0);
  seg(x1, y0, z0, x1, y0, z1);
  seg(x1, y0, z1, x0, y0, z1);
  seg(x0, y0, z1, x0, y0, z0);
  // Cara superior.
  seg(x0, y1, z0, x1, y1, z0);
  seg(x1, y1, z0, x1, y1, z1);
  seg(x1, y1, z1, x0, y1, z1);
  seg(x0, y1, z1, x0, y1, z0);
  // Montantes.
  seg(x0, y0, z0, x0, y1, z0);
  seg(x1, y0, z0, x1, y1, z0);
  seg(x1, y0, z1, x1, y1, z1);
  seg(x0, y0, z1, x0, y1, z1);
  return i;
}

/**
 * Rellena `out` con el pórtico en el avance `progress` (0 = planta, 1 = pórtico).
 *
 * En `progress = 0` los soportes tienen altura cero: sus cajas degeneran en el
 * cuadrado de la sección apoyado en el suelo, que es exactamente el símbolo del
 * pilar en planta. La extrusión no sustituye al dibujo, lo levanta.
 */
export function writeStructure(out: Float32Array, p: FrameParams, progress: number): void {
  const c = p.column / 2;
  const bw = p.beamWidth / 2;
  const front = assemblyFront(p, progress);
  const top = Math.min(front, p.floors) * p.storey;
  let i = 0;

  // Soportes: una sola pieza por nudo, de la huella hacia arriba. Con el frente
  // en cero la caja degenera en el cuadrado de la sección apoyado en el suelo,
  // que es exactamente el símbolo del pilar en planta.
  for (let ix = 0; ix <= p.bays; ix += 1) {
    const x = axisXAt(p, ix);
    for (let iz = 0; iz <= p.frames; iz += 1) {
      const z = axisZAt(p, iz);
      i = writeBox(out, i, x - c, 0, z - c, x + c, top, z + c);
    }
  }

  // Vigas: crecen desde el nudo hacia el eje siguiente en cuanto el frente pasa
  // por su forjado. Antes de eso la caja es de longitud cero y no dibuja nada.
  for (let f = 1; f <= p.floors; f += 1) {
    const grow = smooth(clamp01((front - f) / BEAM_LAG));
    const level = f * p.storey;
    const y0 = level - p.beamDepth;
    // Sin avance la caja se colapsa a un punto. Dejarla con longitud cero pero
    // canto completo pintaría un rectángulo suelto flotando en cada nudo.
    const idle = grow <= 0;

    for (let iz = 0; iz <= p.frames; iz += 1) {
      const z = axisZAt(p, iz);
      for (let b = 0; b < p.bays; b += 1) {
        const a = axisXAt(p, b);
        if (idle) {
          i = writeBox(out, i, a, 0, z, a, 0, z);
          continue;
        }
        const end = a + (axisXAt(p, b + 1) - a) * grow;
        i = writeBox(out, i, a, y0, z - bw, end, level, z + bw);
      }
    }
    for (let ix = 0; ix <= p.bays; ix += 1) {
      const x = axisXAt(p, ix);
      for (let b = 0; b < p.frames; b += 1) {
        const a = axisZAt(p, b);
        if (idle) {
          i = writeBox(out, i, x, 0, a, x, 0, a);
          continue;
        }
        const end = a + (axisZAt(p, b + 1) - a) * grow;
        i = writeBox(out, i, x - bw, y0, a, x + bw, level, end);
      }
    }
  }
}

/**
 * Trazado en planta: la retícula de vigas proyectada en el suelo. No se extruye
 * nunca — es la huella de la que salen los elementos y la que sigue ahí al
 * final, atando la lectura de modelo con la de dibujo.
 */
export function buildTrace(p: FrameParams): Float32Array {
  const y = 0.004;
  const x0 = axisXAt(p, 0);
  const x1 = axisXAt(p, p.bays);
  const z0 = axisZAt(p, 0);
  const z1 = axisZAt(p, p.frames);
  const out = new Float32Array((p.frames + 1 + p.bays + 1) * 6);
  let i = 0;
  const seg = (ax: number, az: number, bx: number, bz: number) => {
    out[i++] = ax;
    out[i++] = y;
    out[i++] = az;
    out[i++] = bx;
    out[i++] = y;
    out[i++] = bz;
  };
  for (let k = 0; k <= p.frames; k += 1) seg(x0, axisZAt(p, k), x1, axisZAt(p, k));
  for (let j = 0; j <= p.bays; j += 1) seg(axisXAt(p, j), z0, axisXAt(p, j), z1);
  return out;
}
