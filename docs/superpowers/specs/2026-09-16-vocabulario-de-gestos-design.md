# Vocabulario de gestos — Fase 1 del catálogo de mecanismos

Fecha: 2026-09-16
Estado: aprobado para implementación
Depende de: [2026-09-11-pptx-design-compiler-design.md](2026-09-11-pptx-design-compiler-design.md)

## 1. Propósito

Completar el vocabulario de **gestos** del compilador: los mecanismos
que transforman objetos y cámara de una escena. Es la primera de dos
fases; la segunda añade una capa de **composiciones** que ensambla estos
gestos en narraciones completas.

El orden importa. Una composición que necesite un gesto inexistente lo
reimplementaría por dentro, y el vocabulario quedaría disperso entre
capas. Primero los gestos, después quien los combina.

## 2. Contexto: qué hay y qué falta

El compilador tiene ocho mecanismos. El spec original documenta cuatro
(`CameraZoom`, `BeforeAfter`, `FocusTransition`, `InfiniteCanvas`); los
otros cuatro (`Build`, `Regroup`, `Spotlight`, `Reveal`) se añadieron
después y no están especificados. Este documento no los especifica
retroactivamente, pero sí los cuenta como parte del vocabulario
existente.

Mapa de ejes cubiertos hoy:

| Eje | Mecanismos |
|---|---|
| Cámara móvil, mundo fijo | `CameraZoom`, `FocusTransition`, `InfiniteCanvas` |
| Mundo móvil, cámara fija | `BeforeAfter`, `Regroup`, `Reveal` |
| Aparición / dosificación | `Build` |
| Peso visual sin movimiento | `Spotlight` |

Huecos que esta fase cierra:

- **La cámara sólo sabe acercarse.** `Camera.framing` siempre encuadra
  su objetivo. La regla R2 de `docs/design-rules.md` documenta la
  consecuencia como limitación: para volver al plano general hay que
  repetir la escena.
- **No hay jerarquía por escala.** Ningún mecanismo cambia el tamaño de
  un objeto para expresar importancia.
- **No hay profundidad.** Nada expresa capas apiladas.
- **El desbordamiento deliberado se escribe a mano.** Un objeto mayor
  que el encuadre, del que sólo asoma un fragmento, exige calcular
  coordenadas negativas en el DSL.

Fuera de esta fase, por dependencias de render (grupo bloqueado):
`ObjectEntrance` y `FullScreenImageReveal` necesitan z-order explícito y
recorte de imagen, que el IR no tiene.

Fuera de esta fase, por ser composiciones (fase 2):
`TimelineProgression`, `SplitScreen`, `DataStory`, `UIWalkthrough`.

## 3. Decisiones de diseño

| Decisión | Elección | Razón |
|---|---|---|
| Gestos antes que composiciones | Dos fases | Una composición no debe inventar gestos que le falten |
| Dónde vive el cálculo de geometría | Módulo `ir/layout.py` puro y compartido | `Regroup` ya calcula rejillas; con más consumidores, la fórmula debe vivir en un sitio |
| Geometría imposible | `LayoutError`, fail fast | Un ancho negativo no significa nada; recortar en silencio esconde el problema |
| Objeto mayor que el encuadre | Válido, nunca error | Desbordar es una técnica de diseño, no un defecto |
| Aviso temprano | Regla de lint para el gap imposible | El error de compilación es la red de seguridad, no la experiencia normal |

### Por qué el layout sale a su propio módulo

`Regroup` calcula hoy filas, columnas, cuadrículas, gap y un área por
defecto derivada de la cámara, todo en funciones privadas
(`_layout`, `_columns`, `_area`). Tres de los cinco mecanismos nuevos
necesitan la misma aritmética, y las composiciones de la fase 2 la
necesitarán entera.

Con el layout extraído, `Regroup` lo consume igual que
`FocusTransition` consume `CameraZoom`: reutilizando, no duplicando.

### Por qué un ancho negativo falla y un objeto gigante no

Son geometrías distintas, y confundirlas produciría un linter que
regaña por hacer buen diseño.

