# Decisiones de arquitectura

Portafolio de Félix Ruiz M. — reemplazo del sitio Django/Bootstrap anterior.

## D1 — Lenguaje del backend: Python + FastAPI

**Alternativa descartada:** Node/NestJS o un núcleo hexagonal en TypeScript dentro
del propio Next.js (un solo despliegue).

**Elegido:** Python 3.12 + FastAPI, servicio independiente.

Razones, en orden de peso:

1. **Coherencia con lo que el portafolio afirma.** El sitio sostiene que Félix es
   Python developer. Un backend en TypeScript contradice la tesis en el único
   artefacto que el visitante puede inspeccionar de verdad. El backend es una
   pieza del portafolio, no solo su plomería.
2. **Precedente probado en Momentum.** El repo `momentum_backend` ya demuestra el
   patrón — puertos ABC en dominio, adaptadores en infraestructura, `Container` de
   DI manual, `create_app(container)` — con persistencia GraphQL/8base intercambiable.
   Se reutiliza el layout y se corrigen sus fugas (ver D2).
3. **El coste habitual de esta elección se neutraliza con ISR.** El argumento
   contra un backend separado es la latencia y el cold start en la ruta pública.
   Aquí el front usa ISR: las páginas se generan estáticamente y se revalidan por
   webhook cuando el admin publica. El visitante recibe HTML desde el CDN de
   Vercel y **nunca** espera a Python. El backend solo se invoca en build,
   revalidación y desde el panel `/admin`, donde 1-2 s de arranque en frío son
   irrelevantes.

Consecuencia asumida: dos despliegues (Vercel + un host Python). Es el precio de
que el backend cuente algo.

## D2 — Regla de dependencia, verificada por test

`src/domain` no puede importar `src.application` ni `src.infrastructure`, ni
ningún framework (FastAPI, Pydantic, supabase, httpx). Momentum falla justo aquí
—sus servicios de dominio importan `src.infrastructure.parsers` y
`src.application.dto`— porque nada lo comprobaba. Aquí hay un test de
arquitectura que recorre el AST de cada módulo de dominio y falla el build si
aparece un import prohibido.

El dominio usa `@dataclass` y `abc.ABC`. Pydantic vive en la frontera HTTP.

## D3 — Supabase como adaptador, no como atajo

- **Postgres** implementa los puertos `ProjectRepository`, `ExperienceRepository`,
  etc. El dominio no sabe que existe; solo `infrastructure/persistence/supabase/`
  importa el cliente.
- **Auth**: el panel se autentica contra Supabase Auth. FastAPI verifica el JWT
  contra el JWKS del proyecto — no confía en el cliente.
- **Storage**: imágenes y vídeo. El puerto es `MediaStoragePort`; el adaptador
  actual es Supabase Storage y puede sustituirse por Bunny/Cloudflare Stream sin
  tocar dominio ni casos de uso.
- **RLS**: el anon key solo lee filas `status = 'published'`. La escritura exige
  el usuario autenticado de Félix. La política vive en la base, no en el código,
  para que un fallo de la aplicación no abra la escritura.

## D4 — Un solo catálogo, etiquetado por área y subárea

`/data`, `/developer` y `/civil-bim` son **vistas filtradas** de la misma tabla
`projects` vía `project_subareas`. No hay contenido duplicado. Un proyecto puede
pertenecer a varias áreas (el cruce civil+datos lo exige).

## D5 — Bilingüe ES/EN conservado, con fallback

El sitio anterior duplica cada campo con sufijo `_en` y muchos están vacíos. Se
conserva la capacidad bilingüe pero como **JSONB por locale** (`{"es": "...",
"en": "..."}`), con ES obligatorio e EN opcional y fallback automático a ES. Así
no se pierde la traducción ya escrita, el panel no obliga a rellenar dos idiomas
para publicar, y añadir un tercer idioma no requiere migración de columnas.

## D6 — Vídeo: transcodificar en origen, reproducir en lightbox

Los seis vídeos heredados son screencasts H.264 a ~8 Mbps — un orden de magnitud
por encima de lo necesario para contenido casi estático. `tools/media` los
recodifica con `-tune stillimage` y `+faststart` a dos renditions (1080p/720p)
más un póster WebP.

