/**
 * Lighthouse movil sobre el build de produccion, 3 pasadas por ruta.
 *
 * Reporta la MEDIANA y el PEOR valor de cada ruta. Nada se redondea al alza: el
 * criterio de aceptacion es rendimiento >= 90 y un 89,6 es un 89.
 *
 *   node scripts/lighthouse-mobile.mjs --base http://127.0.0.1:3220 --runs 3 \
 *        --label antes --out ../lighthouse
 *
 * Las rutas por defecto son las cuatro del criterio: portada, las dos areas con
 * rejilla y la ficha de proyecto con la media mas pesada.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join, resolve } from 'node:path';

const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i === -1 ? fallback : args[i + 1];
};

const BASE = arg('base', 'http://127.0.0.1:3220').replace(/\/+$/, '');
const RUNS = Number(arg('runs', '3'));
const LABEL = arg('label', 'run');
const OUT = resolve(arg('out', join(process.cwd(), '..', 'lighthouse')));

const DEFAULT_ROUTES = [
  '/',
  '/data',
  '/civil-bim',
  '/proyectos/digital-twin-sismico-en-tiempo-real-con-machine-learning',
];
const routesArg = arg('routes', '');
const ROUTES = routesArg ? routesArg.split(',') : DEFAULT_ROUTES;

/** Ruta al `cli/index.js` de Lighthouse. Sin ella se cae a `npx lighthouse@13`. */
const CLI = arg('cli', process.env.LIGHTHOUSE_CLI ?? '');
const quote = (value) => (/\s/.test(value) ? `"${value}"` : value);

mkdirSync(OUT, { recursive: true });

/** Mediana sin interpolar hacia arriba: con n par se toma el valor inferior. */
function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor((sorted.length - 1) / 2)];
}

/** Trunca, nunca redondea al alza: 89,6 tiene que leerse 89. */
function scoreOf(raw) {
  return Math.floor((raw ?? 0) * 100);
}

const results = [];
/** `runsByRoute[ruta]` acumula las pasadas de esa ruta. */
const runsByRoute = new Map(ROUTES.map((route) => [route, []]));

/**
 * Se **intercalan** las pasadas: pasada 0 de todas las rutas, luego la 1, etc.
 *
 * No es un detalle. Midiendo ruta por ruta, un pico de carga de la máquina cae
 * entero sobre la ruta que tocara y la hunde 10 puntos mientras las demás salen
 * limpias — pasó de verdad: `/data`, sin extrusión y sin cambios, marcó 82
 * cuando en la tanda anterior marcaba 92. Intercalando, el ruido se reparte
 * entre todas y la ruta de control sirve para lo que tiene que servir: decir
 * cuánto de la diferencia es real.
 */
