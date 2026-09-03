/**
 * Copia a `public/media` los assets que el front necesita para verse sin backend.
 *
 * Version 2, dirigida por manifiesto. La version anterior adivinaba directorios y
 * se desincronizo de dos formas: copiaba los originales heredados en png y jpg
 * cuando el sitio pide las derivadas webp, y dejaba los videos en
 * `public/media/videos` cuando la app pide `/media/projects/videos`. Resultado,
 * 21 de 23 assets daban 404.
 *
 * Ahora la unica fuente de verdad es `content/media-manifest.json`, que ya mapea
 * cada fichero local a su clave definitiva de Storage. El contrato A4 fija que
 * esa clave incluye el nombre del bucket como primer segmento, asi que
 * `media/projects/videos/1-1080.mp4` se copia a `public/media/projects/videos/1-1080.mp4`.
 *
 * En produccion estos ficheros los sirve Supabase Storage; `public/media` esta en
 * .gitignore porque es una copia de trabajo, no parte del repositorio.
 *
 *   node scripts/sync-media.mjs
 */
import { copyFile, mkdir, readFile, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const WEB = resolve(process.cwd());
const RAIZ = resolve(WEB, '..');
const PUBLIC = join(WEB, 'public');
const MANIFEST = join(RAIZ, 'content', 'media-manifest.json');

if (!existsSync(MANIFEST)) {
  console.error(`falta ${MANIFEST}. Ejecuta antes tools/media/manifest.mjs`);
  process.exit(1);
}

const manifest = JSON.parse(await readFile(MANIFEST, 'utf8'));
const BASE = resolve(RAIZ, manifest._base ?? join('tools', 'media'));

/** Cada destino es la storagePath tal cual, porque el front pide `/media/...`. */
const pendientes = [];
for (const entrada of Object.values(manifest.entries ?? {})) {
  if (entrada.localFile && entrada.storagePath) {
    pendientes.push([entrada.localFile, entrada.storagePath]);
  }
  if (entrada.posterLocalFile && entrada.posterPath) {
    pendientes.push([entrada.posterLocalFile, entrada.posterPath]);
  }
  // Los GIF animados llevan ademas una rendition H.264: mismo contenido, un
  // orden de magnitud menos de peso para quien pueda usar <video>.
  if (entrada.video?.localFile && entrada.video?.storagePath) {
    pendientes.push([entrada.video.localFile, entrada.video.storagePath]);
  }
  for (const rendition of Object.values(entrada.renditions ?? {})) {
    if (rendition.localFile && rendition.storagePath) {
      pendientes.push([rendition.localFile, rendition.storagePath]);
    }
  }
}

let copiados = 0;
let bytes = 0;
const ausentes = [];

for (const [relativo, destinoRelativo] of pendientes) {
  const origen = resolve(BASE, relativo);
  if (!existsSync(origen)) {
    ausentes.push(relativo);
    continue;
  }
  const destino = join(PUBLIC, destinoRelativo);
  await mkdir(dirname(destino), { recursive: true });
  await copyFile(origen, destino);
  bytes += (await stat(destino)).size;
  copiados += 1;
}

console.log(`media: ${copiados} ficheros, ${(bytes / 1024 / 1024).toFixed(1)} MB en ${PUBLIC}`);

if (ausentes.length) {
  // Un fichero del manifiesto que no existe en disco significa que falta pasar
  // el pipeline de tools/media. Se falla en vez de dejar 404 silenciosos.
  console.error(`\n${ausentes.length} ficheros del manifiesto no estan en disco:`);
  for (const falta of ausentes.slice(0, 15)) console.error(`  ${falta}`);
  if (ausentes.length > 15) console.error(`  ... y ${ausentes.length - 15} mas`);
  console.error('\nEjecuta el pipeline de tools/media antes de sincronizar.');
  process.exit(1);
}
