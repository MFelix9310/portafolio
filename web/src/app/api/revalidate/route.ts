import { revalidatePath, revalidateTag } from 'next/cache';
import { NextResponse } from 'next/server';

/**
 * Webhook de revalidacion ISR.
 *
 * El backend lo llama al publicar, despublicar o reordenar desde el panel
 * (`POST /admin/revalidate`, adaptador HttpFrontendRevalidation): `POST` con
 * `{"paths": [...]}` y la cabecera `x-revalidate-secret`. Sin este endpoint
 * publicar desde el panel no cambiaba nada visible hasta que caducaba el ISR
 * de cinco minutos, y el panel parecia roto.
 *
 * El secreto es compartido: REVALIDATE_SECRET aqui, FRONTEND_REVALIDATE_SECRET
 * en el backend. Si no esta configurado, se rechaza todo: un webhook sin
 * secreto es un boton publico para vaciar la cache.
 */

/** Todo lo publico, en los dos idiomas. Se usa cuando el backend no acota rutas. */
const TODAS_LAS_RUTAS = [
  '/',
  '/data',
  '/developer',
  '/civil-bim',
  '/sobre-mi',
  '/contacto',
  '/en',
  '/en/data',
  '/en/developer',
  '/en/civil-bim',
  '/en/about',
  '/en/contact',
];

/** Las fichas de proyecto se revalidan por layout: cubre todos los slugs de golpe. */
const LAYOUTS_DINAMICOS = ['/proyectos/[slug]', '/en/projects/[slug]'];

function secretoValido(request: Request): boolean {
  const esperado = process.env.REVALIDATE_SECRET;
  const recibido = request.headers.get('x-revalidate-secret');
  if (!esperado || !recibido || esperado.length !== recibido.length) return false;
  // Comparacion en tiempo constante, para no filtrar el secreto por temporizacion.
  let diff = 0;
  for (let i = 0; i < esperado.length; i += 1) {
    diff |= esperado.charCodeAt(i) ^ recibido.charCodeAt(i);
  }
  return diff === 0;
}

export async function POST(request: Request) {
  if (!process.env.REVALIDATE_SECRET) {
    return NextResponse.json({ error: 'REVALIDATE_SECRET no configurado' }, { status: 500 });
  }
  if (!secretoValido(request)) {
    return NextResponse.json({ error: 'secreto invalido' }, { status: 401 });
  }

  let pedidas: string[] = [];
  try {
    const body = (await request.json()) as { paths?: unknown };
    if (Array.isArray(body.paths)) {
      pedidas = body.paths.filter((p): p is string => typeof p === 'string' && p.startsWith('/'));
    }
  } catch {
    // Sin cuerpo o cuerpo invalido: se revalida todo, que es lo seguro.
  }

  // Primero la etiqueta, luego las rutas. `revalidatePath` invalida el render
  // de la pagina, pero no la cache de datos de los `fetch` al backend, que van
  // etiquetados como `catalog` en lib/api/client.ts. Sin esto la pagina se
  // regeneraba y volvia a leer del cache de peticiones: publicar desde el panel
  // no cambiaba nada visible hasta que caducaban los 300 segundos del fetch.
  revalidateTag('catalog');

  const rutas = pedidas.length ? pedidas : TODAS_LAS_RUTAS;
  for (const ruta of rutas) revalidatePath(ruta);
  for (const layout of LAYOUTS_DINAMICOS) revalidatePath(layout, 'layout');

  return NextResponse.json({
    revalidated: [...rutas, ...LAYOUTS_DINAMICOS],
    tags: ['catalog'],
    at: new Date().toISOString(),
  });
}