En la tarjeta se muestra solo el póster con `preload="none"`: coste de red cero
hasta que el usuario decide ver. Al pulsar, un lightbox lo reproduce a hasta 92
vw — "más grande" — y ya cabe en memoria porque el archivo pesa megabytes, no
decenas.

Para vídeos que Félix suba desde el panel no hay transcodificación en servidor
(Supabase Storage no transcodifica). El panel avisa por encima de un umbral de
tamaño y `tools/media` sirve para preparar el archivo antes de subirlo. Si en el
futuro hace falta automatizarlo, `MediaStoragePort` ya permite enchufar un
servicio de streaming sin tocar el dominio.

## D7 — Sin Docker: dos adaptadores de persistencia

No se usa el stack local de Supabase (requiere Docker). En su lugar el backend
implementa **dos adaptadores para los mismos puertos**:

| `PERSISTENCE_BACKEND` | Adaptador | Uso |
|---|---|---|
| `json` (por defecto) | `infrastructure/persistence/json/` sobre `content/catalog.seed.json` | Desarrollo. La API arranca con datos reales y sin ninguna infraestructura. |
| `supabase` | `infrastructure/persistence/supabase/` | Producción. |

Esto no es un rodeo por no tener Docker: es la prueba **ejecutable** de que el
dominio no depende de la infraestructura, que es el primer criterio de
aceptación. La misma batería de tests de casos de uso corre contra ambos
adaptadores.

Consecuencia sobre las migraciones: se escriben y se validan sintácticamente sin
servidor (`supabase/validate_sql.py` con sqlglot), pero **no** se aplican contra
un Postgres real hasta que exista el proyecto en la nube. Las políticas RLS son
justo el tipo de código que parsea bien y se comporta mal, así que
`supabase/README.md` incluye una lista de comprobación manual para el primer
`db push`: que anon no vea borradores, que anon no pueda escribir, que anon
pueda insertar en `messages` pero no leerlos, y que el admin sí vea borradores.

Lo mismo para auth: hay un `AUTH_BACKEND=dev` para desarrollo, y
`Settings.validate()` aborta el arranque si se combina con
`ENVIRONMENT=production`.

## D8 — Imágenes: se adopta `next/image`

**Contexto.** `next.config.ts` declaraba `images.formats` desde el principio, pero
no había un solo `next/image` en el código: cuatro `<img>` crudos con su
`eslint-disable` correspondiente. Es decir, configuración muerta que además
sugería una optimización que no ocurría.

**Alternativa descartada:** borrar `images.formats` y dejar los `<img>` crudos
documentando el porqué.

**Elegido:** adoptar `next/image` en las tres superficies públicas —galería de la
ficha, portada de la tarjeta y póster del vídeo— y declarar los `remotePatterns`
de Supabase Storage.

Razón: el catálogo reconstruido trae imágenes de entre 12 kB y 6 MB que se
servían a tamaño completo a un teléfono de 360 px de ancho. `next/image` genera
el `srcset` y sirve el ancho que toca, que es la palanca de LCP que faltaba en
móvil. Como efecto secundario, `images.formats` pasa a significar algo.

`remotePatterns` no es opcional: en producción la media viene de Supabase
Storage y sin ellos `next/image` rechaza el host con un 400. Se derivan de
`NEXT_PUBLIC_MEDIA_URL` / `NEXT_PUBLIC_SUPABASE_URL` para que no se queden
desincronizados, más un comodín `*.supabase.co` para previews.

**Excepción deliberada:** el listado de media del panel (`MediaPanel`) sigue con
un `<img>` crudo. Son miniaturas de 40×56 px con dimensiones fijas —no hay ni
CLS ni bytes que ganar— y la URL viene tal cual de la fila de `project_media`: si
apuntara a un host que `remotePatterns` no contempla, `next/image` devolvería un
400 y el administrador vería una miniatura rota en vez de la imagen que acaba de
subir. Un `<img>` degrada; el optimizador falla. Queda anotado en el propio
componente.

## D9 — GIF animados: `<video>` con el WebP dentro como alternativa

