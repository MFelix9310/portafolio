# Supabase — portafolio Félix

Esquema, RLS y semilla. **Todo lo de esta carpeta es local y no se ha aplicado a
ninguna base de datos.** No se usa el stack local de Supabase porque requiere
Docker (D7). Las migraciones se validan sin servidor y se aplicarán el día que tú
crees tu proyecto en la nube y corras `link` + `db push` — pasos que ejecutas tú.

```
supabase/
  config.toml                 generado por `supabase init`
  validate_sql.py             valida la sintaxis de las migraciones, sin servidor
  rls_smoke_test.py           prueba las políticas RLS contra tu instancia real
  migrations/                 esquema versionado, se aplica en orden alfabético
  seed/load_seed.py           carga content/catalog.seed.json (fuente de verdad)
```

No hay `seed.sql`: duplicar el catálogo en SQL a mano es exactamente el fallo que
se está evitando. `[db.seed]` está desactivado en `config.toml` a propósito.

## Validar las migraciones (sin Docker, sin servidor)

```bash
pip install pglast sqlglot
python supabase/validate_sql.py
```

`pglast` usa **libpg_query**, el parser real de Postgres: si un fichero pasa, el
servidor lo aceptará sintácticamente. `sqlglot` va como segunda opinión, pero su
cobertura de DDL es parcial y degrada `create policy` / `grant` / `do $$...$$` a
comandos opacos; el script cuenta cuántas sentencias quedan así para no dar por
validado lo que no lo está.

Esto comprueba **sintaxis, no comportamiento**. Una política RLS mal pensada
parsea perfectamente. Por eso está la lista de abajo.

## Ver qué haría la semilla

El cargador **no escribe nada por defecto**: monta el plan completo en memoria,
sin tocar la red, y lo imprime. No necesita dependencias — solo la librería
estándar.

```bash
python supabase/seed/load_seed.py
```

Ahí ya se comprueba lo que puede fallar en frío: que cada ruta de media del
catálogo esté en `content/media-manifest.json` (si falta una, aborta en vez de
insertar un `NULL`), que todo texto visible traiga la clave `es` obligatoria
(D5), y que los ficheros locales de `tools/media/out/` existan.

## Cuando crees tu proyecto en la nube — **lo ejecutas tú**

Nada de lo de abajo lo ha hecho ni lo hará este repo por su cuenta.

1. Crea el proyecto en <https://supabase.com/dashboard> y guarda la contraseña de
   la base de datos.

2. Enlaza el repo con ese proyecto (te pedirá la contraseña):

   ```bash
   supabase link --project-ref <TU_PROJECT_REF>
   ```

3. Revisa qué se va a aplicar **antes** de aplicarlo:

   ```bash
   supabase migration list           # qué migraciones faltan allí
   ```

4. Aplica el esquema:

   ```bash
   supabase db push
   ```

   Si falla en `20260828120700_storage_media.sql` por permisos sobre
   `storage.objects`, crea el bucket `media` (público) desde el dashboard y pega
   las cuatro políticas de ese fichero en el SQL Editor. Es el único trozo que
   algunos proyectos no dejan aplicar por migración.

5. Crea tu usuario en Authentication → Users y date de alta como admin. La tabla
   `admin_users` nace vacía, así que **nadie puede escribir hasta que exista esa
   primera fila**, y no puedes insertarla tú mismo desde el panel (aún no eres
   admin). Hazlo en el SQL Editor del dashboard:

   ```sql
   insert into public.admin_users (user_id, note)
   select id, 'Félix' from auth.users where email = 'TU_EMAIL'
   on conflict (user_id) do nothing;
   ```

6. Carga el contenido y sube los ficheros ya optimizados de `tools/media/out/`:

   ```bash
   export SUPABASE_URL="https://<REF>.supabase.co"
   export SUPABASE_SERVICE_ROLE_KEY="<service_role key del dashboard>"

   python supabase/seed/load_seed.py                    # plan, sin escribir
   python supabase/seed/load_seed.py --apply            # datos
   python supabase/seed/load_seed.py --apply --upload   # datos + ~30 MiB a Storage
   ```

   En PowerShell, `$env:SUPABASE_URL = "..."`.

   Es idempotente: *upsert* por `legacy_id` (o por `slug` / `(kind, value)` donde
   no hay `legacy_id`), y la subida omite los objetos que ya están en Storage con
   el mismo tamaño. Se puede repetir tantas veces como haga falta.

   La `service_role` key **nunca** va al navegador: se usa desde esta línea de
   comandos y para nada más.

