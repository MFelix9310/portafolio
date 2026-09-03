import type { HTMLAttributes, ReactNode } from 'react';

interface AnnotationProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
  /** Filete guía a la izquierda, como una llamada que apunta al dibujo. */
  leader?: boolean;
  accent?: boolean;
  as?: 'span' | 'p' | 'div';
}

/**
 * Anotación: todo lo que es *dato* va en monoespaciada. Fechas, tecnologías,
 * contadores, tamaños, coordenadas. La regla dura del documento —prosa en sans,
 * dato en mono— se cumple usando este componente en vez de clases sueltas.
 */
export function Annotation({
  children,
  leader = false,
  accent = false,
  as: Tag = 'span',
  className = '',
  ...rest
}: AnnotationProps) {
  return (
    <Tag
      {...rest}
      className={[
        'inline-flex items-center gap-2 font-mono text-note uppercase',
        accent ? 'text-accent-text' : 'text-muted',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {leader ? <span aria-hidden="true" className="h-px w-6 shrink-0 bg-current opacity-60" /> : null}
      {children}
    </Tag>
  );
}

export default Annotation;
