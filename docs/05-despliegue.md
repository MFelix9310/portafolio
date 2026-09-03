# Despliegue

Tres piezas, tres sitios. Ninguna necesita tarjeta.

| Pieza | Donde | Por que |
|---|---|---|
| Frontend Next.js | **Netlify** | Runtime de Next.js con App Router, ISR y next/image. Sirve las paginas estaticas desde CDN. |
| Backend FastAPI | **Render**, plan gratuito | Netlify no ejecuta Python de forma persistente. Render arranca desde `render.yaml`. |
| Datos, auth y media | **Supabase**, plan gratuito | Ya desplegado: `sqqtaybknkpaofoldcoi`. Esquema aplicado, catalogo cargado, media en Storage, RLS probada 8 de 8. |

El visitante solo toca Netlify y Storage. Render se invoca al revalidar y desde
el panel, asi que que se duerma en el plan gratuito no afecta a nadie que mire
el sitio.

## 1. Frontend en Netlify

1. Netlify, **Add new site**, **Import an existing project**, GitHub.
2. Autoriza la app de Netlify en la cuenta **MFelix9310** y elige `portafolio`.
3. Netlify lee `netlify.toml`: base `web`, `pnpm build`, plugin de Next.js.
   No hay nada que cambiar en la pantalla de build.
4. Antes de desplegar, **Environment variables**, pega estas. Las tres de
   Supabase estan en `backend/.env` y `web/.env.local` de tu maquina.

```
NEXT_PUBLIC_SUPABASE_URL        https://sqqtaybknkpaofoldcoi.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY   la Publishable key
NEXT_PUBLIC_MEDIA_URL           https://sqqtaybknkpaofoldcoi.supabase.co/storage/v1/object/public
NEXT_PUBLIC_REVALIDATE          300
NEXT_PUBLIC_API_URL             URL del backend en Render, paso 2. Hasta entonces, vacio: el sitio cae al seed y funciona igual.
ADMIN_API_URL                   la misma URL del backend en Render
REVALIDATE_SECRET               una cadena larga aleatoria; la misma va en Render como FRONTEND_REVALIDATE_SECRET
```

5. Deploy. El primer build tarda unos minutos. El sitio queda en
   `https://<nombre>.netlify.app`.

`NEXT_PUBLIC_*` se hornea en el build: cambiar una de esas variables exige
volver a desplegar.

## 2. Backend en Render

1. Render, **New**, **Blueprint**, este repositorio. Detecta `render.yaml`.
2. Rellena las variables marcadas sin valor:

```
SUPABASE_URL                https://sqqtaybknkpaofoldcoi.supabase.co
SUPABASE_ANON_KEY           la Publishable key
SUPABASE_SERVICE_ROLE_KEY   la Secret key. Solo aqui, nunca en Netlify.
MEDIA_PUBLIC_BASE_URL       https://sqqtaybknkpaofoldcoi.supabase.co
CORS_ORIGINS                https://<nombre>.netlify.app   (y el dominio propio cuando exista, separados por coma)
FRONTEND_REVALIDATE_URL     https://<nombre>.netlify.app/api/revalidate
FRONTEND_REVALIDATE_SECRET  el mismo REVALIDATE_SECRET de Netlify
```

3. Apply. Cuando `/health` responda, copia la URL del servicio y ponla en
   Netlify como `NEXT_PUBLIC_API_URL` y `ADMIN_API_URL`, y vuelve a desplegar
   el frontend.

## 3. Dominio propio

Cuando lo compres:

1. Netlify, **Domain management**, **Add a domain**. Netlify te da los registros
   DNS. Lo mas simple es apuntar los nameservers del dominio a los de Netlify y
   dejar que gestione el certificado.
2. Anade el dominio a `CORS_ORIGINS` en Render.
3. Listo. El certificado TLS lo emite Netlify solo.

## Comprobar que quedo bien

- `https://<sitio>/civil-bim` muestra 15 proyectos y el cajetin del pie dice
  origen `api`, no `seed local`.
- `https://<sitio>/admin` redirige al login; entrar con tu email y contraseña
  muestra los 23 proyectos.
- Publicar o despublicar algo desde el panel se refleja en el sitio en menos de
  un minuto. Si no, revisa `FRONTEND_REVALIDATE_URL` y el secreto.

## Dos trampas del entorno, ya resueltas en el codigo

- **Claves nuevas de Supabase** (`sb_publishable_`, `sb_secret_`): no son JWT.
  Storage exige la cabecera `apikey` ademas de `Authorization`; el cargador y
  el backend ya la envian.
- **Git Bash en Windows** convierte `/api/v1` en `C:/Program Files/Git/api/v1`
  al exportar variables. No cargues `backend/.env` con `source` antes de
  arrancar el backend: lo lee el solo.
