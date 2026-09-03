'use client';

import { useState, type FormEvent } from 'react';

import Annotation from '@/components/primitives/Annotation';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';

type Status = 'idle' | 'sending' | 'sent' | 'error';

const FIELD =
  'w-full border filete bg-surface px-3 py-2 text-sm text-content placeholder:text-faint focus:border-content';

/** POST /api/v1/messages del contrato. Sin API configurada, el formulario se anuncia inactivo. */
export function ContactForm({ locale }: { locale: Locale }) {
  const c = copy(locale);
  const form = c.contact.form;
  const api = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '');
  const [status, setStatus] = useState<Status>('idle');

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!api) return;

    // `currentTarget` es null tras el primer await; se captura antes.
    const element = event.currentTarget;
    const data = new FormData(element);
    setStatus('sending');
    try {
      const response = await fetch(`${api}/api/v1/messages`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          name: data.get('name'),
          email: data.get('email'),
          subject: data.get('subject'),
          body: data.get('message'),
        }),
      });
      setStatus(response.ok ? 'sent' : 'error');
      if (response.ok) element.reset();
    } catch {
      setStatus('error');
    }
  };

  return (
    <section aria-labelledby="mensaje" className="flex flex-col gap-4">
      <h2 id="mensaje" className="font-mono text-note uppercase tracking-[0.14em] text-faint">
        {form.labels.message}
      </h2>

      {!api ? (
        <Annotation accent className="!normal-case">
          {c.chrome.contact_form_offline}
        </Annotation>
      ) : null}

      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-note uppercase tracking-[0.14em] text-muted">
              {form.labels.name}
            </span>
            <input name="name" required disabled={!api} className={FIELD} autoComplete="name" />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-note uppercase tracking-[0.14em] text-muted">
              {form.labels.email}
            </span>
            <input
              name="email"
              type="email"
              required
              disabled={!api}
              className={FIELD}
              autoComplete="email"
            />
          </label>
        </div>

        <label className="flex flex-col gap-1.5">
          <span className="font-mono text-note uppercase tracking-[0.14em] text-muted">
            {form.labels.subject}
          </span>
          <input name="subject" required disabled={!api} className={FIELD} />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="font-mono text-note uppercase tracking-[0.14em] text-muted">
            {form.labels.message}
          </span>
          <textarea name="message" rows={6} required disabled={!api} className={FIELD} />
        </label>

        <button
          type="submit"
          disabled={!api || status === 'sending'}
          className="self-start border border-content bg-content px-4 py-2 font-mono text-note uppercase tracking-[0.14em] text-surface transition-opacity duration-200 disabled:opacity-40"
        >
          {status === 'sending' ? form.submitting : form.submit}
        </button>

        <p aria-live="polite" className="font-mono text-note uppercase tracking-[0.14em] text-muted">
          {status === 'sent' ? form.success : status === 'error' ? form.errors.generic_error : ''}
        </p>
      </form>
    </section>
  );
}

export default ContactForm;
