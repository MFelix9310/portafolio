# Dirección de arte — "Cota"

## La idea única

Una **cota** es la línea con flechas que en un plano dice cuánto mide algo. Es el
gesto que convierte un dibujo en información: sin cotas un plano es una ilustración,
con cotas es un dato.

Ese es el puente exacto entre las dos mitades de Félix. El sitio no *habla* de la
transición de obra a datos: **está dibujado como un plano y anotado como un dataset**.
Un plano estructural y una tabla de datos son la misma cosa —una retícula con
anotaciones— y el sitio lo hace literal.

Todo lo demás (tipografía, color, retícula, movimiento) se deriva de aquí. Si un
elemento no se explica por esta idea, no entra.

## Retícula: dibujada, no invisible

El grid de Bootstrap es una convención invisible de 12 columnas. Aquí la retícula
**se ve**: filetes de 1 px al 8 % de opacidad, con las columnas rotuladas en el
margen (`A B C D`) y las bandas horizontales numeradas (`01 02 03`), como el marco
de un plano de construcción.

- 12 columnas, medianil 24 px, márgenes rotulados de 48 px en escritorio.
- El contenido se apoya en la retícula y ocasionalmente **la rompe** — un título
  que invade el margen es intencional, igual que una acotación que sale del dibujo.
- Esquinas vivas. Sin `rounded-lg`. Donde haría falta suavizar, se usan **marcas de
  esquina** (dos filetes en ángulo) en vez de un radio: es la marca de recorte de
  una lámina, no una tarjeta de Material Design.

## Tipografía

| Rol | Fuente | Por qué |
|---|---|---|
| Display | **Archivo** (variable, eje Expanded) | Grotesca con eje de anchura real. En caps y tracking negativo da el peso de un cajetín de plano sin caer en Oswald/Bebas, que están quemadas. |
| Texto | **Instrument Sans** | Humanista, alta legibilidad en párrafo largo, y **no es Inter** — Inter, Geist, Manrope y Plus Jakarta son las cuatro defaults de los builders de IA. |
| Anotación | **JetBrains Mono** | Todo lo que es *dato* va en monoespaciada: fechas, tecnologías, contadores, tamaños, coordenadas. Es la letra de la acotación. |

La regla dura: **prosa en sans, dato en mono**. Esa separación tipográfica es la que
hace legible el discurso "de obra a datos" sin decirlo con palabras.

## Color

Derivado de la cianotipia y del lápiz de revisión, no de una paleta "segura".

| Token | Hex | Uso |
|---|---|---|
| `paper` | `#F0EEE7` | Fondo. Blanco cálido de papel vegetal, no `#FFFFFF`. |
| `ink` | `#0F1216` | Texto y filetes principales. |
| `prussian` | `#12315C` | Azul de cianotipo. Estructura, profundidad, superficies invertidas. |
| `revision` | `#D8341F` | **Acento.** Rojo de lápiz de revisión. |
| `graphite-100…600` | escala neutra | Filetes de retícula, texto secundario. |

El acento **rojo revisión** se usa exactamente como se usa un lápiz rojo sobre un
plano: para marcar, corregir y señalar — nunca como relleno decorativo. Si el rojo
cubre más del 5 % de una pantalla, está mal usado.

Esto responde de forma deliberada al naranja plano del sitio anterior: no se
reutiliza ni se "calienta", se sustituye por un color con procedencia y con reglas
de uso.

Modo oscuro = **cianotipo invertido**: fondo `prussian` profundo, filetes en blanco.
No es un tema oscuro genérico, es el negativo del mismo plano.

## Movimiento con función narrativa

Cuatro gestos, todos con GSAP + ScrollTrigger sobre scroll suavizado con Lenis.
Ninguno es decorativo:

1. **Acotación que mide.** Al entrar una sección, una línea de cota se extiende de
   extremo a extremo y su número **cuenta hasta el valor real** (`6 proyectos`,
   `3.5 años`). El movimiento *es* el dato apareciendo.
2. **Capas CAD.** Los chips de subárea no son filtros de e-commerce: se comportan
   como el conmutador de capas de un CAD. Al apagar una capa, los proyectos que
   salen se atenúan a filete antes de desaparecer, igual que una capa oculta.
3. **Llamada de detalle.** Abrir un proyecto no es un modal que hace fade: una marca
   de sección se dibuja sobre la tarjeta y el detalle crece desde ella, como el
   despiece ampliado de un plano.
4. **Extrusión (`/civil-bim`).** El héroe empieza siendo una planta en 2D —líneas
   puras— y con el scroll **se extruye** a un pórtico 3D. Es la tesis del portafolio
   en un solo gesto: el mismo dato, leído como dibujo o como modelo.

## Disciplina de rendimiento

- El bloque de React Three Fiber se carga con `next/dynamic` (`ssr: false`) y solo
  cuando su contenedor entra en viewport. No entra en el bundle inicial.
- Se anima **solo** `transform` y `opacity`. Nada que dispare layout.
- `prefers-reduced-motion` desactiva ScrollTrigger y Lenis y deja los estados finales.
- El 3D degrada a la planta 2D estática en móviles de gama baja y sin WebGL.
- Vídeo con `preload="none"` y póster; se descarga cuando el usuario lo pide.
