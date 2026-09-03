import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import DimensionLine from '@/components/primitives/DimensionLine';
import Reveal from '@/components/motion/Reveal';
import { getCatalog } from '@/lib/api/catalog';
import { copy, plural } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';

const year = (date: string | null | undefined) => (date ? date.slice(0, 4) : '');

export async function AboutView({ locale }: { locale: Locale }) {
  const c = copy(locale);
  const catalog = await getCatalog();

  return (
    <div className="lamina py-12 md:py-16">
      <Reveal stagger="[data-head]" as="header" className="mb-12 flex flex-col gap-5">
        <Annotation data-head leader>
          {catalog.profile.name}
        </Annotation>
        <h1 data-head className="font-display text-display-md font-semibold text-content">
          {c.about.heading}
        </h1>
        {c.about.paragraphs.map((paragraph, index) => (
          <p
            key={paragraph.slice(0, 24)}
            data-head
            className={
              index === 0
                ? 'max-w-prose text-base leading-relaxed text-content md:text-lg'
                : 'max-w-prose text-base leading-relaxed text-muted'
            }
          >
            {paragraph}
          </p>
        ))}
      </Reveal>

      <div className="mb-14 grid gap-6 border-y filete py-6 md:grid-cols-3">
        <DimensionLine
          value={catalog.experiences.length}
          label={plural(catalog.experiences.length, c.chrome.metrics.experience_one, c.chrome.metrics.experience)}
          locale={locale}
        />
        <DimensionLine
          value={catalog.certifications.length}
          label={plural(catalog.certifications.length, c.chrome.metrics.certifications_one, c.chrome.metrics.certifications)}
          locale={locale}
        />
        <DimensionLine
          value={catalog.publications.length}
          label={plural(catalog.publications.length, c.chrome.metrics.publications_one, c.chrome.metrics.publications)}
          locale={locale}
          accent
        />
      </div>

      <section aria-labelledby="experiencia" className="mb-14">
        <h2 id="experiencia" className="mb-6 font-display text-2xl font-semibold text-content">
          {c.chrome.about.experience}
        </h2>
        <Reveal stagger="[data-row]" as="ul" className="flex flex-col border-t filete">
          {catalog.experiences.map((item) => (
            <li key={item.slug} data-row className="relative border-b filete py-6">
              <div className="grid gap-3 md:grid-cols-[10rem_1fr]">
                <Annotation className="tabular-nums self-start">
                  {year(item.startDate)} — {item.isCurrent ? c.chrome.about.present : year(item.endDate)}
                </Annotation>
                <div className="flex flex-col gap-2">
                  <h3 className="font-display text-lg font-semibold text-content">
                    {localize(item.position, locale)}
                  </h3>
                  <Annotation>{localize(item.company, locale)}</Annotation>
                  <p className="max-w-prose text-sm leading-relaxed text-muted">
                    {localize(item.description, locale)}
                  </p>
                  <div className="flex flex-wrap gap-x-3 gap-y-1 pt-1">
                    {item.keywords.slice(0, 8).map((keyword) => (
                      <Annotation key={keyword} className="!normal-case !tracking-[0.08em]">
                        {keyword}
                      </Annotation>
                    ))}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </Reveal>
      </section>

      <section aria-labelledby="formacion" className="mb-14">
        <h2 id="formacion" className="mb-6 font-display text-2xl font-semibold text-content">
          {c.chrome.about.education}
        </h2>
        <Reveal stagger="[data-row]" as="ul" className="grid gap-gutter md:grid-cols-2">
          {catalog.education.map((item, index) => (
            <li
              key={`${item.graduationYear}-${index}`}
              data-row
              className="relative border filete p-4"
            >
              <CornerTicks size={8} />
              <Annotation className="tabular-nums">{item.graduationYear ?? '—'}</Annotation>
              <h3 className="mt-2 font-display text-lg font-semibold text-content">
                {localize(item.title, locale)}
              </h3>
              <p className="mt-1 text-sm text-muted">{localize(item.institution, locale)}</p>
            </li>
          ))}
        </Reveal>
      </section>

      <section aria-labelledby="certificaciones" className="mb-14">
        <h2 id="certificaciones" className="mb-6 font-display text-2xl font-semibold text-content">
          {c.chrome.about.certifications}
        </h2>
        <ul className="flex flex-col border-t filete">
          {catalog.certifications.map((item) => (
            <li key={item.slug} className="border-b filete py-5">
              <div className="grid gap-2 md:grid-cols-[8rem_1fr_auto] md:items-baseline">
                <Annotation className="tabular-nums">{year(item.issuedOn)}</Annotation>
                <div>
                  <h3 className="font-display text-base font-semibold text-content">
                    {localize(item.name, locale)}
                  </h3>
                  <p className="text-sm text-muted">{localize(item.issuer, locale)}</p>
                </div>
                {item.credentialUrl ? (
                  <a
                    href={item.credentialUrl}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="font-mono text-note uppercase tracking-[0.14em] text-accent-text underline underline-offset-4"
                  >
                    {c.chrome.about.credential}
                  </a>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="publicaciones">
        <h2 id="publicaciones" className="mb-6 font-display text-2xl font-semibold text-content">
          {c.chrome.about.publications}
        </h2>
        <ul className="flex flex-col border-t filete">
          {catalog.publications.map((item) => (
            <li key={item.slug} className="border-b filete py-5">
              <div className="grid gap-2 md:grid-cols-[8rem_1fr]">
                <Annotation className="tabular-nums">{year(item.publishedOn)}</Annotation>
                <div className="flex flex-col gap-1">
                  <h3 className="font-display text-base font-semibold text-content">
                    {item.url ? (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="underline-offset-4 hover:underline"
                      >
                        {localize(item.title, locale)}
                      </a>
                    ) : (
                      localize(item.title, locale)
                    )}
                  </h3>
                  {item.authors ? (
                    <Annotation className="!normal-case !tracking-normal">
                      {localize(item.authors, locale)}
                    </Annotation>
                  ) : null}
                  {item.venue ? (
                    <p className="text-sm text-muted">{localize(item.venue, locale)}</p>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export default AboutView;
