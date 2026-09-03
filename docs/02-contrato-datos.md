# Contrato de datos y API

Contrato compartido entre el esquema Postgres, el backend hexagonal, el panel de
administración y el frontend. **Nadie lo cambia unilateralmente.**

## Convenciones

- Todo texto visible es `jsonb` con forma `{"es": "...", "en": "..."}`. `es` es
  obligatorio; `en` es opcional y el consumidor cae a `es` si falta (D5).
- Toda entidad publicable tiene `status text not null default 'draft'` con
  `check (status in ('draft','published'))` y `display_order int not null default 0`.
- Toda tabla lleva `id uuid primary key default gen_random_uuid()`,
  `created_at timestamptz not null default now()`, `updated_at timestamptz not null default now()`
  (trigger `set_updated_at`).
- Los slugs son `text not null unique`, minúsculas ASCII con guiones.

## Taxonomía

```
areas       key: 'data' | 'developer' | 'civil-bim'
subareas    key único dentro del área; pertenece a un area_id
```

Semilla fija (el panel puede añadir, no hace falta migrar para crecer):

| área | subáreas |
|---|---|
| `data` | `analyst`, `scientist`, `engineer` |
| `developer` | `fullstack`, `backend` |
| `civil-bim` | `structural`, `bim`, `automation` |

`civil-bim` nace **sin proyectos**: Félix los carga desde `/admin`. Las tres rutas
deben renderizar correctamente con cero resultados (empty state real, no un hueco).

## Tablas

```
profile              singleton: name, headline jsonb, bio jsonb, photo_path, professional_photo_path
areas                key, name jsonb, blurb jsonb, display_order
subareas             area_id fk, key, name jsonb, display_order   unique(area_id, key)

projects             slug, title jsonb, summary jsonb, body jsonb,
                     technologies text[], project_url, repository_url,
                     thumbnail_path, legacy_id int, status, display_order
project_subareas     project_id fk, subarea_id fk   pk(project_id, subarea_id)
project_media        project_id fk, kind ('image'|'video'|'document'),
                     storage_path, poster_path, caption jsonb, title jsonb,
                     duration_seconds numeric, width int, height int,
                     renditions jsonb, display_order

experiences          slug, company jsonb, position jsonb, description jsonb,
                     keywords text[], company_logo_path, thumbnail_path,
                     start_date date, end_date date null, is_current bool, status, display_order
certifications       slug, name jsonb, issuer jsonb, description jsonb,
                     issued_on date, expires_on date null, credential_url,
                     certificate_path, status, display_order
education            institution jsonb, title jsonb, description jsonb,
                     graduation_year int, status, display_order
publications         slug, kind, title jsonb, authors jsonb, venue jsonb, abstract jsonb,
                     published_on date, doi, isbn, url, pdf_path, thumbnail_path,
                     status, display_order
contacts             kind, value, status, display_order
messages             name, email, subject, body, read bool default false, created_at
```

`project_media.renditions` guarda la salida de `tools/media`:
`{"1080": {"path": "...", "bytes": 3980000}, "720": {...}}`.

## RLS — el contrato de seguridad

Se activa RLS en **todas** las tablas. Sin excepción; una tabla sin política es
una tabla abierta.

1. **Lectura pública**: rol `anon` puede `select` **solo** filas con
   `status = 'published'`. Aplica a todas las tablas de contenido.
2. **Escritura del propietario**: `insert/update/delete` solo para
   `auth.uid() = (select id from admin_users)`. Se usa una tabla `admin_users`
   con la única fila de Félix en vez de comparar contra un email hardcodeado, para
   que rotar la cuenta no requiera una migración.
3. **`messages`**: `anon` puede `insert` (formulario de contacto) pero **no**
   `select`. Solo el admin lee.
4. **Storage**: bucket `media` público en lectura; escritura y borrado solo para
   el admin autenticado.

El `service_role` key **no se usa nunca desde el navegador**. Solo el backend
FastAPI lo tiene, y solo para operaciones que ya pasaron por un caso de uso.

## API HTTP (adaptador de entrada)

Prefijo `/api/v1`. Público sin auth, admin con `Authorization: Bearer <JWT de Supabase>`.