Un gap imposible es **imposibilidad aritmética**. Seis objetos en fila
con `gap: 16` dentro de un área de 76 de ancho: los cinco separadores
suman 80, más que el área disponible antes de colocar un solo objeto.
`cell_w` sale −0,67. No existe un layout válido que el módulo podría
haber encontrado.

Un objeto de `w: 240` en un mundo de 100 es **perfectamente válido**:
positivo, coherente, y se proyecta a un rectángulo del que se ve un
fragmento. `render/projection.py` ya lo contempla explícitamente («el
resultado puede caer fuera del área visible; eso es deliberado») y
`EmuRect` documenta lo mismo.

Regla resultante: layout falla sólo con dimensiones **no positivas**.
Nunca por «esto es más grande que el área».

### Por qué el gap imposible también es aviso de lint

El fallo debe ser raro, no la forma habitual de descubrir que te
pasaste. El caso real: seis tarjetas quedan apretadas (10,17 de ancho),
el autor sube el gap para darles aire, y no hace la cuenta de que con
seis objetos el gap se multiplica por cinco. El número 16 no parece
grande en un mundo de 100.

La asimetría lo agrava: el área por defecto es 76 × 31,5, así que el
mismo gap que sobra en `row` rompe en `column`. Cinco objetos en columna
con `gap: 12` dan `cell_h` = −3,3.

Por eso el mensaje de error trae **el gap máximo posible**, no sólo la
constatación de que no cabe: la diferencia entre «está mal» y «pon
15.2». Y una regla de lint lo detecta antes de compilar, junto al resto
de los avisos de composición.

## 4. El módulo de layout

`ir/layout.py`. Junto a `geometry.py`, con su mismo nivel de pureza: no
conoce escenas, ni cámara, ni objetos. Recibe un área y un número,
devuelve rectángulos.

```python
def row(area: Rect, count: int, gap: float) -> list[Rect]
def column(area: Rect, count: int, gap: float) -> list[Rect]
def grid(area: Rect, count: int, columns: int, gap: float) -> list[Rect]
def bounding(rects: Iterable[Rect]) -> Rect
def inset(area: Rect, fraction_x: float, fraction_y: float) -> Rect
def clamp(rect: Rect, bounds: Rect) -> Rect
```

`bounding` hace posible `CameraFrame`: el encuadre de varios objetos es
la caja que los contiene. `clamp` recorta esa caja al mundo, para que un
objeto oversize no fuerce un alejamiento absurdo. `inset` reemplaza el
cálculo privado de área por defecto de `Regroup`.

Error nuevo en `errors.py`:

```python
class LayoutError(PresentationCompilerError):
    """No existe un layout válido para los parámetros dados."""
```

Lleva el contexto que permite corregir: número de objetos, dimensión del
área, gap recibido y gap máximo posible.

### Migración de Regroup

Sus funciones privadas `_layout`, `_columns` y `_area` desaparecen;
`expand` llama a `layout.row/column/grid` y a `layout.inset`. El
comportamiento no cambia: los tests existentes de `Regroup` deben seguir
verdes **sin tocarlos**, y eso es la prueba de que la extracción fue
fiel.

## 5. Los cinco mecanismos

Cada uno es una carpeta en `mechanisms/` con `__init__.py` (expand) y
`schema.py` (parámetros Pydantic con `extra="forbid"`), registrada en
`mechanisms/__init__.py`. Ninguno toca el render ni el IR de objetos.

### CameraFrame

Encuadra un conjunto de objetos. Permite alejarse.

```json
{ "mechanism": "CameraFrame", "targets": ["riego", "poda", "mapas"], "scale": 1.0 }
```

| Parámetro | Tipo | Defecto | Significado |
|---|---|---|---|
| `targets` | `list[str]`, min 1 | — | Objetos a encuadrar |
| `scale` | `float > 0` | 1.0 | Mayor acerca |
| `clampToWorld` | `bool` | `true` | Recorta el encuadre al mundo |

Emite una escena. Calcula `layout.bounding` de las geometrías de los
objetivos, opcionalmente `layout.clamp` al mundo, y reencuadra con
`Camera.framing`. Con un solo objetivo equivale a `CameraZoom`; con
varios es el plano de conjunto que no existía.

