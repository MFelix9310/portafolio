'use client';

import type { FieldDef } from '@/lib/admin/fields';
import type { FormValue, LocalizedValue, TaxonomyValue } from '@/lib/admin/form-model';
import ListInput from './ListInput';
import LocalizedInput from './LocalizedInput';
import PathInput from './PathInput';
import TaxonomyInput, { type SubareaOption } from './TaxonomyInput';

const INPUT =
  'w-full border border-content/25 bg-surface px-2 py-1.5 text-[14px] text-content placeholder:text-faint';

export default function FieldControl({
  field,
  value,
  error,
  subareas,
  onChange,
}: {
  field: FieldDef;
  value: FormValue;
  error?: string;
  subareas: SubareaOption[];
  onChange: (next: FormValue) => void;
}) {
  const id = `field-${field.name}`;
  const helpId = field.help ? `${id}-help` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(' ') || undefined;
  const invalid = Boolean(error);
  const text = String(value ?? '');
  const localized = field.kind === 'localized' || field.kind === 'localized-long';
  // Los campos compuestos no tienen un control unico al que apuntar con `for`.
  const grouped = localized || field.kind === 'taxonomy';

  const shared = {
    id,
    'aria-describedby': describedBy,
    'aria-invalid': invalid || undefined,
    className: `${INPUT} ${invalid ? 'border-accent-text' : ''}`,
  };

  return (
    <div className="space-y-1">
      {/* Con pestañas ES/EN la etiqueta no puede ser un <label for>: apunta a dos
          controles. Se rotula el grupo y cada pestaña lleva su propio control. */}
      {grouped ? (
        <span id={`${id}-label`} className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
          {field.label}
          {field.required && <span className="ml-1 text-accent-text">*</span>}
        </span>
      ) : (
        <label htmlFor={id} className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
          {field.label}
          {field.required && <span className="ml-1 text-accent-text">*</span>}
        </label>
      )}

      {localized && (
        <LocalizedInput
          id={id}
          value={value as LocalizedValue}
          rows={field.rows}
          describedBy={describedBy}
          labelledBy={`${id}-label`}
          invalid={invalid}
          onChange={(next) => onChange(next)}
        />
      )}

      {field.kind === 'taxonomy' && (
        <TaxonomyInput
          value={value as TaxonomyValue[]}
          options={subareas}
          onChange={(next) => onChange(next)}
        />
      )}

      {field.kind === 'path' && (
        <PathInput
          id={id}
          value={text}
          accept={field.accept}
          describedBy={describedBy}
          onChange={(next) => onChange(next)}
        />
      )}

      {field.kind === 'list' && (
        <ListInput
          id={id}
          value={value as string[]}
          rows={field.rows}
          describedBy={describedBy}
          className={shared.className}
          onChange={(next) => onChange(next)}
        />
      )}

      {field.kind === 'select' && (
        <select {...shared} value={text} onChange={(event) => onChange(event.target.value)}>
          {(field.options ?? []).map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}

      {field.kind === 'boolean' && (
        <input
          id={id}
          type="checkbox"
          checked={Boolean(value)}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.checked)}
          className="h-4 w-4 accent-[rgb(var(--structure))]"
        />
      )}

      {(field.kind === 'text' || field.kind === 'slug' || field.kind === 'date' || field.kind === 'number') && (
        <input
          {...shared}
          type={field.kind === 'date' ? 'date' : field.kind === 'number' ? 'number' : 'text'}
          value={text}
          placeholder={field.placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      )}

      {field.help && (
        <p id={helpId} className="text-[12px] text-muted">
          {field.help}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="text-[12px] text-accent-text">
          {error}
        </p>
      )}
    </div>
  );
}
