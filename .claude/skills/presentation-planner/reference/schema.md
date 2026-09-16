# Schema del DSL

Todos los campos válidos. Cualquier campo no listado aquí hace que el
documento falle: los schemas rechazan lo desconocido en vez de ignorarlo.

Fuente de verdad: `src/pptx_compiler/dsl/schema.py`. Si algo aquí no
concuerda, manda el código.

## Documento

```json
{
  "presentation": { "title": "...", "aspectRatio": "16:9" },
  "world": { "w": 100, "h": 56.25 },
  "scenes": [ ... ],
  "sequence": [ ... ]
}
```

| Campo | Obligatorio | Por defecto |
|---|---|---|
| `presentation.title` | no | `"Untitled"` |
| `presentation.aspectRatio` | no | `"16:9"` (único valor) |
| `presentation.transitionMs` | no | `2000`; mayor que cero |
| `world.w` / `world.h` | no | `100` / `56.25` |
| `scenes` | no | `[]` |
| `sequence` | **sí** | mínimo una entrada |

`transitionMs` es la duración de cada transición en milisegundos. Los
2000 por defecto son el ritmo que aplica PowerPoint, y resultan lentos
para un barrido: entre 700 y 1000 el movimiento se siente ágil sin
atropellarse. Afecta a toda la presentación por igual.

## Coordenadas

El mundo mide 100 × 56.25 unidades por defecto: la proporción de 16:9.
Un objeto en `{x: 0, y: 0, w: 100, h: 56.25}` llena la pantalla.

Márgenes cómodos: empezar en `x: 12` y terminar en `x: 88`.

Un objeto puede salirse del mundo (`x: 150`) — es válido y es lo que
permite las entradas desde fuera del marco y los lienzos amplios.

## Escena

```json
{
  "id": "modulos",
  "camera": { "x": 0, "y": 0, "w": 100, "h": 56.25 },
  "objects": [ ... ]
}
```

`camera` es opcional; por defecto encuadra el mundo entero. Casi siempre
se omite: los mecanismos mueven la cámara por ti.

## Objeto

```json
{
  "id": "titulo",
  "type": "text",
  "content": "Gestión de áreas verdes",
  "at": { "x": 12, "y": 9, "w": 76, "h": 8 },
  "style": { "fontSize": 30, "bold": true, "align": "center" }
}
```

| Campo | Valores | Notas |
|---|---|---|
| `id` | texto | Identidad entre escenas: el mismo id morphea |
| `type` | `text`, `shape`, `image` | |
| `at` | `x`, `y`, `w`, `h` | `w` y `h` mayores que cero |
| `content` | texto | Admite `\n` |
| `source` | ruta | **Obligatorio** para `image`; el archivo debe existir |
| `style` | ver abajo | |

### style

| Campo | Por defecto | Valores |
|---|---|---|
| `fontSize` | `18` | mayor que cero; es el tamaño a cámara completa |
| `color` | `"202020"` | hex **sin** `#` |
| `fill` | ninguno | hex; sin relleno si se omite |
| `line` | ninguno | hex; sin borde si se omite |
| `lineWidth` | ninguno | grosor del borde en puntos (`line_width`) |
| `spin` | ninguno | giro continuo: `{seconds, clockwise}` |
| `bold` | `false` | |
| `opacity` | `1.0` | de `0.0` a `1.0`; solo afecta al relleno |
| `opacity` | `1.0` | entre 0 y 1 |
| `rotation` | `0` | grados, de -360 a 360 |
| `sectorStart` | `0` | grados; solo para `pie` y `blockArc` |
| `sectorEnd` | `90` | grados; mayor que `sectorStart` |
| `align` | `"left"` | `left`, `center`, `right` |
| `shape` | `"rect"` | `rect`, `ellipse`, `roundRect`, `pie`, `blockArc`, `star4`, `star5`, `star6`, `star8` |

`fontSize` escala con el zoom: 30 pt en una cámara 2× se ve como 60 pt.

`rotation` gira el objeto sobre su centro. Un mismo id con dos ángulos
distintos morphea, así que una rueda que cambia de sector es un solo
objeto girando. `pie` dibuja un sector de círculo y `blockArc` un anillo. Ambos ocupan su
caja `at` completa, y `sectorStart`/`sectorEnd` delimitan qué porción se
dibuja: `0` a `90` es un cuarto, `0` a `180` una mitad. Sin declararlos,
PowerPoint usa su sector por defecto —de 0 a 162 grados—, que no es ni un
cuarto ni una mitad y deja al descubierto una porción impredecible de lo
que haya debajo.

En el DSL se escriben en camelCase (`sectorStart`, `sectorEnd`); dentro
del compilador son `sector_start` y `sector_end`.

Las estrellas (`star4` es un shuriken de cuatro puntas) sirven de textura de fondo: contorno fino con `line` y `lineWidth`, y sin `fill`.

`spin` las hace girar **sin parar** mientras la diapositiva está a la vista, al margen de las transiciones:

```json
"style": { "shape": "star4", "line": "2E5C7A", "lineWidth": 1,
           "spin": { "seconds": 6, "clockwise": false } }
```

`seconds` es lo que tarda una vuelta completa. Duraciones distintas en cada figura evitan que el patrón se mueva como un bloque. Es la única animación dentro de una diapositiva; todo lo demás ocurre en las transiciones.

### Imágenes

```json
{ "id": "foto", "type": "image", "source": "examples/assets/parque.png",
  "at": { "x": 52, "y": 0, "w": 48, "h": 56.25 } }
```