`clampToWorld` por defecto en `true` porque un objetivo oversize daría
un bounding box enorme y alejaría la cámara hasta perder la
composición — lo contrario de lo que se pide al encuadrar.

Efecto sobre las reglas: R2 pasa de limitación a recomendación. Para
volver al plano general ya no hace falta repetir la escena.

Ejercita: cámara móvil sobre conjuntos, alejamiento.

### Oversize

Un objeto pasa a ser mucho mayor que el encuadre y se ancla a un borde;
sólo asoma un fragmento.

```json
{ "mechanism": "Oversize", "target": "titulo", "scale": 2.6, "anchor": "left" }
```

| Parámetro | Tipo | Defecto | Significado |
|---|---|---|---|
| `target` | `str` | — | Objeto a agrandar |
| `scale` | `float > 1` | 2.0 | Tamaño respecto al encuadre |
| `anchor` | `left\|right\|top\|bottom\|center` | `center` | Borde al que se ancla |

Emite una escena con el objetivo redimensionado y reposicionado; los
demás objetos no se tocan. Calcula las coordenadas —negativas cuando el
anclaje lo exige— que hoy el autor escribiría a mano.

El objetivo conserva su id, así que el differ pide Morph y el objeto
crece en continuidad en lugar de aparecer ya gigante.

Ejercita: desbordamiento deliberado del encuadre.

### CardExpansion

Una tarjeta crece hasta convertirse en el contenido de la diapositiva.

```json
{ "mechanism": "CardExpansion", "target": "riego", "others": "dim" }
```

| Parámetro | Tipo | Defecto | Significado |
|---|---|---|---|
| `target` | `str` | — | Tarjeta que se expande |
| `others` | `dim\|push\|hide` | `dim` | Qué pasa con las demás |
| `dim` | `float 0..1` | 0.25 | Opacidad del resto si `others="dim"` |

Emite dos escenas: el estado inicial y el objetivo expandido al área de
contenido (`layout.inset` sobre el encuadre). Las demás tarjetas se
atenúan, se apartan fuera del encuadre o desaparecen, según `others`.

`push` reutiliza la lógica de desplazamiento fuera de encuadre que ya
usa `Reveal`; `dim` reutiliza el atenuado de `Spotlight`.

Ejercita: jerarquía por escala. Es el gesto que `PRODUCT_REVEAL` y
`UIWalkthrough` necesitarán en la fase 2.

### LayerReveal

Capas superpuestas se separan y dejan ver su estructura.

```json
{ "mechanism": "LayerReveal", "layers": ["base", "datos", "interfaz"], "offset": 4.0 }
```

| Parámetro | Tipo | Defecto | Significado |
|---|---|---|---|
| `layers` | `list[str]`, min 2 | — | Capas, de abajo arriba |
| `offset` | `float > 0` | 4.0 | Desplazamiento entre capas |
| `direction` | `up\|down\|left\|right` | `up` | Hacia dónde se despliegan |

Emite N escenas: las capas parten superpuestas y se despliegan en
cascada, una por escena, desplazándose `offset` respecto a la anterior.
Cada capa conserva su id, así que el despliegue se lee como un
movimiento y no como un cambio de contenido.

Ejercita: profundidad y estructura en capas.

### PerspectiveShift

La cámara se desplaza lateralmente sin cambiar el zoom.

```json
{ "mechanism": "PerspectiveShift", "direction": "right", "amount": 0.75 }
```

| Parámetro | Tipo | Defecto | Significado |
|---|---|---|---|
| `direction` | `left\|right\|up\|down` | — | Hacia dónde |
| `amount` | `float > 0` | 1.0 | Fracción del encuadre a desplazar |

Emite una escena con la cámara trasladada `amount` veces su propio
ancho (o alto) en la dirección dada, conservando dimensiones y por tanto
el zoom.

Es panning sobre la escena actual. Se diferencia de `InfiniteCanvas` en
que no exige declarar un canvas con objetos y un tour: sirve para
desplazarse por una escena ya escrita.

Ejercita: panning sin canvas declarado.

## 6. Reglas de lint nuevas

En `rules_visual.py`, registradas en `lint.py` — lo único que hace falta
para añadir una.