```
GET    /health
GET    /catalog                      ?area=&subarea=&locale=   → catálogo completo filtrado
GET    /projects                     ?area=&subarea=&status=
GET    /projects/{slug}
GET    /areas                                                   → áreas + subáreas + conteos
GET    /experiences
GET    /certifications
GET    /education
GET    /publications
GET    /profile
GET    /contacts
POST   /messages                                                → formulario de contacto

# admin — requieren JWT válido de Supabase
GET    /admin/{recurso}              incluye borradores
POST   /admin/{recurso}
PATCH  /admin/{recurso}/{id}
DELETE /admin/{recurso}/{id}
POST   /admin/{recurso}/reorder      body: {"ids": [...]}  → reordena en bloque
POST   /admin/media/upload-url       body: {"filename","content_type"} → URL firmada de subida
POST   /admin/revalidate             dispara la revalidación ISR del front
```

`recurso` ∈ `projects | experiences | certifications | education | publications | contacts | areas | subareas | profile | media`.

**Regla dura**: los endpoints `/admin` invocan los mismos casos de uso de
`src/application/use_cases` que los públicos. No hay una ruta que escriba a la
base saltándose el dominio.

## Puertos del dominio

```python
ProjectRepository        get_by_slug, list(filter: ProjectFilter), save, delete, reorder
ExperienceRepository     list, get, save, delete, reorder
CertificationRepository  list, get, save, delete, reorder
EducationRepository      list, get, save, delete, reorder
PublicationRepository    list, get, save, delete, reorder
ProfileRepository        get, save
ContactRepository        list, save, delete, reorder
MessageRepository        save, list
TaxonomyRepository       list_areas, list_subareas, save_area, save_subarea, delete
MediaStoragePort         create_upload_url, public_url, delete
ClockPort                now
```

Todos ABC puros en `src/domain/repositories/` (y `MediaStoragePort`/`ClockPort` en
`src/application/ports/`, porque son salidas de aplicación, no del dominio).

---

## Addendum — desviaciones aceptadas (revisión del esquema)

Al implementar el esquema aparecieron puntos donde este contrato estaba mal o
incompleto. Manda lo que dice este addendum.

### A1 — `is_admin()` en vez de la comparación literal

El contrato escribía la regla de escritura como
`auth.uid() = (select id from admin_users)`. Es incorrecto: ese subselect revienta
en cuanto hay más de una fila, y confunde el `id` propio de la tabla con el uuid
del usuario.

Forma correcta: `admin_users` tiene `id` propio y `user_id` FK a `auth.users`, y
la comprobación es una función `is_admin()` con
`exists (select 1 from admin_users where user_id = auth.uid())`.

`is_admin()` es `security definer` con `search_path = ''` y nombres cualificados:
así su lectura interna no vuelve a pasar por RLS (evita la recursión con la
política de `admin_users`) y un `search_path` hostil no puede resolver
`admin_users` a otra tabla.

### A2 — El admin necesita su propia política de lectura

Cada tabla de contenido lleva **dos** políticas de `select`: la pública
(`status = 'published'`) y una de admin (`is_admin()`, sin filtro). Las políticas
permissive se combinan con OR, así que el filtro público no puede ocultarle los
borradores al panel.

Este es el fallo clásico de RLS y la razón de que exista la lista de comprobación
manual del `supabase/README.md`.

### A3 — `legacy_id` en cinco tablas, no en una

`education` no tiene slug, así que sin `legacy_id` no hay clave estable para que
el seed sea idempotente. `legacy_id int unique` va en `projects`, `experiences`,
`certifications`, `education` y `publications`.

### A4 — Convención de rutas de media (vinculante para el backend)

`content/media-manifest.json` da `storagePath` **con el prefijo del bucket
incluido**: `media/projects/videos/1-1080.mp4`.

- En la base se guarda **verbatim**, con el prefijo.
- Para hablar con la API de Storage se quita el primer segmento (`media/`), que
  es el nombre del bucket.
- La URL pública se compone `{SUPABASE_URL}/storage/v1/object/public/{storagePath}`.

Aplica a `thumbnail_path`, `poster_path`, `company_logo_path`,
`certificate_path`, `pdf_path`, `photo_path`, `professional_photo_path` y
`project_media.storage_path`.

### A5 — Claves de unicidad que faltaban

