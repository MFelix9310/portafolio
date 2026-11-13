import type { Project, ProjectMedia } from './types';

/** Subárea de Civil BIM que reúne los proyectos realizados con juego de planos. */
export const COMPLETED_SUBAREA = 'completed';

/**
 * Una lámina es un documento que es imagen: el plano entero a alta resolución.
 * El PDF del juego también es un documento, pero se descarga, no se pinta.
 */
export function isSheet(media: ProjectMedia): boolean {
  return media.kind === 'document' && /\.(webp|png|jpe?g)$/i.test(media.src);
}

export function isCompleted(project: Project): boolean {
  return project.tags.some((tag) => tag.area === 'civil-bim' && tag.subarea === COMPLETED_SUBAREA);
}
