import { ImageResponse } from 'next/og';

/**
 * Imagen de previsualizacion al compartir el enlace.
 *
 * Se genera en el build en vez de subir un PNG, para que el titular no pueda
 * divergir del copy. Reproduce la lamina: papel vegetal, reticula de filetes,
 * la frase de posicionamiento con la segunda mitad en rojo revision, y el
 * cajetin de la esquina.
 */
export const alt = 'Félix Ruiz M. · Ingeniero que automatiza, de obra a datos';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const PAPEL = '#F0EEE7';
const TINTA = '#0F1216';
const ROJO = '#B02914';
const FILETE = 'rgba(15,18,22,0.10)';

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          background: PAPEL,
          padding: '64px 72px',
          position: 'relative',
        }}
      >
        {/* Reticula dibujada, como en el sitio. */}
        {[1, 2, 3, 4, 5].map((n) => (
          <div
            key={n}
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${(n * 100) / 6}%`,
              width: 1,
              background: FILETE,
            }}
          />
        ))}

        <div
          style={{
            display: 'flex',
            fontSize: 22,
            letterSpacing: 4,
            color: 'rgba(15,18,22,0.55)',
            textTransform: 'uppercase',
          }}
        >
          Portafolio · Félix Ruiz M.
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', fontSize: 78, fontWeight: 700, color: TINTA, lineHeight: 1.05 }}>
            Ingeniero que automatiza
          </div>
          <div style={{ display: 'flex', fontSize: 78, fontWeight: 700, color: ROJO, lineHeight: 1.05 }}>
            de obra a datos
          </div>
          <div style={{ display: 'flex', fontSize: 30, color: 'rgba(15,18,22,0.62)', marginTop: 18 }}>
            Un plano sin cotas es una ilustración. Con cotas es un dato.
          </div>
        </div>

        {/* Cajetin, abajo a la derecha. */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            fontSize: 20,
            letterSpacing: 3,
            color: 'rgba(15,18,22,0.55)',
            textTransform: 'uppercase',
            borderTop: `1px solid ${FILETE}`,
            paddingTop: 18,
          }}
        >
          <div style={{ display: 'flex' }}>Datos · Desarrollo · Civil &amp; BIM</div>
          <div style={{ display: 'flex' }}>Escala 1:1</div>
        </div>
      </div>
    ),
    size,
  );
}