`contacts unique (kind, value)` y `project_media unique (project_id, storage_path)`.
Sin ellas no hay upsert idempotente.

### A6 — `profile` y defensa en profundidad

`profile` lleva `status` (para que la regla de lectura pública sea uniforme) pero
no `display_order`, que no significa nada en un singleton. El singleton se fuerza
con `singleton boolean not null default true unique check (singleton)`.

Además de RLS hay `revoke all` a `anon`/`authenticated` y grants explícitos:
`anon` solo tiene `select` sobre contenido e `insert` sobre `messages`. Aunque una
política se escribiera mal, `anon` carece del privilegio de `update`/`delete`.

### A7 — `projects.body` no se toca al recargar el seed

`body` existe en el esquema pero no en el export. El cargador **omite la columna**
en su payload, de modo que recargar la semilla no pisa lo que Félix haya escrito
desde `/admin`.

### A8 — `technologies_en` / `keywords_en` no tienen destino

`technologies` y `keywords` son `text[]` sin localizar. Se comprobó que las
variantes EN del sitio antiguo son **idénticas** a las ES en los 6 proyectos y en
la única experiencia, así que no se pierde nada. Si algún día divergen, habrá que
localizarlas.

### A9 — Puertos que faltaban en el contrato

El cuerpo del documento lista `recurso ∈ ... | media` en `/admin` pero no define
`MediaRepository`, y expone `POST /admin/revalidate` sin puerto. Sin ellos, el
CRUD de media escribiría a la base saltándose el dominio. Ambos existen:

- `domain/repositories/media_repository.py`
- `application/ports/revalidation.py` → `FrontendRevalidationPort`

Si no hay `FRONTEND_REVALIDATE_URL` configurada, la revalidación responde
`accepted: false` en vez de fallar: que el front no responda no puede tumbar una
publicación.

### A10 — Las áreas son fijas, las subáreas crecen

Las tres áreas son la arquitectura de información: `/data`, `/developer` y
`/civil-bim` son rutas del App Router. Crear un área desde el panel produciría un
área sin ruta que la renderice.

- `POST /admin/areas` y `DELETE /admin/areas/{id}` → rechazados con mensaje explícito.
- `PATCH /admin/areas/{id}` → permitido (nombre, descripción, orden, `status`).
- `subareas` → CRUD completo.

### A11 — `get` por id y por slug son dos accesos distintos

El contrato decía `get` sin especificar. Son dos: `GetProject` por slug (ruta
pública) y `GetProjectById` por id (panel, porque `PATCH /admin/{recurso}/{id}`
va por id). Confundirlos produjo un bug real que los tests atraparon.

### A12 — Unicidad impuesta también en la aplicación

`project_media (project_id, storage_path)` y `contacts (kind, value)` se validan
en el caso de uso, no solo en el esquema. Si solo estuvieran en Postgres, el
adaptador JSON aceptaría duplicados que el de Supabase rechaza — y la
equivalencia entre adaptadores dejaría de ser cierta justo donde nadie mira.

### A13 — Taxonomia ampliada tras recuperar el contenido real

El seed inicial salio de `db.sqlite3` del repo de GitHub, que estaba
desactualizado: 6 proyectos y 1 experiencia. El despliegue en produccion tiene
**23 proyectos y 3 experiencias**, y entre ellos hay bastante ingenieria civil
aplicada y bastante ingenieria de datos. Las areas `civil-bim` y la subarea
`data/engineer` dejan de estar vacias.

Semilla de subareas revisada:

| area | subareas |
|---|---|
| `data` | `analyst`, `scientist`, `engineer` |
| `developer` | `fullstack`, `backend`, `desktop` |
| `civil-bim` | `structural`, `geotechnical`, `bim`, `construction` |

`developer/desktop` es nueva porque hay varias aplicaciones de escritorio reales
en PyQt6 y PySide6, y llamarlas backend seria inexacto.

`civil-bim` se abre en cuatro porque el contenido lo pide: calculo estructural,
geotecnia con ensayos CPT, modelo BIM y automatizacion, y planificacion de obra.

El resto del contrato no cambia. Un proyecto sigue pudiendo pertenecer a varias
areas, que es justo lo que necesitan los gemelos digitales sismicos y los
predictores de resistencia: son civil y son data a la vez.
