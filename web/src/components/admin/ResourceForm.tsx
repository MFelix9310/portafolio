'use client';

import { useRouter } from 'next/navigation';
import { useMemo, useState, useTransition } from 'react';

import { saveResourceAction } from '@/lib/admin/actions';
import {
  initialValues,
  isDirty,
  validate,
  type FieldErrors,
  type FormValue,
  type FormValues,
} from '@/lib/admin/form-model';
import { RESOURCES, type ResourceKey } from '@/lib/admin/resources';
import FieldControl from './FieldControl';
import type { SubareaOption } from './TaxonomyInput';
import { Button, Notice } from './ui';
import { useUnsavedChanges } from './useUnsavedChanges';

export default function ResourceForm({
  resource,
  id,
  row,
  subareas,
  readOnlyReason,
}: {
  resource: ResourceKey;
  id: string | null;
  row?: Record<string, unknown> | null;
  subareas: SubareaOption[];
  readOnlyReason?: string;
}) {
  const def = RESOURCES[resource];
  const router = useRouter();
  const loaded = useMemo(() => initialValues(def, row), [def, row]);
  const [values, setValues] = useState<FormValues>(loaded);
  // Copia contra la que se compara para saber si hay cambios sin guardar. Se
  // renueva al guardar, no al recargar los datos del servidor.
  const [baseline, setBaseline] = useState<FormValues>(loaded);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState<{ tone: 'error' | 'success'; text: string } | null>(null);
  const [pending, startTransition] = useTransition();

  const dirty = isDirty(values, baseline);
  useUnsavedChanges(dirty && !readOnlyReason);

  function set(name: string, next: FormValue) {
    setValues((current) => ({ ...current, [name]: next }));
    setErrors((current) => {
      if (!current[name]) return current;
      const { [name]: _dropped, ...rest } = current;
      return rest;
    });
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);

    const found = validate(def, values);
    if (Object.keys(found).length > 0) {
      setErrors(found);
      setMessage({ tone: 'error', text: 'Hay campos por corregir.' });
      const first = def.fields.find((field) => found[field.name]);
      if (first) document.getElementById(`field-${first.name}`)?.focus();
      return;
    }

    startTransition(async () => {
      const result = await saveResourceAction(resource, id, values);
      if (!result.ok) {
        setErrors(result.fieldErrors ?? {});
        setMessage({ tone: 'error', text: result.message ?? 'No se pudo guardar.' });
        return;
      }
      setMessage({ tone: 'success', text: 'Guardado.' });
      const newId = result.data?.id;
      if (!id && newId) {
        router.replace(`/admin/${resource}/${newId}`);
        return;
      }
      setBaseline(values);
      router.refresh();
    });
  }

  return (
    <form onSubmit={submit} className="space-y-5" noValidate>
      {readOnlyReason && <Notice tone="info">{readOnlyReason}</Notice>}
      {def.note && <Notice tone="info">{def.note}</Notice>}

      <div className="grid gap-4 md:grid-cols-2">
        {def.fields.map((field) => (
          <div
            key={field.name}
            className={
              field.kind === 'localized-long' || field.kind === 'taxonomy' ? 'md:col-span-2' : ''
            }
          >
            <FieldControl
              field={field}
              value={values[field.name] as FormValue}
              error={errors[field.name]}
              subareas={subareas}
              onChange={(next) => set(field.name, next)}
            />
          </div>
        ))}
      </div>

      {message && <Notice tone={message.tone}>{message.text}</Notice>}

      <div className="flex items-center gap-3 border-t border-content/15 pt-3">
        <Button type="submit" variant="primary" disabled={pending || Boolean(readOnlyReason)}>
          {pending ? 'Guardando…' : id ? 'Guardar cambios' : `Crear ${def.singular}`}
        </Button>
        <span aria-live="polite" className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
          {dirty ? 'Cambios sin guardar' : 'Sin cambios'}
        </span>
      </div>
    </form>
  );
}
