# PowerPoint Design Compiler

Compila un DSL declarativo de presentaciones a `.pptx` con transiciones
Morph reales, controlando OOXML directamente.

La idea central: **la IA no escribe PPTX ni XML, escribe DSL**. El
compilador se encarga de duplicar slides, mantener identificadores
compatibles y generar el XML que PowerPoint necesita.

## Instalación

```bash
pip install -e .
```

## Uso

```bash
pptxc validate examples/areas_verdes.json        # valida y lista escenas
pptxc lint examples/areas_verdes.json            # revisa la composición
pptxc compile examples/areas_verdes.json -o deck.pptx
pptxc inspect deck.pptx                          # vuelca transiciones e ids
```

`validate` comprueba que el DSL es correcto; **`lint` comprueba que
narra bien**: avisa si la presentación termina en un primer plano, si un
antes/después va a parpadear o si dos títulos se sustituyen en el sitio.
Las reglas están en [docs/design-rules.md](docs/design-rules.md).

## El modelo: escenas y cámara

Los objetos viven en un **mundo** continuo, no en slides. Una escena es
un estado de ese mundo: dónde está la cámara y qué objetos existen.

```
DSL  ->  Scene IR  ->  differ  ->  Slide Plan  ->  OOXML  ->  .pptx
```

El compilador compara escenas consecutivas y **deriva** la transición:

- Un objeto persistente que cambió de posición, estilo o texto -> **Morph**
- Objetos que entran o salen con otros que permanecen -> **Morph**
- Cambio de tema completo, sin objetos en común -> **Fade**
- Nada cambió -> sin transición

Un objeto que no se mueve en el mundo sí cambia en la slide si la cámara
se movió. **El zoom cinematográfico sale de la geometría**, no de un
efecto especial.

## Ejemplo mínimo

```json
{
  "scenes": [
    {
      "id": "intro",
      "objects": [
        {
          "id": "dash",
          "type": "shape",
          "at": { "x": 60, "y": 32, "w": 25, "h": 18 },
          "style": { "fill": "2D6A4F" }
        }
      ]
    }
  ],
  "sequence": [
    { "scene": "intro" },
    { "mechanism": "CameraZoom", "target": "dash", "scale": 2.5 }
  ]
}
```

Dos slides; la segunda morphea acercándose al objeto.

## Cada escena es una diapositiva

Un mecanismo **no anima dentro de una diapositiva**: emite diapositivas
nuevas. `CameraZoom` produce una diapositiva acercada, y el espectador
avanza hasta ella con un clic, igual que con cualquier otra.

Eso significa que un zoom debe llevar a alguna parte. Esta secuencia
deja al espectador encallado en un primer plano del título:

```json
{ "scene": "portada" },
{ "mechanism": "CameraZoom", "target": "titulo", "scale": 1.8 },
{ "scene": "otroTema" }
```

### Para volver al plano general, repite la escena

`CameraZoom` **siempre encuadra su objetivo**, así que no sirve para
alejarse: `scale: 1.0` sobre el título deja la cámara sobre el título,
no en la vista completa. Para cerrar un recorrido se repite la escena
original, y el differ morphea de vuelta al ver el cambio de cámara:

```json
{ "scene": "modulos" },
{ "mechanism": "FocusTransition", "sequence": ["a", "b", "c"], "scale": 1.9 },
{ "scene": "modulos" }
```

### Para un antes/después, reutiliza el id

Dos objetos distintos solo pueden desvanecerse uno y aparecer el otro.
**Un mismo id en dos escenas morphea**: el bloque crece, se desplaza y
cambia de texto de forma continua.

```json
{ "id": "estado", "content": "Antes\nRegistros en papel",
  "at": { "x": 30, "y": 24, "w": 40, "h": 18 } }

{ "id": "estado", "content": "Después\nTrazabilidad en tiempo real",
  "at": { "x": 22, "y": 20, "w": 56, "h": 24 } }
```

Cuidado con el efecto contrario: dos objetos **distintos** que ocupan la
misma posición en escenas consecutivas (dos títulos de temas diferentes,
por ejemplo) se sustituyen en el sitio y parecen "cambiar de texto". Si
no quieres eso, separa los temas con una escena que no comparta
geometría.

## Mecanismos

Macros puras que expanden a escenas. No conocen PowerPoint.

| Mecanismo | Qué hace | Eje que ejercita |
|---|---|---|
| `CameraZoom` | Acerca la cámara a un objeto | Cámara móvil, mundo fijo |
| `BeforeAfter` | Sustituye unos objetos por otros | Mundo móvil, cámara fija |
| `FocusTransition` | Encadena focos sobre varios objetos | Composición, N escenas |
| `InfiniteCanvas` | Recorre un lienzo mayor que la pantalla | Panning lateral |
| `Build` | Revela los objetos uno a uno | Construcción progresiva |
| `Regroup` | Cambia la disposición de los mismos objetos | Reorganización |
| `Spotlight` | Destaca atenuando el resto | Énfasis sin mover la cámara |
| `Reveal` | Aparta una tapa y descubre lo de debajo | Descubrimiento |

Añadir un mecanismo es añadir una carpeta en `mechanisms/`. El
compilador no se modifica.

## Identidad de objetos

Es el punto crítico. Un objeto con el mismo `id` en varias escenas
recibe **el mismo identificador OOXML en todas las slides**. Sin esa
estabilidad PowerPoint no empareja nada y degrada a un fade genérico,
en silencio y sin error.

Comprobable con `pptxc inspect`: el `id` de un objeto persistente debe
repetirse entre slides consecutivas unidas por Morph.

## Arquitectura

| Capa | Responsabilidad | Pureza |
|---|---|---|
| `dsl/` | Schemas Pydantic, carga | Puro |
| `mechanisms/` | Macros: parámetros -> escenas | Puro |
| `ir/` | Scene, Camera, identidad | Puro |
| `compiler/` | Differ, expansor | Puro |
| `render/` | Proyección, python-pptx, OOXML | I/O |
| `cli/` | Línea de comandos | I/O |

Las capas puras no importan `pptx` ni tocan disco, así que se testean
sin generar un solo archivo.

## Tests

```bash
python -m pytest
```

## Escribir presentaciones con Claude Code

El repositorio incluye una skill en
[.claude/skills/presentation-planner](.claude/skills/presentation-planner/)
que escribe el DSL por ti: propone conceptos, compone las escenas y
verifica el resultado con `lint` antes de compilar.

Pídeselo a Claude Code en este repositorio:

> Hazme una presentación de 8 diapositivas sobre nuestro sistema de riego
> para una reunión con el municipio.

La skill no puede inventar mecanismos ni saltarse el lint; las reglas que
sigue son las de [docs/design-rules.md](docs/design-rules.md), y unos
tests comprueban que sigue describiendo el compilador real.

## Estado

Compilador funcional con los cuatro mecanismos, verificado contra un
golden file generado por PowerPoint real. El diseño completo está en
[docs/superpowers/specs](docs/superpowers/specs/).

La skill de `.claude/skills/` escribe el DSL dentro de Claude Code.

Pendiente: temas y estilos reutilizables, duración y opciones de Morph
configurables por escena, y un loop de QA visual que renderice las
diapositivas y las evalúe con un modelo de visión.
