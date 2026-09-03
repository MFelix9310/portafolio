'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { RESOURCE_KEYS, RESOURCES } from '@/lib/admin/resources';

const EXTRA = [
  { href: '/admin/profile', label: 'Perfil' },
  { href: '/admin/messages', label: 'Mensajes' },
] as const;

export default function AdminNav() {
  const pathname = usePathname();

  const items = [
    { href: '/admin', label: 'Panel' },
    ...RESOURCE_KEYS.map((key) => ({ href: `/admin/${key}`, label: RESOURCES[key].label })),
    ...EXTRA,
  ];

  return (
    <nav aria-label="Secciones del panel" className="border-b border-content/15 md:border-b-0 md:border-r">
      <ul className="flex flex-wrap md:flex-col">
        {items.map((item) => {
          const active =
            item.href === '/admin' ? pathname === '/admin' : pathname.startsWith(item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={active ? 'page' : undefined}
                className={`block border-b border-content/10 px-3 py-2 font-mono text-[11px] uppercase tracking-[0.12em] transition-colors md:w-44 ${
                  active
                    ? 'bg-surface-sunken text-content'
                    : 'text-muted hover:bg-surface-sunken hover:text-content'
                }`}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
