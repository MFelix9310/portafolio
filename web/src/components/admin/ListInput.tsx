'use client';

import { useEffect, useRef, useState } from 'react';

function parse(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

/**
 * Campo de lista (`text[]`) sobre un textarea.
 *
 * El texto crudo vive aquí y no en el formulario. Si el valor controlado fuese el
 * array ya partido, escribir una coma la borraría en el mismo golpe de tecla: el
 * separador desaparece al normalizar. Se emite el array partido hacia arriba y se
 * conserva abajo lo que Félix está escribiendo.
 */
export default function ListInput({
  id,
  value,
  rows,
  describedBy,
  className,
  onChange,
}: {
  id: string;
  value: string[];
  rows?: number;
  describedBy?: string;
  className?: string;
  onChange: (next: string[]) => void;
}) {
  const [text, setText] = useState(() => value.join('\n'));
  const emitted = useRef<string[]>(value);

  useEffect(() => {
    // Solo se reescribe si el cambio viene de fuera (recarga de la fila), no del
    // propio tecleo: comparar por referencia distingue los dos casos.
    if (value !== emitted.current) {
      setText(value.join('\n'));
      emitted.current = value;
    }
  }, [value]);

  return (
    <textarea
      id={id}
      rows={rows ?? 3}
      value={text}
      aria-describedby={describedBy}
      placeholder="Una por línea"
      className={className}
      onChange={(event) => {
        setText(event.target.value);
        const parsed = parse(event.target.value);
        emitted.current = parsed;
        onChange(parsed);
      }}
    />
  );
}
