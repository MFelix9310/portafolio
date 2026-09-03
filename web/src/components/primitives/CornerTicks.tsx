interface CornerTicksProps {
  /** Longitud del filete en píxeles. */
  size?: number;
  className?: string;
  /** Sólo las dos esquinas superiores, para marcar un encabezado. */
  top?: boolean;
}

/**
 * Marcas de esquina: dos filetes en ángulo. Sustituyen al radio de borde —
 * son la marca de recorte de una lámina, no una tarjeta de Material Design.
 */
export function CornerTicks({ size = 10, className = '', top = false }: CornerTicksProps) {
  const corners = top
    ? (['tl', 'tr'] as const)
    : (['tl', 'tr', 'bl', 'br'] as const);

  const position: Record<string, string> = {
    tl: 'left-0 top-0 border-l border-t',
    tr: 'right-0 top-0 border-r border-t',
    bl: 'left-0 bottom-0 border-l border-b',
    br: 'right-0 bottom-0 border-r border-b',
  };

  return (
    <span aria-hidden="true" className={`pointer-events-none absolute inset-0 ${className}`}>
      {corners.map((corner) => (
        <span
          key={corner}
          className={`absolute border-content ${position[corner]}`}
          style={{ width: size, height: size }}
        />
      ))}
    </span>
  );
}

export default CornerTicks;
