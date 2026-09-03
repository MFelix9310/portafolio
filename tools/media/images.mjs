/**
 * Normaliza las imágenes heredadas del portafolio Django.
 *
 * El peso no es el problema (2.8 MB en total). El problema son los nombres:
 * `Diseño_sin_título_1.jpg` o `Captura_de_pantalla_2025-05-13_072544.png` se
 * rompen como claves de Supabase Storage y como URLs. Se renombra a ASCII con
 * guiones y, de paso, se convierte a WebP (calidad 82) con tope de 1920 px.
 *
 * La salida incluye un manifiesto `legacy path -> storage path` porque
 * `content/catalog.seed.json` referencia las rutas antiguas y el cargador del
 * seed necesita traducirlas.
 *
 * GIF animado: el contenido recuperado del sitio en vivo trae animaciones de
 * 40 a 334 fotogramas (gemelos digitales sísmicos, campos de esfuerzo GNN,
 * convergencia Monte Carlo) que pesan 75 MB en GIF. Se codifican a WebP animado
 * —sustituto directo dentro de un `<img>`— y además se emite una rendition
 * H.264 en el manifiesto, porque para este contenido un `<video autoplay loop
 * muted>` pesa un orden de magnitud menos. El consumidor elige; el manifiesto
 * lleva las dos.
 */
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { basename, dirname, extname, join, relative } from 'node:path';
import ffmpeg from 'ffmpeg-static';
import { path as ffprobe } from 'ffprobe-static';

const run = promisify(execFile);

const SRC = process.argv[2] ?? 'C:/tmp/portfolio-research/PORTFOLIO_WEB/assets/media';
const OUT = process.argv[3] ?? join(process.cwd(), 'out', 'images');

const IMAGE_EXT = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp']);

/** Nº de fotogramas. Un GIF de 1 es una imagen fija y va por la ruta normal. */
async function frameCount(file) {
  try {
    const { stdout } = await run(ffprobe, [
      '-v', 'error', '-select_streams', 'v:0', '-count_frames',
      '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', file,
    ]);
    return Number.parseInt(stdout.trim(), 10) || 1;
  } catch {
    return 1;
  }
}

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

/**
 * `_casemap.json` deshace las colisiones de mayúsculas que NTFS obliga a hacer
 * al descargar (`projects/MINIATURA.jpg` y `projects/miniatura.jpg` son dos
 * ficheros distintos en el sitio). Devuelve ruta en disco → ruta real del sitio.
 */
async function loadCaseMap(dir) {
  try {
    return JSON.parse(await readFile(join(dir, '_casemap.json'), 'utf8'));
  } catch {
    return {};
  }
}

async function main() {
  const manifest = [];
  const taken = new Set();
  const caseMap = await loadCaseMap(SRC);
  let before = 0;
  let after = 0;

  for await (const source of walk(SRC)) {
    if (!IMAGE_EXT.has(extname(source).toLowerCase())) continue;

    // La ruta relativa se conserva como carpeta (projects/, profile/…) porque el
    // seed referencia `projects/1.png`, no solo el nombre del archivo.
    const diskPath = relative(SRC, source).split('\\').join('/');
    const legacyPath = caseMap[diskPath] ?? diskPath;
    const folder = dirname(legacyPath);
    const slug = slugify(basename(legacyPath, extname(legacyPath)));
    // slugify pasa a minúsculas, así que MINIATURA.jpg y miniatura.jpg
    // producirían la misma clave. Se desambigua o se pierde un archivo.
    let storagePath = folder === '.' ? `${slug}.webp` : `${folder}/${slug}.webp`;
    for (let n = 2; taken.has(storagePath); n += 1) {
      storagePath = folder === '.' ? `${slug}-${n}.webp` : `${folder}/${slug}-${n}.webp`;
    }
    taken.add(storagePath);
    const target = join(OUT, storagePath);
    const frames = await frameCount(source);
    const animated = frames > 1;

    await mkdir(dirname(target), { recursive: true });
    if (animated) {
      // 1280 px de ancho: por encima el WebP animado se dispara y estas
      // animaciones se ven a media columna, no a pantalla completa.
      await run(ffmpeg, [
        '-y', '-i', source,
        '-vf', "scale='min(1280,iw)':-2:flags=lanczos",
        '-c:v', 'libwebp_anim', '-lossless', '0', '-quality', '70',
        '-compression_level', '6', '-loop', '0',
        target,
      ], { maxBuffer: 1024 * 1024 * 32 });
    } else {
      await run(ffmpeg, [
        '-y', '-i', source,
        '-vf', "scale='min(1920,iw)':-2:flags=lanczos",
        '-c:v', 'libwebp', '-quality', '82',
        target,
      ], { maxBuffer: 1024 * 1024 * 32 });
    }

    const sourceBytes = (await stat(source)).size;
    const targetBytes = (await stat(target)).size;
    before += sourceBytes;
    after += targetBytes;

    const entry = { legacyPath, storagePath, sourceBytes, bytes: targetBytes };

    if (animated) {
      // Rendition de vídeo para quien pueda usar <video>: mismo fotograma,
      // una fracción del peso. `-an` porque un GIF no lleva audio.
      const videoPath = storagePath.replace(/\.webp$/, '.mp4');
      const videoTarget = join(OUT, videoPath);
      await run(ffmpeg, [
        '-y', '-i', source,
        '-vf', "scale='min(1280,iw)':-2:flags=lanczos",
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '28',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an',
        videoTarget,
      ], { maxBuffer: 1024 * 1024 * 32 });
      const videoBytes = (await stat(videoTarget)).size;
      after += videoBytes;
      entry.animated = true;
      entry.frames = frames;
      entry.video = { storagePath: videoPath, bytes: videoBytes };
    }

    manifest.push(entry);
  }

  await writeFile(join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2));
  const mb = (b) => (b / 1024 / 1024).toFixed(2);
  console.log(`${manifest.length} imágenes: ${mb(before)}MB → ${mb(after)}MB`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
