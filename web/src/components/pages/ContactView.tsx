import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import ContactForm from '@/components/contact/ContactForm';
import Reveal from '@/components/motion/Reveal';
import { getCatalog } from '@/lib/api/catalog';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';

export async function ContactView({ locale }: { locale: Locale }) {
  const c = copy(locale);
  const catalog = await getCatalog();

  return (
    <div className="lamina py-12 md:py-16">
      <Reveal stagger="[data-head]" as="header" className="mb-10 flex flex-col gap-5">
        <Annotation data-head leader>
          {catalog.profile.name}
        </Annotation>
        <h1 data-head className="font-display text-display-md font-semibold text-content">
          {c.contact.heading}
        </h1>
        <p data-head className="max-w-prose text-base leading-relaxed text-muted md:text-lg">
          {c.contact.support_text}
        </p>
      </Reveal>

      <div className="grid gap-10 md:grid-cols-[1fr_1.2fr]">
        <section aria-labelledby="canales" className="relative h-fit border filete p-5">
          <CornerTicks size={10} />
          <h2
            id="canales"
            className="mb-4 font-mono text-note uppercase tracking-[0.14em] text-faint"
          >
            {c.chrome.contact_channels}
          </h2>
          <ul className="flex flex-col border-t filete">
            {catalog.contacts.map((contact) => (
              <li key={contact.kind}>
                <a
                  href={contact.value}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="flex items-center justify-between gap-4 border-b filete py-3 font-mono text-note uppercase tracking-[0.14em] text-content transition-colors duration-200 hover:text-accent-text"
                >
                  <span>{c.contact.channels[contact.kind] ?? contact.kind}</span>
                  <span aria-hidden="true">↗</span>
                </a>
              </li>
            ))}
          </ul>
        </section>

        <ContactForm locale={locale} />
      </div>
    </div>
  );
}

export default ContactView;
