import type { ColumnKind } from '@/lib/admin/fields';

/** Una celda por tipo de columna. El panel muestra siempre el ES, que es el obligatorio. */
export default function Cell({ kind, value }: { kind: ColumnKind; value: unknown }) {
  if (value === null || value === undefined || value === '') {
    return <span className="text-faint">—</span>;
  }

  if (kind === 'localized') {
    const text = value as { es?: string; en?: string };
    return (
      <span className="flex items-baseline gap-1.5">
        <span className="line-clamp-2">{text.es}</span>
        {!text.en?.trim() && (
          <abbr
            title="Sin traducción al inglés (opcional)"
            className="shrink-0 font-mono text-[9px] uppercase tracking-[0.1em] text-faint no-underline"
          >
            es
          </abbr>
        )}
      </span>
    );
  }

  if (kind === 'list') {
    const items = value as string[];
    if (items.length === 0) return <span className="text-faint">—</span>;
    return (
      <span className="font-mono text-[11px] text-muted">
        {items.slice(0, 4).join(' · ')}
        {items.length > 4 && ` +${items.length - 4}`}
      </span>
    );
  }

  if (kind === 'boolean') {
    return <span className="font-mono text-[11px]">{value ? 'Sí' : 'No'}</span>;
  }

  if (kind === 'date' || kind === 'number') {
    return <span className="font-mono text-[11px] tabular-nums">{String(value)}</span>;
  }

  return <span className="line-clamp-2">{String(value)}</span>;
}
