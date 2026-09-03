'use client';

import { AREA_OPTIONS } from '@/lib/admin/fields';
import type { TaxonomyValue } from '@/lib/admin/form-model';
import { Button } from './ui';

export interface SubareaOption {
  area: string;
  key: string;
  label: string;
}

const SELECT =
  'border border-content/25 bg-surface px-2 py-1.5 text-[13px] text-content';

/** Pares área/subárea de un proyecto. Un proyecto puede colgar de varias. */
export default function TaxonomyInput({
  value,
  options,
  onChange,
}: {
  value: TaxonomyValue[];
  options: SubareaOption[];
  onChange: (next: TaxonomyValue[]) => void;
}) {
  function update(index: number, patch: Partial<TaxonomyValue>) {
    onChange(
      value.map((tag, position) => {
        if (position !== index) return tag;
        const next = { ...tag, ...patch };
        // Al cambiar de área la subárea anterior deja de existir en ella.
        if (patch.area && patch.area !== tag.area) next.subarea = '';
        return next;
      }),
    );
  }

  return (
    <div className="space-y-2">
      {value.length === 0 && (
        <p className="font-mono text-[11px] uppercase tracking-[0.1em] text-faint">
          Sin área asignada
        </p>
      )}
      {value.map((tag, index) => {
        const forArea = options.filter((option) => option.area === tag.area);
        return (
          <div key={index} className="flex flex-wrap items-center gap-2">
            <select
              className={SELECT}
              aria-label={`Área de la etiqueta ${index + 1}`}
              value={tag.area}
              onChange={(event) => update(index, { area: event.target.value })}
            >
              <option value="">— área —</option>
              {AREA_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <select
              className={SELECT}
              aria-label={`Subárea de la etiqueta ${index + 1}`}
              value={tag.subarea}
              onChange={(event) => update(index, { subarea: event.target.value })}
            >
              <option value="">— subárea —</option>
              {forArea.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
            <Button
              type="button"
              variant="quiet"
              onClick={() => onChange(value.filter((_, position) => position !== index))}
              aria-label={`Quitar etiqueta ${index + 1}`}
            >
              Quitar
            </Button>
          </div>
        );
      })}
      <Button type="button" onClick={() => onChange([...value, { area: '', subarea: '' }])}>
        Añadir área
      </Button>
    </div>
  );
}