La ruta es relativa al directorio desde el que se compila. El compilador
empaqueta el archivo dentro del `.pptx`, así que el resultado es
autónomo. Una imagen morphea como cualquier otro objeto: reutiliza su id
entre escenas.

**Calcula la caja a partir del hueco libre** (R12): margen de 6 unidades,
la zona que dejan los textos, y la imagen encajada ahí conservando su
proporción. Una imagen pequeña en una diapositiva medio vacía se lee como
un icono perdido.

El `at` no respeta la proporción original: si no coincide, la imagen se
deforma. Calcula `w` y `h` con la proporción real del archivo.

## Secuencia

Cada entrada es una referencia a escena o una llamada a mecanismo.

```json
{ "scene": "modulos" }
{ "mechanism": "CameraZoom", "target": "dash", "scale": 2.5 }
```

Repetir `{"scene": "x"}` es válido y es la forma de volver al plano
general tras un recorrido.

### Escenas silenciosas

```json
{ "scene": "modulos", "emit": false }
```

`emit` es `true` por defecto. Con `false` la escena carga su estado pero
no produce diapositiva: queda disponible como punto de partida de un
mecanismo sin que el espectador vea antes lo que ese mecanismo va a ir
revelando.

Es lo que necesitan `Build`, `Reveal` y `BeforeAfter`, cuya escena fuente
contiene el estado final. Sin `emit: false`, `Build` enseña todos los
puntos antes de construirlos de uno en uno.

Una secuencia de solo escenas silenciosas falla: no produce ninguna
diapositiva.

## Mecanismos

Solo existen estos ocho.

### CameraZoom

```json
{ "mechanism": "CameraZoom", "target": "dash", "scale": 2.5 }
```

| Parámetro | Obligatorio | Por defecto |
|---|---|---|
| `target` | **sí** | id de un objeto de la escena actual |
| `scale` | no | `2.0`; mayor acerca más |

Emite **una** escena. Siempre encuadra `target`: no sirve para alejarse.

### BeforeAfter

```json
{ "mechanism": "BeforeAfter", "before": ["viejo"], "after": ["nuevo"], "keep": ["titulo"] }
```

Emite **dos** escenas con la misma cámara. Todos los ids deben existir en
la escena actual.

Para que el cambio morphee en vez de parpadear, prefiere un solo objeto
que cambie de estado (mismo id en dos escenas) a este mecanismo.

### FocusTransition

```json
{ "mechanism": "FocusTransition", "sequence": ["modA", "modB"], "scale": 2.0 }
```

Emite **una escena por elemento**. `sequence` necesita al menos uno.
Cierra siempre repitiendo la escena del plano general después.

### InfiniteCanvas

```json
{
  "mechanism": "InfiniteCanvas",
  "objects": [ { "id": "zonaA", "type": "shape", "at": { "x": 120, "y": 10, "w": 30, "h": 20 } } ],
  "tour": [ { "at": "zonaA", "scale": 1.5 } ]
}
```

Añade sus `objects` a la escena actual y emite **una escena por parada**.
Cada `tour[].at` referencia el id de un objeto. `scale` por defecto `1.5`.

Declara una escena propia antes de usarlo, o arrastrará los objetos del
tema anterior.

### Build

```json
{ "mechanism": "Build", "sequence": ["punto1", "punto2", "punto3"] }
```

Revela los objetos **uno a uno**. Emite una escena por elemento. Los
objetos que no aparecen en `sequence` permanecen visibles todo el tiempo:
son el contexto sobre el que se construye.

El recurso más común de una presentación. Úsalo para listas, pasos de un
proceso o argumentos que se acumulan.

### Regroup

```json
{ "mechanism": "Regroup", "targets": ["a", "b", "c"], "layout": "grid", "gap": 3 }
```

| Parámetro | Obligatorio | Por defecto |
|---|---|---|
| `targets` | **sí** | objetos a reorganizar |
| `layout` | no | `"row"`; también `"column"` y `"grid"` |
| `area` | no | el encuadre con márgenes |
| `gap` | no | `3.0` |

Emite **una** escena: los mismos objetos en otra disposición. Como
conservan su id, cada uno viaja a su nueva posición y se lee como un
movimiento. Los objetos fuera de `targets` no se tocan.

### Spotlight

```json
{ "mechanism": "Spotlight", "target": "modB", "dim": 0.25, "keep": ["titulo"] }
```

| Parámetro | Obligatorio | Por defecto |
|---|---|---|
| `target` | **sí** | objeto a destacar |
| `dim` | no | `0.25`; opacidad del resto |
| `keep` | no | objetos que no se atenúan |

Destaca sin mover la cámara: el conjunto sigue a la vista y solo cambia
el peso visual. Pon el título en `keep` para que no se atenúe con el
contenido.

Alternativa a `CameraZoom` cuando el contexto importa tanto como el
detalle.

### Reveal

```json
{ "mechanism": "Reveal", "cover": "tapa", "target": "secreto", "direction": "up" }
```

| Parámetro | Obligatorio | Por defecto |
|---|---|---|
| `cover` | **sí** | objeto que tapa |
| `target` | **sí** | objeto que queda al descubierto |
| `direction` | no | `"up"`; también `down`, `left`, `right` |

Emite **dos** escenas. La tapa se desplaza fuera del encuadre
conservando su id, así que Morph la aparta en lugar de desvanecerla.

Coloca `cover` sobre `target` con la misma geometría, y declara `cover`
**después** en la lista de objetos para que quede encima.

## Comandos

```bash
pptxc validate deck.json   # estructura
pptxc lint deck.json       # composición: debe salir limpio
pptxc compile deck.json -o deck.pptx
pptxc inspect deck.pptx    # transiciones e ids del resultado
```
