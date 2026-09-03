# content/copy

Copy estático del sitio, separado del catálogo dinámico (`catalog.seed.json`).
Un archivo por idioma con la **misma estructura de claves**: `copy.es.json`
(fuente) y `copy.en.json` (traducción profesional, no calco). Claves en inglés
snake_case; valores en el idioma del archivo.

## Esquema

```
meta                    language, positioning (frase fija de posicionamiento)
nav                     home, about, projects, contact, areas.{data,developer,civil_bim}
home                    headline, subtitle, intro, cta_view_projects,
                        area_cards.{data,developer,civil_bim}.{title,description}
areas                   data.intro
                        developer.intro
                        civil_bim.intro, civil_bim.empty_state.{title,body}
about                   heading, paragraphs[] (2-3 párrafos)
contact                 heading, support_text,
                        form.labels.{name,email,subject,message}
                        form.{submit,submitting,success}
                        form.errors.{name_required,email_required,email_invalid,
                                     subject_required,message_required,
                                     message_too_short,generic_error}
                        channels.{linkedin,github,instagram}
projects                mapa slug → { summary }. Las claves son los `slug` de
                        `catalog.seed.json`; no se traduce el slug.
microcopy               areas.{data,developer,civil_bim}          (nombres cortos)
                        subareas.{data,developer,civil_bim}.*      (etiquetas de chips)
                        buttons.*                                  (textos de botón)
                        empty_states.*                             (estados vacíos genéricos)
                        footer.{tagline,copyright}
chrome                  vocabulario de interfaz de la lámina: skip_to_content, eyebrow,
                        thesis, measure, menu, language_label, theme, areas_index,
                        layers, metrics, sheet, video, project, about,
                        contact_channels, contact_form_offline, civil_bim, not_found
```

## Reglas

- `chrome.*` es el vocabulario de la interfaz (cotas, capas, cajetín, lámina).
  Vive aquí para que el front no tenga un segundo diccionario propio.
- `chrome.civil_bim.placeholder_3d` es el texto que usaba el héroe de `/civil-bim`
  antes de tener la extrusión 3D implementada. `extrusion_plan` (nota bajo el
  dibujo cuando se queda en 2D), `extrusion_scene` (nota cuando el 3D está
  activo) y `extrusion_alt` (`aria-label` del SVG accesible) lo sustituyen;
  `placeholder_3d` se retira cuando el componente deje de leerlo como fallback.
- `civil_bim.empty_state` es el único empty state "narrativo"; el resto de
  áreas no lo necesitan porque siempre tienen proyectos publicados.
- `projects.*.summary` reescribe el tono del resumen legado
  (`catalog.seed.json → projects[].summary`) sin añadir tecnologías, cifras,
  fechas o alcance que no estén en el seed.
- `footer.copyright` usa el placeholder `{year}` — se resuelve en runtime, no
  es un dato del catálogo.