**R8. Layout sin solución.** Detecta invocaciones de `Regroup` (y en
fase 2, composiciones) cuyos parámetros de área, gap y número de objetos
no dan un layout válido. Severidad `WARNING`. El hint trae el gap máximo
posible.

Se evalúa antes de compilar, así que el autor lo corrige sin llegar al
`LayoutError`.

**R9. Objeto completamente fuera del encuadre.** Un objeto sin ninguna
intersección con la cámara no se ve, y casi siempre es un error de
coordenadas. Severidad `WARNING`.

Distingue explícitamente de asomar parcialmente, que es intencionado
(`Oversize`) y no genera aviso. El spec original ya listaba este caso
extremo entre los que hay que testear.

## 7. Documentación a actualizar

- `docs/design-rules.md`: R2 pasa a recomendación (`CameraFrame`
  resuelve el alejamiento); añadir R8 y R9.
- `README.md`: la tabla de mecanismos pasa a trece; corregir «los cuatro
  mecanismos» de la sección Estado, que ya estaba desactualizada.
- `.claude/skills/presentation-planner`: los mecanismos nuevos deben
  entrar en el contexto de la skill, o no los usará. Hay tests que
  comprueban que la skill sigue describiendo el compilador real.

## 8. Testing

Los cinco mecanismos y el módulo de layout son puros: se testean sin
generar un solo archivo. TDD, ciclo rojo → verde → refactor.

Por mecanismo:

- **Normal:** el gesto produce las escenas esperadas, con la geometría y
  la cámara correctas.
- **Límite:** un solo objetivo (`CameraFrame`, `LayerReveal` con dos
  capas), objetivos oversize, `clampToWorld` en ambos valores, anclajes
  que producen coordenadas negativas.
- **Error:** id inexistente vía `ctx.require`; parámetros fuera de rango
  rechazados por el schema; `scale` no positiva.

Para layout: gap imposible en `row`, `column` y `grid`; `bounding` de un
solo rect; `clamp` sin intersección.

Regresión: la suite de `Regroup` debe pasar sin modificación tras la
migración a `layout`.

Verificación visual: al aprobar cada mecanismo se compila un `.pptx` de
ejemplo en `examples/` para revisarlo en PowerPoint. El usuario aprueba
mecanismo a mecanismo antes de pasar al siguiente.

## 9. Fuera de alcance

- El render, el IR de objetos y el schema de estilo no se tocan.
- El registro de mecanismos sigue siendo manual. El descubrimiento
  automático que promete el spec original es un arreglo aparte.
- `ObjectEntrance` y `FullScreenImageReveal`: requieren z-order y
  recorte de imagen.
- La capa de composiciones y los cuatro mecanismos del grupo 2: fase 2,
  con su propio spec.
- Temas y estilos reutilizables; duración y easing de Morph; loop de QA
  visual.

## 10. Orden de implementación

1. `ir/layout.py` con sus tests, y `LayoutError`.
2. Migración de `Regroup` a `layout` (tests existentes sin tocar).
3. `CameraFrame` — es el que cierra el hueco de eje y el que más usarán
   las composiciones.
4. `Oversize`.
5. `CardExpansion`.
6. `LayerReveal`.
7. `PerspectiveShift`.
8. Reglas R8 y R9.
9. Documentación y contexto de la skill.

El layout va primero porque tres mecanismos dependen de él. `CameraFrame`
va antes que el resto porque la fase 2 lo usará más que ningún otro.

## 11. Criterios de aceptación

- Los cinco mecanismos emiten escenas correctas, verificado por tests
  puros sin generar archivos.
- `Regroup` pasa su suite original sin modificación tras la migración.
- Un gap imposible produce `LayoutError` con el gap máximo posible, y
  `pptxc lint` lo avisa antes de compilar.
- Un objeto mayor que el encuadre compila sin error ni aviso.
- Un objeto completamente fuera del encuadre produce aviso de lint.
- `CameraFrame` sobre varios objetivos devuelve al plano de conjunto sin
  repetir la escena.
- Cada mecanismo tiene un `.pptx` de ejemplo aprobado en PowerPoint.
- La tabla de mecanismos del README y el contexto de la skill incluyen
  los cinco nuevos.
