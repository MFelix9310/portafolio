import type { ComponentProps, ReactNode } from 'react';

import type { Status } from '@/lib/admin/types';

/** Primitivas del panel. Densas y sin adornos: esto es una herramienta de trabajo. */

const VARIANTS = {
  primary: 'bg-surface-inverted text-on-inverted hover:opacity-90',
  default: 'border border-content/25 text-content hover:bg-surface-sunken',
  quiet: 'text-muted hover:text-content hover:bg-surface-sunken',
  danger: 'border border-accent-text/50 text-accent-text hover:bg-accent/10',
} as const;

export type ButtonVariant = keyof typeof VARIANTS;

export function Button({
  variant = 'default',
  className = '',
  ...props
}: ComponentProps<'button'> & { variant?: ButtonVariant }) {
  return (
    <button
      {...props}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.1em] transition-opacity disabled:cursor-not-allowed disabled:opacity-40 ${VARIANTS[variant]} ${className}`}
    />
  );
}

export function StatusBadge({ status }: { status: Status | string }) {
  const published = status === 'published';
  return (
    <span
      className={`inline-block border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em] ${
        published
          ? 'border-structure/60 text-structure'
          : 'border-content/25 text-muted'
      }`}
    >
      {published ? 'Publicado' : 'Borrador'}
    </span>
  );
}

export function Panel({
  title,
  actions,
  children,
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="border border-content/15 bg-surface">
      {(title || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-content/15 px-3 py-2">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">{title}</h2>
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

export function Notice({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'error' | 'success';
  children: ReactNode;
}) {
  const tones = {
    info: 'border-content/20 text-muted',
    error: 'border-accent-text text-accent-text',
    success: 'border-structure text-structure',
  } as const;
  return (
    <p
      role={tone === 'error' ? 'alert' : 'status'}
      className={`border-l-2 px-3 py-2 text-[13px] ${tones[tone]}`}
    >
      {children}
    </p>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <p className="px-3 py-8 text-center font-mono text-[11px] uppercase tracking-[0.12em] text-muted">
      {children}
    </p>
  );
}