El catálogo reconstruido trae doce animaciones de gemelos digitales y campos de
esfuerzos (de 40 a 334 fotogramas). En WebP animado suman **36,94 MB**; la
rendition H.264 que ya produce `tools/media` suma **2,17 MB** — treinta veces
menos, misma imagen.

Cuatro de ellas son además la portada de su proyecto, así que la rejilla de
`/civil-bim` descargaba 8,97 MB en cuatro peticiones sólo para las miniaturas.

`ProjectShot` pinta `<video autoplay loop muted playsinline preload="metadata">`
cuando existe la rendition, y deja el WebP de alternativa.

Detalle que costó una medición: la forma declarativa —meter el `<img>` **dentro**
del `<video>` como contenido alternativo— no es gratis. Se comprobó en Chrome
(`naturalWidth` del `<img>` distinto de cero con el vídeo reproduciéndose) que un
`<img>` conectado al documento descarga su recurso aunque la alternativa no se
pinte nunca: se pagaban los 201 kB del MP4 **y** los 5,9 MB del WebP. Por eso
`AnimatedShot` sólo monta el `<img>` cuando el `<video>` emite `error`.

Nota de contrato pendiente: la API no emite el campo `video` de una imagen
animada (`presenters.media` no lo tiene), así que en modo API la ruta H.264 se
recupera del `content/media-manifest.json` que viaja con el build. En cuanto el
backend lo emita, `web/src/lib/api/catalog.ts` puede quedarse sólo con el campo.

## D10 — Lighthouse móvil: dónde estamos y qué queda (2026-08-31)

Medido sobre `pnpm build` + `pnpm start`, modo API, emulación móvil, tres
pasadas por ruta, con `web/scripts/lighthouse-mobile.mjs`. Medianas, y entre
paréntesis el peor valor de las tres.

> Nota de método: esta primera tabla se midió **ruta por ruta**, que resultó ser
> un error. Un pico de carga de la máquina cae entero sobre la ruta que toque y
> la hunde diez puntos mientras las demás salen limpias. El script ahora
> **intercala** las pasadas (la 0 de todas las rutas, luego la 1…), que es lo que
> hace que una ruta de control valga para algo. Las medidas del bloque siguiente
> ya usan ese método.

| Ruta | Antes | Después | Bytes antes | Bytes después |
|---|---|---|---|---|
| `/` | 92 (91) | 92 (86) | 355 kB | 355 kB |
| `/data` | 92 (89) | 92 (89) | 6509 kB | 1563 kB |
| `/civil-bim` | 88 (87) | 86 (85) | 9734 kB | 1673 kB |
| `/proyectos/digital-twin-sismico…` | 93 (92) | 92 (91) | 6327 kB | 592 kB |

Dos lecturas honestas de esta tabla:

1. **Los bytes bajan entre 4× y 11×; la puntuación no se mueve.** Es esperable:
   Lighthouse mide contra `127.0.0.1`, donde un WebP de 3 MB tarda 46 ms en
   llegar. La simulación de red no le pone precio real a los megabytes, así que
   sustituir 9 MB de GIF por 1,1 MB de vídeo no aparece en el número — pero es la
   diferencia entre usable y no usable en un móvil con datos.
2. **La máquina de medida hace ruido.** `/` no cambió una línea y su peor pasada
   pasó de 91 a 86. Cualquier diferencia menor de ~3 puntos en esta tabla es
   ruido, no señal.

### Resuelto: `/civil-bim` sube a 89 al degradar el 3D por debajo de 768 px

Tras aplicar el corte por ancho de viewport en `canRender3d()`
(ver `docs/03-pieza-3d.md`), medido con **5 pasadas intercaladas** y con `/` y
`/data` como control en la misma tanda:

| Ruta | Antes del corte | Tras el corte | JS transferido |
|---|---|---|---|
| `/civil-bim` | 86 (85), TBT 243 ms | **89 (88), TBT 131 ms** | 319 kB → **190 kB** |
| `/` (control, sin cambios) | 92 (86) | 91 (91) | — |
| `/data` (control, sin cambios) | 92 (89) | 90 (89) | 190 kB |

