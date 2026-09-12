/**
 * Origen publico del sitio.
 *
 * Estaba escrito a mano como `https://felixruiz.dev`, un dominio que todavia no
 * existe, asi que `metadataBase` resolvia las URL absolutas de Open Graph contra
 * un host inexistente. Ahora sale del entorno y cae al dominio de Netlify, que
 * es el que esta vivo. El dia que haya dominio propio basta con definir
 * `NEXT_PUBLIC_SITE_URL` en Netlify y volver a desplegar.
 */
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL ?? 'https://portafolio-felix-ruiz.netlify.app'
).replace(/\/+$/, '');

export const SITE_NAME = 'Félix Ruiz M.';