7. **Comprueba que RLS se comporta como dice el contrato.** Este paso no es
   opcional: las migraciones están validadas sintácticamente, no probadas, y una
   política mal pensada parsea perfectamente.

   ```bash
   export SUPABASE_URL="https://<REF>.supabase.co"
   export SUPABASE_ANON_KEY="<anon key>"
   export SUPABASE_ADMIN_EMAIL="tu@email"
   export SUPABASE_ADMIN_PASSWORD="..."
   # opcional, para la comprobación 7:
   export SUPABASE_TEST_EMAIL="prueba@email"
   export SUPABASE_TEST_PASSWORD="..."

   python supabase/rls_smoke_test.py
   ```

## Prueba de humo de RLS

`supabase/rls_smoke_test.py` comprueba contra tu instancia real, con la **anon
key**, las ocho cosas que tienen que ser ciertas:

1. `anon` no ve borradores (y sí ve lo publicado, como control).
2. `anon` no ve los medios ni las subáreas de un proyecto en borrador.
3. `anon` no puede insertar, actualizar ni borrar.
4. `anon` sí puede insertar en `messages`.
5. `anon` no puede leer `messages`.
6. El admin sí ve los borradores.
7. Un usuario autenticado que no está en `admin_users` tampoco escribe.
8. `areas` y `subareas` respetan `status`, y una subárea hereda el del área.

Se monta sus propios datos temporales (un proyecto borrador, uno publicado, un
área y una subárea de prueba, todos con prefijo `zz-smoke-`), los usa y los borra
en un `finally`. **No toca tu contenido real**: los intentos de escritura de
`anon` van siempre contra las filas temporales.

La comprobación 3 no se fía del código HTTP: después de intentar el `insert`, el
`update` y el `delete`, vuelve a leer como admin y falla si algo cambió de verdad.
Un 200 sin efecto pasa, pero con aviso para que revises los grants.

Imprime un resumen `8/8 OK` y sale con código distinto de cero si algo falla
(código 2 si es un problema de configuración, no de políticas). La comprobación 7
se omite si no defines el usuario de prueba, y el resumen lo dice.

Vuelve a ejecutarlo cada vez que toques una política.

## Notas sobre el esquema

- **RLS en todas las tablas.** La migración de RLS termina con una comprobación
  que hace fallar el `db push` si alguna tabla de `public` se queda sin RLS o sin
  políticas; no depende de que alguien lo revise.
- **El admin ve los borradores.** Cada tabla de contenido tiene dos políticas de
  `select`: la pública, que filtra `status = 'published'`, y la del admin, que no
  filtra. Las políticas *permissive* se combinan con OR, así que el panel ve todo.
- **`project_media` y `project_subareas` heredan la visibilidad del proyecto.** No
  tienen `status` propio; su política pública exige que el proyecto padre esté
  publicado, para que un borrador no filtre sus medios.
- **`messages`** no tiene política de `select` para `anon`, ni el privilegio. El
  formulario inserta y no puede marcar su propio mensaje como leído.
- **Privilegios además de RLS.** `anon` solo tiene `select` sobre contenido e
  `insert` sobre `messages`. Aunque una política se escribiera mal, `anon` no
  tiene `update` ni `delete` en ninguna tabla.
- **Taxonomía fija en migración.** `areas` y `subareas` se siembran en
  `20260828120200_taxonomia.sql` porque `/data`, `/developer` y `/civil-bim` deben
  renderizar aunque tengan cero proyectos. `civil-bim` nace vacía a propósito.
- **`areas` y `subareas` tienen `status`** (`20260829090000_taxonomia_status.sql`),
  con `default 'published'` para que el sitio no nazca sin navegación. Así se puede
  retirar un chip del panel sin borrar la fila y perder sus vínculos en
  `project_subareas`. Una subárea publicada cuya área está en borrador **no se ve**:
  sería un chip huérfano apuntando a una sección que ya no existe.
