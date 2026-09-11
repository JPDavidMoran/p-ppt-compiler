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
pptxc compile examples/areas_verdes.json -o deck.pptx
pptxc inspect deck.pptx                          # vuelca transiciones e ids
```

## El modelo: escenas y cámara

Los objetos viven en un **mundo** continuo, no en slides. Una escena es
un estado de ese mundo: dónde está la cámara y qué objetos existen.

```
DSL  ->  Scene IR  ->  differ  ->  Slide Plan  ->  OOXML  ->  .pptx
```

El compilador compara escenas consecutivas y **deriva** la transición:

- Un objeto persistente cuya geometría proyectada cambió -> **Morph**
- Solo entradas y salidas -> **Fade**
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

Un zoom cuenta algo cuando enfoca aquello de lo que vas a hablar, o
cuando vuelve al plano general antes de cambiar de tema:

```json
{ "scene": "modulos" },
{ "mechanism": "FocusTransition", "sequence": ["a", "b", "c"], "scale": 2.2 },
{ "mechanism": "CameraZoom", "target": "tituloModulos", "scale": 1.0 }
```

## Mecanismos

Macros puras que expanden a escenas. No conocen PowerPoint.

| Mecanismo | Qué hace | Eje que ejercita |
|---|---|---|
| `CameraZoom` | Acerca la cámara a un objeto | Cámara móvil, mundo fijo |
| `BeforeAfter` | Sustituye unos objetos por otros | Mundo móvil, cámara fija |
| `FocusTransition` | Encadena focos sobre varios objetos | Composición, N escenas |
| `InfiniteCanvas` | Recorre un lienzo mayor que la pantalla | Panning lateral |

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

## Estado

Compilador funcional con los cuatro mecanismos. El diseño completo está
en [docs/superpowers/specs](docs/superpowers/specs/).

Pendiente: verificación contra un golden file creado en PowerPoint real
para confirmar el criterio exacto de emparejamiento de Morph. El
compilador emite hoy `id` y `name` estables, que son los dos criterios
documentados.

Fuera del alcance actual: generación de DSL por IA, render a imagen y
loop de QA visual.
