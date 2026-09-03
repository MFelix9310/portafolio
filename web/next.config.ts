import type { NextConfig } from 'next';

/**
 * Hosts de los que `next/image` acepta optimizar.
 *
 * En desarrollo la media se sirve desde `web/public`, que es local y no necesita
 * permiso. En producción vive en Supabase Storage, y sin `remotePatterns`
 * `next/image` rechaza el host con un 400 —así que esto no es opcional, es lo
 * que hace que el sitio se vea. Se deriva de la URL del proyecto que ya está
 * configurada en vez de escribirse a mano, para que no se quede desincronizada.
 */
function mediaRemotePatterns() {
  const candidates = [process.env.NEXT_PUBLIC_MEDIA_URL, process.env.NEXT_PUBLIC_SUPABASE_URL];
  const hosts = new Set<string>();

  for (const candidate of candidates) {
    if (!candidate) continue;
    try {
      hosts.add(new URL(candidate).hostname);
    } catch {
      // Una variable mal escrita no debe tumbar el build; simplemente no añade host.
    }
  }

  const patterns = [...hosts].map((hostname) => ({
    protocol: 'https' as const,
    hostname,
    pathname: '/storage/v1/object/public/**',
  }));

  // Red de seguridad para previews y ramas, donde la URL del proyecto puede no
  // estar inyectada en el build pero la media sigue viniendo de Supabase.
  patterns.push({
    protocol: 'https' as const,
    hostname: '*.supabase.co',
    pathname: '/storage/v1/object/public/**',
  });

  return patterns;
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  // El seed de `content/` vive fuera de `web/`; se lee con `fs` en build/ISR.
  outputFileTracingIncludes: {
    '/**': ['../content/catalog.seed.json', '../content/media-manifest.json'],
  },
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: mediaRemotePatterns(),
  },
};

export default nextConfig;
