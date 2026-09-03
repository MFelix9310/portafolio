'use client';

import { useId, useState } from 'react';

import type { LocalizedValue } from '@/lib/admin/form-model';

const INPUT =
  'w-full border border-content/25 bg-surface px-2 py-1.5 text-[14px] text-content placeholder:text-faint';

/**
 * Campo bilingüe con pestañas ES / EN.
 *
 * ES es obligatorio y EN opcional (D5): la pestaña inglesa nunca muestra un error
 * de "falta", porque una traducción ausente no puede bloquear una publicación.
 */
export default function LocalizedInput({
  id,
  value,
  onChange,
  rows,
  describedBy,
  labelledBy,
  invalid,
}: {
  id: string;
  value: LocalizedValue;
  onChange: (next: LocalizedValue) => void;
  rows?: number;
  describedBy?: string;
  /** Id del rótulo del grupo: cada pestaña se anuncia como «Título, ES». */
  labelledBy?: string;
  invalid?: boolean;
}) {
  const [locale, setLocale] = useState<'es' | 'en'>('es');
  const group = useId();

  const tab = (key: 'es' | 'en', label: string, hint: string) => {
    const active = locale === key;
    const filled = value[key].trim().length > 0;
    return (
      <button
        key={key}
        type="button"
        role="tab"
        id={`${group}-tab-${key}`}
        aria-selected={active}
        aria-controls={`${group}-panel-${key}`}
        onClick={() => setLocale(key)}
        className={`border-b-2 px-2 py-1 font-mono text-[10px] uppercase tracking-[0.12em] ${
          active ? 'border-structure text-content' : 'border-transparent text-muted hover:text-content'
        }`}
      >
        {label}
        <span className="ml-1 text-faint">{hint}</span>
        {filled && <span aria-hidden className="ml-1 text-structure">•</span>}
      </button>
    );
  };

  const shared = {
    id,
    'aria-describedby': describedBy,
    'aria-invalid': invalid || undefined,
    className: `${INPUT} ${invalid && locale === 'es' ? 'border-accent-text' : ''}`,
  };

  return (
    <div>
      <div role="tablist" aria-label="Idioma" className="mb-1 flex gap-1 border-b border-content/15">
        {tab('es', 'ES', 'obligatorio')}
        {tab('en', 'EN', 'opcional')}
      </div>
      {(['es', 'en'] as const).map((key) => (
        <div
          key={key}
          role="tabpanel"
          id={`${group}-panel-${key}`}
          aria-labelledby={`${group}-tab-${key}`}
          hidden={locale !== key}
        >
          {rows ? (
            <textarea
              {...shared}
              id={key === 'es' ? id : `${id}-en`}
              aria-labelledby={[labelledBy, `${group}-tab-${key}`].filter(Boolean).join(' ')}
              rows={rows}
              value={value[key]}
              onChange={(event) => onChange({ ...value, [key]: event.target.value })}
            />
          ) : (
            <input
              {...shared}
              id={key === 'es' ? id : `${id}-en`}
              aria-labelledby={[labelledBy, `${group}-tab-${key}`].filter(Boolean).join(' ')}
              type="text"
              value={value[key]}
              onChange={(event) => onChange({ ...value, [key]: event.target.value })}
            />
          )}
        </div>
      ))}
    </div>
  );
}
