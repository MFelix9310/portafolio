'use client';

import { useRouter } from 'next/navigation';
import { useMemo, useState, useTransition } from 'react';

import { saveProfileAction } from '@/lib/admin/actions';
import { STATUS_OPTIONS, type FieldDef } from '@/lib/admin/fields';
import { initialValues, isDirty, type FieldErrors, type FormValue, type FormValues } from '@/lib/admin/form-model';
import FieldControl from './FieldControl';
import { Button, Notice } from './ui';
import { useUnsavedChanges } from './useUnsavedChanges';

/** El perfil es un singleton: no tiene listado, ni orden, ni borrado. */
const FIELDS: FieldDef[] = [
  { name: 'name', label: 'Nombre', kind: 'text', required: true },
  { name: 'headline', label: 'Titular', kind: 'localized', required: true },
  { name: 'bio', label: 'Biografía', kind: 'localized-long', rows: 10, required: true },
  { name: 'photo_path', label: 'Foto', kind: 'path', accept: 'image' },
  {
    name: 'professional_photo_path',
    label: 'Foto profesional',
    kind: 'path',
    accept: 'image',
  },
  { name: 'status', label: 'Estado', kind: 'select', options: STATUS_OPTIONS },
];

export default function ProfileForm({ row }: { row: Record<string, unknown> | null }) {
  const router = useRouter();
  const loaded = useMemo(() => initialValues({ fields: FIELDS }, row), [row]);
  const [values, setValues] = useState<FormValues>(loaded);
  const [baseline, setBaseline] = useState<FormValues>(loaded);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState<{ tone: 'error' | 'success'; text: string } | null>(null);
  const [pending, startTransition] = useTransition();

  const dirty = isDirty(values, baseline);
  useUnsavedChanges(dirty);

  function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    startTransition(async () => {
      const result = await saveProfileAction(values);
      if (!result.ok) {
        setErrors(result.fieldErrors ?? {});
        setMessage({ tone: 'error', text: result.message ?? 'No se pudo guardar.' });
        return;
      }
      setErrors({});
      setBaseline(values);
      setMessage({ tone: 'success', text: 'Perfil guardado.' });
      router.refresh();
    });
  }

  return (
    <form onSubmit={submit} className="space-y-5" noValidate>
      <div className="grid gap-4 md:grid-cols-2">
        {FIELDS.map((field) => (
          <div key={field.name} className={field.kind === 'localized-long' ? 'md:col-span-2' : ''}>
            <FieldControl
              field={field}
              value={values[field.name] as FormValue}
              error={errors[field.name]}
              subareas={[]}
              onChange={(next) => setValues((current) => ({ ...current, [field.name]: next }))}
            />
          </div>
        ))}
      </div>
      {message && <Notice tone={message.tone}>{message.text}</Notice>}
      <div className="flex items-center gap-3 border-t border-content/15 pt-3">
        <Button type="submit" variant="primary" disabled={pending}>
          {pending ? 'Guardando…' : 'Guardar perfil'}
        </Button>
        <span aria-live="polite" className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
          {dirty ? 'Cambios sin guardar' : 'Sin cambios'}
        </span>
      </div>
    </form>
  );
}
