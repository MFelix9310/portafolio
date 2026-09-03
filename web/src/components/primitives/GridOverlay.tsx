/**
 * La retícula del plano, dibujada en vez de implícita.
 *
 * 12 columnas con filetes al 8 %, rotuladas A…L en el margen superior, y bandas
 * horizontales numeradas 01…04 en el margen izquierdo. En móvil sólo se dibuja
 * una de cada tres: doce filetes en 375 px son ruido, no estructura.
 * Es decoración estructural, así que va `aria-hidden`.
 */

const COLUMNS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
const BANDS = ['01', '02', '03', '04'];

export function GridOverlay() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 select-none overflow-hidden"
    >
      {BANDS.map((band, index) => (
        <div
          key={band}
          className="absolute left-0 w-full"
          // Las bandas arrancan al 20 %: al 0 % quedarían tapadas por el cajetín superior.
          style={{ top: `${((index + 1) * 100) / (BANDS.length + 1)}%` }}
        >
          <span className="block h-px w-full bg-rule" style={{ opacity: 'var(--grid-alpha)' }} />
          <span className="absolute left-1.5 top-1 font-mono text-[9px] tracking-[0.2em] text-content/25">
            {band}
          </span>
        </div>
      ))}

      <div className="lamina h-full">
        <div className="reticula h-full">
          {COLUMNS.map((column, index) => (
            <div
              key={column}
              className={`relative h-full ${index % 3 === 0 ? '' : 'opacity-0 md:opacity-100'}`}
            >
              <span
                className="absolute left-0 top-0 h-full w-px bg-rule"
                style={{ opacity: 'var(--grid-alpha)' }}
              />
              {/* Los rótulos van por debajo del cajetín superior (56 px de alto). */}
              <span className="absolute left-1 top-16 font-mono text-[9px] tracking-[0.2em] text-content/25">
                {column}
              </span>
              {index === COLUMNS.length - 1 ? (
                <span
                  className="absolute right-0 top-0 h-full w-px bg-rule"
                  style={{ opacity: 'var(--grid-alpha)' }}
                />
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default GridOverlay;
