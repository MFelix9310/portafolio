/**
 * Planta 2D estática. Es a la vez el **estado inicial** del gesto 4 (lo que se
 * ve antes de que el scroll empiece a extruir) y su **estado degradado** —sin
 * WebGL, con `prefers-reduced-motion` o en un dispositivo de gama baja—, así
 * que la degradación sigue contando la mitad de la historia en lugar de mostrar
 * un hueco.
 *
 * Es también la representación accesible de la pieza: el canvas va
 * `aria-hidden`, este SVG no. Nada existe sólo dentro del 3D.
 */

interface PlanSvgProps {
  /** Texto alternativo; describe el dibujo, no la tecnología. */
  label: string;
  className?: string;
}

const COLUMNS = [12, 34, 56, 78];

export function PlanSvg({ label, className = '' }: PlanSvgProps) {
  return (
    <svg
      viewBox="0 0 100 56"
      preserveAspectRatio="xMidYMid meet"
      className={`aspect-[16/9] w-full text-structure ${className}`}
      role="img"
      aria-label={label}
    >
      <g stroke="currentColor" strokeWidth="0.25" fill="none" opacity="0.9">
        <rect x="10" y="10" width="80" height="36" />
        {COLUMNS.map((x) => (
          <g key={x}>
            <rect x={x - 1.6} y={8.4} width={3.2} height={3.2} />
            <rect x={x - 1.6} y={44.4} width={3.2} height={3.2} />
            <line x1={x} y1="11.6" x2={x} y2="44.4" strokeDasharray="1.5 1.5" opacity="0.5" />
          </g>
        ))}
        <line x1="10" y1="28" x2="90" y2="28" strokeDasharray="3 2" opacity="0.4" />
      </g>
      <g stroke="currentColor" strokeWidth="0.2" opacity="0.55">
        <line x1="10" y1="52" x2="90" y2="52" />
        <line x1="10" y1="50" x2="10" y2="54" />
        <line x1="90" y1="50" x2="90" y2="54" />
      </g>
    </svg>
  );
}

export default PlanSvg;
