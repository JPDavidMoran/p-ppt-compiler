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
| `world.w` / `world.h` | no | `100` / `56.25` |
| `scenes` | no | `[]` |
| `sequence` | **sí** | mínimo una entrada |

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
| `bold` | `false` | |
| `align` | `"left"` | `left`, `center`, `right` |
| `shape` | `"rect"` | `rect`, `ellipse`, `roundRect` |

`fontSize` escala con el zoom: 30 pt en una cámara 2× se ve como 60 pt.

### Imágenes

```json
{ "id": "foto", "type": "image", "source": "examples/assets/parque.png",
  "at": { "x": 52, "y": 0, "w": 48, "h": 56.25 } }
```

La ruta es relativa al directorio desde el que se compila. El compilador
empaqueta el archivo dentro del `.pptx`, así que el resultado es
autónomo. Una imagen morphea como cualquier otro objeto: reutiliza su id
entre escenas.

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

## Mecanismos

Solo existen estos cuatro.

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

## Comandos

```bash
pptxc validate deck.json   # estructura
pptxc lint deck.json       # composición: debe salir limpio
pptxc compile deck.json -o deck.pptx
pptxc inspect deck.pptx    # transiciones e ids del resultado
```
