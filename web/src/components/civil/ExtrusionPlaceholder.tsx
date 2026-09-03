'use client';

import dynamic from 'next/dynamic';
import { useCallback, useEffect, useRef, useState } from 'react';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';

import type { FrameParams } from './frame-model';
import PlanSvg from './PlanSvg';

/**
 * ===========================================================================
 * GESTO 4 — EXTRUSIÓN DE LA PLANTA A PÓRTICO 3D (/civil-bim)
 * ===========================================================================
 * Este archivo es sólo la **carcasa**. Decide si la pieza puede ser 3D, la monta
 * cuando el contenedor se acerca al viewport y, si no puede, se queda en la
 * planta 2D. Ni `three` ni R3F se importan aquí: viven detrás del `dynamic()`
 * de abajo, en su propio chunk.
 *
 * Cadena de carga: `ExtrusionSlot` (dynamic, ssr:false) → esta carcasa →
 * `IntersectionObserver` → `ExtrusionScene` (dynamic, ssr:false) → three.
 * El 3D no entra en el bundle inicial ni en la ruta crítica de LCP.
 *
 * El nombre del archivo se conserva porque `ExtrusionSlot` importa esta ruta y
 * ese contrato es de otro agente.
 * ===========================================================================
 */

const ExtrusionScene = dynamic(() => import('./ExtrusionScene'), { ssr: false });

interface ExtrusionPlaceholderProps {
  locale: Locale;
  /** El pórtico es paramétrico; por defecto 3 vanos × 3 plantas. */
  params?: Partial<FrameParams>;
}

type LowEndNavigator = Navigator & {
  deviceMemory?: number;
  connection?: { saveData?: boolean };
};

/** Mismo corte que `md:` de Tailwind, que es el que usa la nota de esta pieza. */
const ANCHO_MINIMO_3D = '(min-width: 768px)';

/**
 * Degradación explícita. No es un caso de error: la planta 2D es el estado
 * inicial de la pieza, así que quedarse en ella sigue contando media historia.
 *
 * Se degrada si hay `prefers-reduced-motion`, si no hay WebGL, si el dispositivo
 * declara menos de 4 núcleos o menos de 4 GB, si el usuario pidió ahorro de
 * datos, **o si el viewport mide menos de 768 px de ancho**.
 *
 * El corte por ancho no es un recorte para contentar a una métrica: la
 * dirección de arte ya manda degradar a la planta 2D en móvil de gama baja
 * (`docs/01-direccion-de-arte.md`), y el gesto es una extrusión conducida por
 * scroll de un pórtico de 3 vanos × 3 plantas — a 375 px eso no se lee. La
 * planta 2D es ese mismo dibujo en su estado inicial y en un teléfono se lee
 * mejor. Lo que cuesta el 3D ahí está medido: 129 kB de JS y el TBT de
 * `/civil-bim` al doble que el de `/data`, que tiene más tarjetas.
 *
 * Se comprueba **aquí**, antes de que nada arme la pieza: `ExtrusionScene` sólo
 * se renderiza con `armed`, y `armed` sólo se enciende si esta función dice que
 * sí. Si dijera que no más tarde, el chunk de `three` ya estaría pedido.
 */
function canRender3d(): boolean {
  if (typeof window === 'undefined') return false;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
  if (!window.matchMedia(ANCHO_MINIMO_3D).matches) return false;

  const nav = navigator as LowEndNavigator;
  if (nav.connection?.saveData) return false;
  const cores = nav.hardwareConcurrency;
  if (typeof cores === 'number' && cores > 0 && cores < 4) return false;
  const memory = nav.deviceMemory;
  if (typeof memory === 'number' && memory > 0 && memory < 4) return false;

  try {
    const probe = document.createElement('canvas');
    const gl = probe.getContext('webgl2') ?? probe.getContext('webgl');
    if (!gl) return false;
    // Se libera el contexto de sondeo: los navegadores limitan cuántos hay vivos.
    (gl.getExtension('WEBGL_lose_context') as { loseContext(): void } | null)?.loseContext();
    return true;
  } catch {
    return false;
  }
}

export function ExtrusionPlaceholder({ locale, params }: ExtrusionPlaceholderProps) {
  const host = useRef<HTMLDivElement>(null);
  const [armed, setArmed] = useState(false);
  const [ready, setReady] = useState(false);

  // El copy vive en `content/copy/*.json`. `extrusion_alt` describe el dibujo,
  // no la tecnología: es la representación accesible de la pieza, porque el
  // canvas va `aria-hidden`.
  const strings = copy(locale).chrome.civil_bim;
  const alt = strings.extrusion_alt;
  const note = armed ? strings.extrusion_scene : strings.extrusion_plan;

  useEffect(() => {
    const el = host.current;
    if (!el || !canRender3d()) return;

    // Se monta sólo cuando el contenedor se acerca al viewport; el margen da
    // tiempo a descargar el chunk antes de que la pieza se vea.
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries[0]?.isIntersecting) return;
        observer.disconnect();
        setArmed(true);
      },
      { rootMargin: '300px 0px' },
    );
    observer.observe(el);

    // Si el usuario activa «reducir movimiento» con la pieza ya montada, se
    // vuelve a la planta: la degradación no es sólo una decisión de arranque.
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => {
      if (!media.matches) return;
      setArmed(false);
      setReady(false);
    };
    media.addEventListener('change', onChange);

    return () => {
      observer.disconnect();
      media.removeEventListener('change', onChange);
    };
  }, []);

  const onReady = useCallback(() => setReady(true), []);
  // Contexto WebGL perdido o imposible de crear: se vuelve a la planta 2D, que
  // es un estado válido de la pieza y no una pantalla de error.
  const onFail = useCallback(() => {
    setReady(false);
    setArmed(false);
  }, []);

  return (
    <div
      ref={host}
      data-gesture="4"
      data-mode={armed ? 'scene' : 'plan'}
      className="relative w-full border filete bg-surface-sunken"
    >
      <CornerTicks size={12} />
      <div className="relative">
        {/* La planta se queda montada: es el estado inicial, el estado degradado
            y la representación accesible de la pieza. Nada existe sólo en 3D. */}
        <PlanSvg
          label={alt}
          className={`transition-opacity duration-700 ease-cota ${ready ? 'opacity-0' : 'opacity-100'}`}
        />
        {armed ? (
          // Fundido cruzado con la planta: hasta que la escena pinta su primer
          // frame se ve sólo el SVG, nunca los dos dibujos superpuestos.
          <div
            aria-hidden="true"
            className={`absolute inset-0 transition-opacity duration-700 ease-cota ${ready ? 'opacity-100' : 'opacity-0'}`}
          >
            <ExtrusionScene
              triggerRef={host}
              params={params}
              onReady={onReady}
              onFail={onFail}
            />
          </div>
        ) : null}
      </div>
      {/* En móvil la nota va debajo del dibujo; superpuesta sólo cabe en pantalla ancha. */}
      <Annotation
        className="block border-t filete px-3 py-2 !normal-case md:absolute md:bottom-3 md:left-3 md:max-w-[70%] md:border-0 md:py-0"
        accent
      >
        {note}
      </Annotation>
    </div>
  );
}

export default ExtrusionPlaceholder;