for (let i = 0; i < RUNS; i += 1) {
  for (const route of ROUTES) {
    const url = `${BASE}${route}`;
    const runs = runsByRoute.get(route);
    const outFile = join(OUT, `${LABEL}${route.replace(/[^a-z0-9]+/gi, '_')}-${i}.json`);
    const lhArgs = [
      url,
      '--quiet',
      '--only-categories=performance,accessibility,best-practices,seo',
      '--form-factor=mobile',
      '--screenEmulation.mobile',
      '--throttling-method=simulate',
      '--output=json',
      `--output-path=${outFile}`,
      '--chrome-flags=--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage',
    ];

    // Se invoca el CLI con el propio node en vez de `npx`: desde Node 20.12
    // spawnSync se niega a ejecutar un `.cmd` sin shell, y en Windows npx lo es.
    const proc = CLI
      ? spawnSync(process.execPath, [CLI, ...lhArgs], {
          encoding: 'utf8',
          stdio: ['ignore', 'pipe', 'pipe'],
          timeout: 300000,
        })
      : spawnSync('npx', ['--yes', 'lighthouse@13', ...lhArgs.map(quote)], {
          encoding: 'utf8',
          stdio: ['ignore', 'pipe', 'pipe'],
          timeout: 300000,
          shell: true,
        });

    // En Windows Lighthouse a veces sale con EPERM al borrar el perfil temporal
    // de Chrome *despues* de escribir el informe. Manda el informe, no el codigo.
    if (!existsSync(outFile)) {
      console.error(
        `[fallo] ${url} pasada ${i}:`,
        proc.error?.message ?? proc.stderr?.slice(-1200) ?? `status ${proc.status}`,
      );
      continue;
    }

    const report = JSON.parse(readFileSync(outFile, 'utf8'));
    const audits = report.audits ?? {};
    runs.push({
      performance: scoreOf(report.categories?.performance?.score),
      accessibility: scoreOf(report.categories?.accessibility?.score),
      bestPractices: scoreOf(report.categories?.['best-practices']?.score),
      seo: scoreOf(report.categories?.seo?.score),
      lcp: Math.round(audits['largest-contentful-paint']?.numericValue ?? 0),
      cls: Number((audits['cumulative-layout-shift']?.numericValue ?? 0).toFixed(4)),
      tbt: Math.round(audits['total-blocking-time']?.numericValue ?? 0),
      fcp: Math.round(audits['first-contentful-paint']?.numericValue ?? 0),
      si: Math.round(audits['speed-index']?.numericValue ?? 0),
      bytes: Math.round((audits['total-byte-weight']?.numericValue ?? 0) / 1024),
    });
    process.stdout.write(`${route} `);
  }
  process.stdout.write(`\n[pasada ${i + 1}/${RUNS} completa]\n`);
}

for (const route of ROUTES) {
  const runs = runsByRoute.get(route);
  if (runs.length === 0) {
    console.error(`[sin datos] ${route}`);
    continue;
  }

  const pick = (key) => runs.map((r) => r[key]);
  results.push({
    route,
    runs: runs.length,
    perf: { median: median(pick('performance')), worst: Math.min(...pick('performance')) },
    a11y: { median: median(pick('accessibility')), worst: Math.min(...pick('accessibility')) },
    bp: { median: median(pick('bestPractices')), worst: Math.min(...pick('bestPractices')) },
    seo: { median: median(pick('seo')), worst: Math.min(...pick('seo')) },
    lcp: { median: median(pick('lcp')), worst: Math.max(...pick('lcp')) },
    cls: { median: median(pick('cls')), worst: Math.max(...pick('cls')) },
    tbt: { median: median(pick('tbt')), worst: Math.max(...pick('tbt')) },
    fcp: { median: median(pick('fcp')), worst: Math.max(...pick('fcp')) },
    si: { median: median(pick('si')), worst: Math.max(...pick('si')) },
    bytes: { median: median(pick('bytes')), worst: Math.max(...pick('bytes')) },
    raw: runs,
  });
  console.log(`${route}: perf ${results.at(-1).perf.median} (peor ${results.at(-1).perf.worst})`);
}

writeFileSync(join(OUT, `${LABEL}-summary.json`), JSON.stringify(results, null, 2));

console.log(`\n=== ${LABEL} · movil · mediana de ${RUNS} pasadas ===`);
const pad = (v, n) => String(v).padEnd(n);
console.log(
  pad('ruta', 46),
  pad('perf', 10),
  pad('a11y', 6),
  pad('LCP ms', 12),
  pad('CLS', 12),
  pad('TBT ms', 10),
  pad('kB', 8),
);
for (const r of results) {
  console.log(
    pad(r.route.slice(0, 45), 46),
    pad(`${r.perf.median} (${r.perf.worst})`, 10),
    pad(r.a11y.median, 6),
    pad(`${r.lcp.median} (${r.lcp.worst})`, 12),
    pad(`${r.cls.median} (${r.cls.worst})`, 12),
    pad(`${r.tbt.median} (${r.tbt.worst})`, 10),
    pad(r.bytes.median, 8),
  );
}
console.log('formato: mediana (peor)');
