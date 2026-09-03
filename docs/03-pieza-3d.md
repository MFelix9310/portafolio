# Pieza 3D — la extrusión de `/civil-bim`

Especificación del gesto 4 de la dirección de arte. Es la única pieza 3D del
sitio; todo lo demás es 2D deliberadamente.

## Qué tiene que decir

La tesis del portafolio en un solo movimiento: **el mismo dato, leído como dibujo
o como modelo**. El héroe empieza siendo una planta estructural en 2D —líneas
puras, como un plano— y con el scroll se **extruye** a un pórtico tridimensional.

No es una decoración 3D. Si se le quita el scroll y queda un objeto girando, está
mal hecho.

## Comportamiento

1. **Estado inicial (scroll 0)**: planta en 2D vista cenital. Ejes de replanteo
   rotulados (A/B/C, 1/2/3), cotas visibles, líneas en `ink` sobre `paper`. Es
   indistinguible de un plano dibujado.
2. **Transición (scroll 0 → 1)**: la cámara orbita de cenital a isométrica
   mientras los elementos ganan altura. Columnas y vigas se extruyen desde su
   trazado en planta. Las cotas de la planta permanecen, proyectadas sobre el
   suelo, como referencia — es lo que ata las dos lecturas.
3. **Estado final (scroll 1)**: pórtico isométrico completo, con una rotación
   lenta y contenida en reposo. Sin autoplay agresivo.

El progreso lo controla ScrollTrigger sobre el contenedor del héroe, no un
`requestAnimationFrame` libre: el usuario conduce la animación.

## Geometría

Pórtico paramétrico generado en código, sin cargar ningún `.glb`. Motivos: pesa
cero, es coherente con "ingeniero que automatiza" (el modelo *se calcula*, no se
descarga) y evita depender de un asset binario que nadie puede versionar bien.

Parámetros: número de vanos, número de plantas, luz, altura de entrepiso.
Por defecto: 3 vanos × 3 plantas. Elementos como cajas delgadas o líneas gruesas
— **wireframe estructural**, no arquitectura renderizada. Sin materiales PBR, sin
sombras suaves, sin environment map. El acabado es de plano, no de render.

## Rendimiento — condiciones de aceptación

- `next/dynamic` con `ssr: false`, montado solo cuando el contenedor entra en
  viewport (`IntersectionObserver`). Fuera del bundle inicial.
- `frameloop="demand"`: solo se renderiza cuando el scroll o la rotación en
  reposo lo piden. Un canvas R3F a 60 fps constantes en una página estática es
  batería quemada por nada.
- `dpr={[1, 1.75]}` con tope; nada de `devicePixelRatio` sin límite.
- Degradación explícita a un **SVG estático de la planta 2D** cuando: no hay
  WebGL, `prefers-reduced-motion` está activo, el dispositivo declara poca
  memoria/núcleos, el usuario pidió ahorro de datos, **o el viewport mide menos
  de 768 px de ancho**. El SVG no es un error, es el estado inicial de la pieza
  — así que la degradación sigue contando la mitad de la historia.
- Presupuesto: el chunk de la pieza (R3F + three + drei mínimo) por debajo de
  180 KB gzip, y no debe entrar en la ruta crítica de LCP de `/civil-bim`.

### El corte por ancho: 768 px (2026-08-31)

La condición de ancho se añadió después de medir. El dato que la motiva:

| | `/data` | `/civil-bim` |
|---|---|---|
| Tarjetas de proyecto | 19 | 15 |
| JavaScript transferido | 190 kB | **319 kB** |
| TBT (móvil) | 113 ms | **243 ms** |
| Rendimiento (móvil) | 92 | **86** |

`/civil-bim` tenía **menos** tarjetas que `/data` y aun así el doble de TBT y seis
puntos menos. Los **129 kB** de diferencia son exactamente los chunks de esta
pieza. La hidratación de las tarjetas no era la causa: si lo fuera, `/data`
—que tiene cuatro más— habría puntuado peor.

El motivo del corte no es sólo el coste. En un móvil de 812 px de alto la pieza
cae a unos 70 px del pliegue, dentro del `rootMargin` de 300 px del observador,
así que `three` se descargaba y montaba a la vez que hidrataba la rejilla. Y a
375 px de ancho una extrusión conducida por scroll de un pórtico de 3 vanos × 3
plantas **no se lee**: el pórtico sale apretado y el gesto se pierde. La planta
2D es ese mismo dibujo en su estado inicial y en un teléfono se lee mejor.

Escritorio y tablet conservan la pieza entera. El gesto 4 no se ha recortado:
se ha aplicado la regla de degradación que ya estaba escrita
(`docs/01-direccion-de-arte.md`, disciplina de rendimiento).

**Dónde se comprueba, y por qué ahí.** En `canRender3d()`, dentro de
`ExtrusionPlaceholder`. Tiene que ser antes de que nada arme la pieza:
`ExtrusionScene` sólo se renderiza cuando `armed` es cierto, y `armed` sólo se
enciende si `canRender3d()` dio el visto bueno. Comprobarlo más tarde —al
montar la escena, o dentro del propio `ExtrusionScene`— no serviría de nada: el
chunk de `three` ya estaría pedido y el coste ya estaría pagado. Verificado en
el navegador a 375 px: `data-mode="plan"`, cero `<canvas>`, y ni rastro de los
chunks de 74 kB y 50 kB en la pestaña de red, ni siquiera como `prefetch`.

Lo que se probó y **no** funcionó, por si alguien lo vuelve a intentar: armar la
pieza en `requestIdleCallback` en vez de al intersectar. Empeoró (86 → 84, TBT
243 → 348). Mover el trabajo más tarde alarga la ventana de tareas largas en vez
de acortarla.

## Accesibilidad

El canvas es decorativo respecto al contenido: `aria-hidden`, con el mensaje real
del héroe en texto adyacente. Nada de información que solo exista dentro del 3D.
