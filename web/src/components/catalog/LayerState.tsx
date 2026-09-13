'use client';

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

interface LayerState {
  /**
   * Capas encendidas. `null` es el estado que sirve el servidor —todas— y por
   * tanto el único que puede estar en el HTML estático: el cliente sólo lo
   * estrecha después de leer la URL.
   */
  active: string[] | null;
  /**
   * Si este cambio se anima. La selección que trae la URL al cargar se aplica
   * seca: animar la salida de media rejilla recién pintada sería un parpadeo, no
   * un gesto. Los clics posteriores sí animan.
   */
  animate: boolean;
  publish: (next: string[] | null, animate: boolean) => void;
}

const LayerContext = createContext<LayerState>({
  active: null,
  animate: false,
  publish: () => {},
});

/**
 * Puente entre el conmutador de capas (cliente, dentro del límite de Suspense
 * porque lee `useSearchParams`) y la rejilla (prerenderizada fuera de ese
 * límite, para que las tarjetas existan en el HTML servido).
 *
 * El proveedor no lee la URL, así que no arrastra a la rejilla al mismo
 * bailout: la página sigue siendo estática con ISR.
 */
const same = (a: string[] | null, b: string[] | null) =>
  a === b || (a !== null && b !== null && a.length === b.length && a.join('|') === b.join('|'));

export function LayerProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{ active: string[] | null; animate: boolean }>({
    active: null,
    animate: false,
  });

  // `publish` tiene que ser estable: el conmutador la llama desde un efecto que
  // la lleva en las dependencias, y una identidad nueva en cada render sería un
  // bucle. Publicar lo mismo tampoco crea estado nuevo, por la misma razón.
  const publish = useCallback((next: string[] | null, animate: boolean) => {
    setState((previous) =>
      same(previous.active, next) && previous.animate === animate
        ? previous
        : { active: next, animate },
    );
  }, []);

  const value = useMemo<LayerState>(
    () => ({ active: state.active, animate: state.animate, publish }),
    [state, publish],
  );

  return <LayerContext.Provider value={value}>{children}</LayerContext.Provider>;
}

export function useLayers(): LayerState {
  return useContext(LayerContext);
}

export default LayerProvider;
