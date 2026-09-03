/**
 * Pipeline de media del portafolio.
 *
 * Los vídeos heredados son screencasts H.264 a ~8 Mbps: sobrecodificados en un
 * orden de magnitud para contenido que es, casi todo, pixeles estáticos.
 * Se recodifican con `-tune stillimage` (x264 reparte bits hacia el detalle fino
 * del texto en pantalla en vez de hacia el movimiento) y `+faststart` (mueve el
 * moov atom al principio para que el navegador pueda empezar a reproducir sin
 * descargar el archivo entero).
 *
 * Salida por vídeo: rendition 1080p + 720p (H.264, universal) y un póster WebP.
 */
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdir, readdir, stat, writeFile } from 'node:fs/promises';
import { basename, extname, join } from 'node:path';
import ffmpeg from 'ffmpeg-static';
import { path as ffprobe } from 'ffprobe-static';

const run = promisify(execFile);

const SRC = process.argv[2] ?? 'C:/tmp/portfolio-research/PORTFOLIO_WEB/assets/media/projects/videos';
const OUT = process.argv[3] ?? join(process.cwd(), 'out', 'videos');

/** Un CRF de 26 sobre screencast es visualmente transparente; 28 en la rendition baja. */
const RENDITIONS = [
  { label: '1080', maxHeight: 1080, crf: 26 },
  { label: '720', maxHeight: 720, crf: 28 },
];

/** Nombres como `Grabación_2025-05-13_083215.mp4` rompen URLs y buckets. */
const slugify = (value) =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

async function probe(file) {
  const { stdout } = await run(ffprobe, [
    '-v', 'error',
    '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height',
    '-show_entries', 'format=duration',
    '-of', 'json',
    file,
  ]);
  const { streams, format } = JSON.parse(stdout);
  return {
    width: streams[0].width,
    height: streams[0].height,
    duration: Number(format.duration),
  };
}

async function transcode(file, source, rendition) {
  const target = join(OUT, `${file}-${rendition.label}.mp4`);
  // scale: limita la altura pero nunca amplía, y fuerza dimensiones pares (yuv420p lo exige).
  const scale = `scale=-2:'min(${rendition.maxHeight},ih)':flags=lanczos`;
  await run(ffmpeg, [
    '-y', '-i', source,
    '-vf', scale,
    '-c:v', 'libx264',
    '-preset', 'slow',
    '-crf', String(rendition.crf),
    '-tune', 'stillimage',
    '-profile:v', 'high',
    '-pix_fmt', 'yuv420p',
    '-g', '60',
    '-c:a', 'aac', '-b:a', '96k', '-ac', '2',
    '-movflags', '+faststart',
    target,
  ], { maxBuffer: 1024 * 1024 * 32 });
  return target;
}

async function poster(file, source, duration) {
  const target = join(OUT, `${file}-poster.webp`);
  // Un frame del 15% evita fundidos de entrada y pantallas en negro del inicio.
  const at = Math.max(0.5, duration * 0.15);
  await run(ffmpeg, [
    '-y', '-ss', at.toFixed(2), '-i', source,
    '-frames:v', '1',
    '-vf', "scale=-2:'min(1080,ih)':flags=lanczos",
    '-c:v', 'libwebp', '-quality', '82',
    target,
  ], { maxBuffer: 1024 * 1024 * 32 });
  return target;
}

const mb = (bytes) => (bytes / 1024 / 1024).toFixed(1);

async function main() {
  await mkdir(OUT, { recursive: true });
  const files = (await readdir(SRC)).filter((f) => extname(f).toLowerCase() === '.mp4');
  const manifest = [];
  let before = 0;
  let after = 0;

  for (const original of files) {
    const source = join(SRC, original);
    const slug = slugify(basename(original, extname(original)));
    const meta = await probe(source);
    const sourceSize = (await stat(source)).size;
    before += sourceSize;

    const outputs = {};
    for (const rendition of RENDITIONS) {
      const target = await transcode(slug, source, rendition);
      const size = (await stat(target)).size;
      after += size;
      outputs[rendition.label] = { file: basename(target), bytes: size };
      console.log(`${original} → ${basename(target)}  ${mb(sourceSize)}MB → ${mb(size)}MB`);
    }

    const posterFile = await poster(slug, source, meta.duration);
    after += (await stat(posterFile)).size;

    manifest.push({
      original,
      slug,
      durationSeconds: Number(meta.duration.toFixed(2)),
      sourceWidth: meta.width,
      sourceHeight: meta.height,
      sourceBytes: sourceSize,
      poster: basename(posterFile),
      renditions: outputs,
    });
  }

  await writeFile(join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2));
  console.log(`\nTotal: ${mb(before)}MB → ${mb(after)}MB (${(100 - (after / before) * 100).toFixed(1)}% menos)`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
