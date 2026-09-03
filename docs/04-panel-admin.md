# Panel de administración

Félix tiene que poder cambiar **todo** el contenido sin tocar código ni
redesplegar. Es el requisito que decide si el portafolio sigue vivo dentro de un
año o se queda congelado como el anterior.

## Alcance

Ruta `/admin` dentro de la misma app de Next.js (no un subdominio: menos
superficie de despliegue y menos configuración de CORS y cookies).

CRUD completo sobre: `projects`, `experiences`, `certifications`, `education`,
`publications`, `contacts`, `areas`, `subareas`, `profile`, `project_media`.
Más lectura de `messages` (los del formulario de contacto).

Cada listado permite **reordenar** (`display_order`) y alternar
`draft ↔ published`.

## Acceso

- Login con Supabase Auth. Magic link por email como método principal — sin
  contraseña que gestionar ni recuperar.
- **Sin registro público.** No hay pantalla de "crear cuenta". La única fila de
  `admin_users` se inserta manualmente en la base; cualquier otro usuario
  autenticado que llegue a `/admin` recibe 403, no una pantalla vacía.
- Middleware de Next.js protege `/admin/*` y redirige a `/admin/login`.
- La autorización real vive en dos sitios y ambos tienen que decir que sí: la
  política RLS de Postgres y la dependencia `require_admin` de FastAPI. El
  middleware es conveniencia de UX, **no** es el control de acceso.

## Regla arquitectónica que no se negocia

El panel llama a los endpoints `/api/v1/admin/*`, que ejecutan **los mismos casos
de uso** de `src/application/use_cases` que usa el sitio público. El panel no
habla con Postgres directamente ni usa el cliente de Supabase para escribir
contenido. Si aparece un `supabase.from('projects').update(...)` en `web/`, se
ha roto la arquitectura.

Única excepción permitida: la **subida** de archivos va del navegador a Supabase
Storage con una URL firmada que emite el backend (`POST /admin/media/upload-url`).
El binario no atraviesa FastAPI —sería tonto— pero el permiso lo concede el
backend y el registro en `project_media` se crea con un caso de uso.

## Borrador y vista previa

`status: draft | published` en todas las entidades publicables.

- El sitio público solo lee `published` (lo impone RLS, no el código).
- El panel ve ambos.
- Al publicar se dispara `POST /admin/revalidate`, que revalida las rutas ISR
  afectadas. Sin eso, publicar no cambiaría nada visible y el panel parecería roto.

### Vista previa de borradores: no implementada (2026-08-31)

Este documento prometía `/civil-bim?preview=1` (y equivalentes) renderizando
borradores para sesión de admin. **No existe.** Ninguna ruta pública lee
`searchParams`, así que el enlace del panel llevaba a un 404 en el único caso en
que servía de algo —un borrador—, y en un publicado el parámetro se ignoraba.

El enlace se ha sustituido por **«Ver en el sitio»**, que sólo aparece cuando la
fila está `published` y por tanto la página pública existe de verdad. Un enlace a
una página que no existe es peor que no tener enlace.

Lo que falta para implementarla de verdad, en este orden:

1. **Backend.** `GetCatalog` ya acepta `include_drafts`, pero no hay ninguna ruta
   HTTP que lo active: `GET /api/v1/catalog` no admite el parámetro y no existe
   `GET /api/v1/admin/catalog`. Sin eso el front no tiene de dónde sacar un
   borrador, se monte la vista previa donde se monte.
2. **Front.** La vista previa **no** puede vivir en la ruta pública: leer
   `searchParams` en `/civil-bim` la convierte en dinámica para todo el mundo y
   se pierde el ISR que hoy la mantiene por encima de 90 en Lighthouse. El sitio
   correcto es una ruta bajo `/admin/*`, que el middleware ya protege, que
   reutilice `AreaView` y `ProjectView` con un catálogo que incluya borradores.

Mientras tanto, la regla se cumple igual por otra vía: el panel enseña el
borrador en el propio formulario, y publicar revalida.

## Subida de media

- Imágenes: se aceptan y se sirven vía `next/image`.
- Vídeo: **avisar por encima de 15 MB**. Supabase Storage no transcodifica, así
  que un `.mp4` de 60 MB subido desde el panel anularía justo el trabajo de
  optimización que se hizo con los heredados. El aviso explica cómo pasarlo por
  `tools/media` antes de subir, y no bloquea: informa.
- Barra de progreso real, no un spinner indefinido.

## Formularios

- Bilingüe: cada campo de texto tiene pestaña ES / EN. **ES obligatorio, EN
  opcional** — no se puede bloquear la publicación por falta de traducción (D5).
- Validación en cliente y en servidor. La del servidor es la que cuenta.
- Autoguardado de borrador o aviso al salir con cambios sin guardar. Perder un
  texto largo escrito a mano es la forma más rápida de que un panel deje de usarse.
- Confirmación explícita antes de borrar, mostrando qué se va a borrar.

## Aspecto

Hereda los tokens del sistema de diseño, pero prioriza densidad y velocidad sobre
espectáculo: aquí no hay animación de scroll ni GSAP. Es una herramienta de
trabajo. Tablas densas, teclado usable, estados de carga claros.
