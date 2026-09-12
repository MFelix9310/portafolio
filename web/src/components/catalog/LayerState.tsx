'use client';

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

interface LayerState {
  /**
   * Capas encendidas. `null` es el estado que sirve el servidor —todas— y por
   * tanto el único que puede estar en el HTML estático: el cliente sólo lo
   * estrecha después de leer la URL.
   */
  active: string[] | null;
  publish: (next: string[] | null) => void;
}

const LayerContext = createContext<LayerState>({ active: null, publish: () => {} });

/**
 * Puente entre el conmutador de capas (cliente, dentro del límite de Suspense
 * porque lee `useSearchParams`) y la rejilla (prerenderizada fuera de ese
 * límite, para que las tarjetas existan en el HTML servido).
 *
 * El proveedor no lee la URL, así que no arrastra a la rejilla al mismo
 * bailout: la página sigue siendo estática con ISR.
 */
export function LayerProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<string[] | null>(null);
  const value = useMemo<LayerState>(() => ({ active, publish: setActive }), [active]);
  return <LayerContext.Provider value={value}>{children}</LayerContext.Provider>;
}

export function useLayers(): LayerState {
  return useContext(LayerContext);
}

export default LayerProvider;
