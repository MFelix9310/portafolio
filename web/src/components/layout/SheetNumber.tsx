'use client';

import { usePathname } from 'next/navigation';

/** Número de lámina de la página actual, como en el cajetín de un plano. */
const SHEETS: [RegExp, string][] = [
  [/^\/(en\/)?data$/, 'A-01'],
  [/^\/(en\/)?developer$/, 'B-01'],
  [/^\/(en\/)?civil-bim$/, 'C-01'],
  [/^\/(en\/)?(proyectos|projects)\//, 'D-##'],
  [/^\/(en\/)?(sobre-mi|about)$/, 'E-01'],
  [/^\/(en\/)?(contacto|contact)$/, 'F-01'],
];

export function SheetNumber() {
  const pathname = usePathname() ?? '/';
  const match = SHEETS.find(([pattern]) => pattern.test(pathname));
  return <>{match ? match[1] : '00-00'}</>;
}

export default SheetNumber;
