/**
 * Unifica las salidas de `transcode.mjs` e `images.mjs` (y copia los documentos)
 * en un único manifiesto `content/media-manifest.json`.
 *
 * `content/catalog.seed.json` referencia rutas del sitio antiguo
 * (`projects/videos/Grabación_2025-05-13_083215.mp4`). El cargador del seed
 * necesita traducirlas a la clave definitiva de Supabase Storage, y además
 * conocer las renditions y el póster de cada vídeo para poblar
 * `project_media.renditions`.
 */
import { copyFile, mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { basename, dirname, extname, join, relative } from 'node:path';

// Origen del media sin transformar. Por defecto el volcado del sitio en vivo
// (`tools/media/live`, ver tools/download_live_media.py); se puede apuntar a
// otro directorio como primer argumento.
const SRC = process.argv[2] ?? join(process.cwd(), 'live');
const OUT_DIR = process.argv[3] ?? join(process.cwd(), 'out');
const REPO = join(process.cwd(), '..', '..');
const MANIFEST = join(REPO, 'content', 'media-manifest.json');

// `.ipynb` está aquí porque el proyecto 16 publica su notebook de entrenamiento
// como documento descargable.
const DOC_EXT = new Set(['.pdf', '.csv', '.xlsx', '.xls', '.docx', '.ipynb']);

const slugify = (value) =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

async function* walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else yield full;
  }
}

async function main() {
  const entries = {};

  // --- imágenes -----------------------------------------------------------
  const images = JSON.parse(await readFile(join(OUT_DIR, 'images', 'manifest.json'), 'utf8'));
  for (const image of images) {
    const entry = {
      kind: 'image',
      storagePath: `media/${image.storagePath}`,
      localFile: join('out', 'images', image.storagePath),
      bytes: image.bytes,
    };
    if (image.animated) {
      // Sigue siendo `kind: image` (entra en un <img> tal cual), pero el
      // consumidor puede preferir la rendition de vídeo, mucho más ligera.
      entry.animated = true;
      entry.frames = image.frames;
      entry.video = {
        storagePath: `media/${image.video.storagePath}`,
        localFile: join('out', 'images', image.video.storagePath),
        bytes: image.video.bytes,
      };
    }
    entries[image.legacyPath] = entry;
  }

  // --- vídeos -------------------------------------------------------------
  const videos = JSON.parse(await readFile(join(OUT_DIR, 'videos', 'manifest.json'), 'utf8'));
  for (const video of videos) {
    const legacyPath = `projects/videos/${video.original}`;
    const renditions = {};
    for (const [label, data] of Object.entries(video.renditions)) {
      renditions[label] = {
        storagePath: `media/projects/videos/${data.file}`,
        localFile: join('out', 'videos', data.file),
        bytes: data.bytes,
      };
    }
    entries[legacyPath] = {
      kind: 'video',
      // La rendition 1080 es la canónica; `renditions` lleva ambas para el <source>.
      storagePath: renditions['1080'].storagePath,
      posterPath: `media/projects/videos/${video.poster}`,
      posterLocalFile: join('out', 'videos', video.poster),
      durationSeconds: video.durationSeconds,
      width: video.sourceWidth,
      height: video.sourceHeight,
      renditions,
    };
  }

  // --- documentos: no se transforman, solo se renombra la clave ------------
  // `_casemap.json` deshace las colisiones de mayúsculas del volcado (ver
  // tools/download_live_media.py); sin él se perdería el archivo colisionado.
  let caseMap = {};
  try {
    caseMap = JSON.parse(await readFile(join(SRC, '_casemap.json'), 'utf8'));
  } catch { /* sin colisiones */ }

  const docsOut = join(OUT_DIR, 'documents');
  const takenDocs = new Set();
  await mkdir(docsOut, { recursive: true });
  for await (const source of walk(SRC)) {
    const ext = extname(source).toLowerCase();
    if (!DOC_EXT.has(ext)) continue;

    const diskPath = relative(SRC, source).split('\\').join('/');
    const legacyPath = caseMap[diskPath] ?? diskPath;
    const folder = dirname(legacyPath);
    const stem = slugify(basename(legacyPath, ext));
    let name = `${stem}${ext}`;
    for (let n = 2; takenDocs.has(folder === '.' ? name : `${folder}/${name}`); n += 1) {
      name = `${stem}-${n}${ext}`;
    }
    const storagePath = folder === '.' ? name : `${folder}/${name}`;
    takenDocs.add(storagePath);
    const target = join(docsOut, storagePath);

    await mkdir(dirname(target), { recursive: true });
    await copyFile(source, target);

    entries[legacyPath] = {
      kind: 'document',
      storagePath: `media/${storagePath}`,
      localFile: join('out', 'documents', storagePath),
      bytes: (await stat(target)).size,
    };
  }

  await mkdir(dirname(MANIFEST), { recursive: true });
  await writeFile(
    MANIFEST,
    JSON.stringify(
      {
        _generated_by: 'tools/media/manifest.mjs',
        _base: 'tools/media',
        _note:
          'Clave = ruta del sitio antiguo tal como aparece en catalog.seed.json. ' +
          'Valor = destino en Supabase Storage + archivo local a subir.',
        entries,
      },
      null,
      2,
    ),
  );

  const byKind = Object.values(entries).reduce((acc, entry) => {
    acc[entry.kind] = (acc[entry.kind] ?? 0) + 1;
    return acc;
  }, {});
  console.log(`escrito ${MANIFEST}`);
  console.log(byKind);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