Lectura honesta: los controles bajaron 1 y 2 puntos entre tandas, así que la
tanda nueva mide algo por debajo de la vieja; `/civil-bim` sube 3 puntos contra
ese fondo, lo que deja la mejora real en unos **4-5 puntos**. El TBT casi a la
mitad y el JS idéntico al de `/data` son la confirmación de que el mecanismo es
el que se creía y no otra cosa.

**Sigue por debajo de 90, y se deja así.** Con 89 (peor 88), `/civil-bim` está
ahora dentro del ruido de las rutas que sí pasan (`/` 91, `/data` 90): la
extrusión ya no es lo que lo diferencia, y el punto que falta es el mismo suelo
que tiene todo el sitio en esta máquina. Forzarlo más significaría recortar algo
que sí se usa, y un 89 honesto vale más que un 90 comprado.

En escritorio la pieza sigue entera y `/civil-bim` puntúa **100** (LCP 712 ms,
TBT 2 ms), con los chunks de `three` descargándose como siempre.

### El diagnóstico original, para que no se pierda

Ya estaba en 88 antes de tocar nada. La causa está medida y es la pieza 3D:

| | `/data` | `/civil-bim` |
|---|---|---|
| Tarjetas de proyecto | 19 | 15 |
| JavaScript transferido | 190 kB | 319 kB |
| TBT | 113 ms | 243 ms |
| Rendimiento | 92 | 86 |

`/civil-bim` tiene **menos** tarjetas que `/data` y peor puntuación. Los 129 kB
de diferencia son exactamente los chunks de la extrusión (`three` + R3F), que en
un móvil de 812 px de alto cae a unos 70 px del pliegue: dentro del `rootMargin`
de 300 px del `IntersectionObserver`, así que se monta a la vez que hidrata la
rejilla. La hidratación de las tarjetas **no** es el problema: si lo fuera,
`/data` puntuaría peor.

La pieza cumple su propia especificación (`docs/03-pieza-3d.md`: fuera del bundle
inicial, fuera de la ruta crítica de LCP, por debajo de 180 kB gzip). El
presupuesto es el que se queda corto para un 90 en móvil, no la implementación.

Lo que se probó y **no** funcionó: armar la extrusión en `requestIdleCallback` en
vez de al intersectar. Empeoró (86 → 84, TBT 243 → 348): mover el trabajo más
tarde alarga la ventana de tareas largas en vez de acortarla. Revertido.

**Resuelto** con el corte por ancho de 768 px, que resultó no ser un cambio de
producto sino la aplicación de una regla ya escrita: `docs/01-direccion-de-arte.md`
manda degradar a la planta 2D en móvil. Ver el bloque anterior.

### Queda pendiente: el salto de la propia pieza (CLS 0,0279)

`/civil-bim` es la única ruta con CLS por encima de 0,01, y está localizado: el
`loading` de `ExtrusionSlot` reserva `aspect-[16/9]` (188 px a 335 de ancho) y la
pieza montada mide 254 px, porque en móvil el pie va **debajo** del dibujo y no
superpuesto (`md:absolute`). Todo lo que hay por debajo baja ~66 px al hidratar.
Confirmado por dos vías: el nodo que señala el audit `layout-shifts` de Lighthouse
(`div.lamina > div.mb-12`) y la medida directa de `getBoundingClientRect`.

El arreglo exacto no es afinar el placeholder —la altura del pie depende del
largo del texto, que cambia con el idioma— sino **renderizar la carcasa en
servidor**: quitar el `ssr: false` de `ExtrusionSlot` e importar
`ExtrusionPlaceholder` directamente. La planta y su pie entrarían en el HTML,
el hueco quedaría reservado desde el primer pintado y desaparecería también el
recuadro gris que se ve un instante antes de hidratar. El `ssr: false` de fuera
no protege de nada: `three` ya está detrás de su propio `dynamic(ssr: false)`
dentro de la carcasa.

Comprobado que es viable: `PlanSvg` no es componente cliente y no usa
`Math.random`, `Date.now`, `useId` ni `window`, así que no hay riesgo de desajuste
de hidratación. No se ha hecho porque no mueve la puntuación —0,0279 ya puntúa
100 en CLS, el umbral son 0,1— y no tocaba meter otro cambio en la arquitectura
de la pieza en la misma tanda en la que se medía el corte por ancho.
