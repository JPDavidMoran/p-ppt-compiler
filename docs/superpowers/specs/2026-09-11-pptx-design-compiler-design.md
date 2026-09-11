# PowerPoint Design Compiler — Diseño

Fecha: 2026-09-11
Estado: aprobado para implementación

## 1. Propósito

Compilar un DSL declarativo de presentaciones en archivos `.pptx` con
transiciones Morph reales, controlando OOXML directamente.

La IA no genera PPTX ni XML. Genera DSL. El compilador traduce.

Este documento cubre **solo el compilador**. El director creativo, el
planner y el loop de QA visual son specs posteriores.

## 2. Alcance

Dentro del alcance:

- DSL en JSON validado con Pydantic.
- Scene IR con mundo persistente, cámara y objetos con identidad.
- Differ que deriva transiciones comparando escenas consecutivas.
- Generación de `.pptx` con `python-pptx` y parcheo OOXML con `lxml`.
- Cuatro mecanismos: `CameraZoom`, `BeforeAfter`, `FocusTransition`,
  `InfiniteCanvas`.
- Tipos de objeto: `text`, `shape`, `image`.
- CLI con `compile`, `validate`, `inspect`.

Fuera del alcance:

- Generación de DSL por IA.
- Render de slides a imagen y evaluación con modelos de visión.
- Automatización COM de PowerPoint.
- Sistema de composiciones y temas.
- Animaciones intra-slide (`<p:timing>`). Solo transiciones entre slides.

## 3. Decisiones de diseño

| Decisión | Elección | Razón |
|---|---|---|
| Primer entregable | El compilador | El riesgo real es OOXML, no la IA |
| Lenguaje | Python | `python-pptx` expone el árbol lxml del slide |
| Abstracción central | Escenas + cámara | Morph es un interpolador entre estados |
| Mecanismos | Macros sobre escenas | El compilador no cambia al añadir uno |
| Verificación | Golden file + tests de XML | El XML real de PowerPoint es la verdad |

### Por qué escenas y no efectos

Morph interpola entre dos estados de los mismos objetos. Un DSL cuya
semántica es "estados sucesivos del mismo mundo" mapea uno a uno con
ese comportamiento.

Si los mecanismos fueran la primitiva, cada uno reimplementaría el
duplicado de slides y la gestión de identidad. Con escenas como núcleo,
esa lógica vive en un solo módulo y los mecanismos solo emiten datos.

## 4. Arquitectura

```
1. DSL          JSON del autor
      |  expander      macros -> escenas
2. Scene IR     mundo, cámara, objetos con identidad
      |  differ        compara escenas consecutivas
3. Slide Plan   slides + objetos persistentes + transiciones
      |  renderer      proyección cámara->slide, luego OOXML
4. PPTX
```

### Capas

| Capa | Responsabilidad | Pureza |
|---|---|---|
| `dsl/` | Schemas Pydantic, carga y validación | Puro |
| `mechanisms/` | Macros: parámetros -> escenas | Puro |
| `ir/` | Scene, Camera, SceneObject, identidad | Puro |
| `compiler/` | Differ, planner de slides | Puro |
| `render/` | Proyección, python-pptx, OOXML | I/O |
| `cli/` | Entrada de línea de comandos | I/O |

Las capas puras no importan `pptx` ni tocan disco. Reciben datos y
devuelven datos.

Flujo unidireccional: `cli -> dsl -> mechanisms -> ir -> compiler -> render`.
Ninguna capa importa una capa posterior.

## 5. Modelo de datos

### Mundo y cámara

Los objetos viven en coordenadas de mundo sobre un lienzo continuo. La
unidad de mundo es arbitraria; el encuadre por defecto es 100 x 56.25
unidades, con la misma proporción que 16:9.

La cámara es un rectángulo sobre ese mundo:

```json
{"x": 0, "y": 0, "w": 100, "h": 56.25}
```

El renderer proyecta lo que la cámara ve al área de la slide
(13.333 x 7.5 pulgadas). Un objeto que no se mueve en el mundo cambia de
posición en la slide si la cámara se movió. Ese es el efecto de zoom
cinematográfico: sale de la geometría, no de un efecto especial.

Toda aritmética interna en EMU (914400 por pulgada) para evitar
redondeo acumulado.

### Escena

```json
{
  "id": "intro",
  "camera": {"x": 0, "y": 0, "w": 100, "h": 56.25},
  "objects": [
    {
      "id": "titulo",
      "type": "text",
      "content": "Gestión de áreas verdes",
      "at": {"x": 10, "y": 20, "w": 60, "h": 8},
      "style": {"fontSize": 44, "color": "1B4332", "bold": true}
    }
  ]
}
```

El `id` de cada objeto es su identidad conceptual. El mismo `id` en dos
escenas significa el mismo objeto, y es lo que permite el Morph.

### Documento DSL

```json
{
  "presentation": {"title": "...", "aspectRatio": "16:9"},
  "world": {"w": 100, "h": 56.25},
  "scenes": [ ... ],
  "sequence": [
    {"scene": "intro"},
    {"mechanism": "CameraZoom", "target": "dashboard", "scale": 2.5}
  ]
}
```

`scenes` declara escenas nombradas. `sequence` es la línea de tiempo:
entradas que son o bien una referencia a escena, o bien una invocación
de mecanismo que expande a una o más escenas.

## 6. Mecanismos

Contrato:

```python
def expand(params: ParamsModel, ctx: ExpansionContext) -> list[Scene]
```

Función pura. No conoce PowerPoint, no genera XML, no asigna ids OOXML.
`ctx` da acceso a la escena actual y al mundo declarado.

### CameraZoom

Acerca la cámara a un objeto. Los objetos no se mueven.

```json
{"mechanism": "CameraZoom", "target": "dashboard", "scale": 2.5}
```

Emite una escena con la misma lista de objetos y la cámara reencuadrada
sobre el objeto destino. Ejercita: cámara móvil, mundo fijo.

### BeforeAfter

Cámara fija; unos objetos se sustituyen por otros.

```json
{
  "mechanism": "BeforeAfter",
  "before": ["estadoViejo"],
  "after": ["estadoNuevo"],
  "keep": ["titulo"]
}
```

Dos escenas con idéntica cámara. Los objetos de `keep` persisten; los
de `before` desaparecen y los de `after` entran. Ejercita: mundo móvil,
cámara fija. Es el complemento exacto de `CameraZoom`; juntos validan
que la abstracción es general en ambos ejes.

### FocusTransition

Encadena focos sobre objetos existentes.

```json
{"mechanism": "FocusTransition", "sequence": ["modA", "modB"], "scale": 2.0}
```

Se implementa **reutilizando** `CameraZoom` por cada elemento de la
secuencia, no duplicando su lógica. Ejercita: composición de mecanismos
y secuencias de N escenas.

### InfiniteCanvas

Declara un lienzo mayor que el encuadre y genera un recorrido.

```json
{
  "mechanism": "InfiniteCanvas",
  "objects": [ ... ],
  "tour": [{"at": "zonaA", "scale": 1.5}, {"at": "zonaB", "scale": 1.5}]
}
```

Ejercita panning lateral y objetos fuera del encuadre. PowerPoint admite
shapes fuera del área visible de la slide, y eso es lo que hace posible
la sensación de entrada desde fuera del marco.

Los `objects` que declara este mecanismo se añaden a la escena que emite,
igual que si estuvieran escritos en una escena del DSL. Es azúcar para no
tener que declarar a mano una escena con muchos objetos dispersos; no
introduce un contenedor distinto. Cada `at` del `tour` referencia el `id`
de uno de esos objetos.

### Registro

`MECHANISMS: dict[str, Mechanism]` poblado por descubrimiento del
paquete `mechanisms/`. Añadir un mecanismo es añadir una carpeta; el
compilador no se modifica.

Cada mecanismo vive en su carpeta:

```
mechanisms/camera_zoom/
  __init__.py    expand()
  schema.py      parámetros Pydantic
  README.md      concepto, intent, constraints, ejemplo
```

Los `example.pptx` y `preview.png` se añaden cuando exista el loop de
render, no antes: sin render no pueden verificarse.

## 7. Differ

Recibe dos escenas consecutivas ya proyectadas y decide la transición.

```
diff(A, B):
    persistentes = ids(A) & ids(B)
    salientes    = ids(A) - ids(B)
    entrantes    = ids(B) - ids(A)

    for id in persistentes:
        comparar geometría proyectada en A vs B
```

Decisión:

- Algún persistente con geometría distinta -> `Morph`, matching `byObject`.
- Solo entradas y salidas -> `Fade`.
- Sin cambios -> sin transición.

La comparación es sobre geometría **proyectada**, no de mundo: un objeto
inmóvil en un mundo con cámara móvil sí cambia en la slide, y debe
morphear.

## 8. Identidad de objetos

Un objeto con `id` del DSL presente en varias escenas recibe el **mismo**
identificador OOXML en todas las slides. `ir/identity.py` mantiene el
mapa `dsl_id -> ooxml_id` durante toda la compilación.

Si la identidad falla, PowerPoint no empareja nada y degrada a un fade
genérico **sin emitir error**. Ese fallo silencioso es el riesgo
principal del proyecto, y por eso existe un test dedicado que afirma que
el identificador se repite entre slides.

### Incertidumbre resuelta

**Resuelto el 2026-09-11 contra el golden file.** Basta con `<p:cNvPr>`
llevando `id` y `name` estables entre slides; no hizo falta emitir
`creationId`.

El hallazgo importante fue otro: **Morph vive en el namespace `p159`**
(`.../powerpoint/2015/09/main`), no en `p14` (2010). Un `p14:morph` hace
que PowerPoint entre al `mc:Choice`, no reconozca el elemento y lo
descarte **en silencio**: la transición degrada a un corte abrupto sin
error alguno. El atributo `p14:dur` sí permanece en el namespace de 2010.

El enum COM de la transición es `EntryEffect = 3954`, hallado por
barrido de los 159 valores válidos porque no está documentado.

## 9. Capa OOXML

`python-pptx` no expone transiciones. `render/transitions.py` las inserta
manipulando el árbol lxml del slide:

- Construye el bloque `<mc:AlternateContent>` que contiene `<p:transition>`.
- Declara `mc`, `p159` en el `Choice` (con `Requires="p159"`) y `p14`
  en la transición para el atributo de duración.
- Lo inserta en la posición correcta dentro de `<p:sld>`.

El orden de los hijos importa en OOXML: un elemento en el sitio
equivocado hace que PowerPoint declare el archivo dañado. La plantilla
XML exacta se extrae del golden file, no se escribe de memoria.

## 10. Errores

Jerarquía con raíz `PresentationCompilerError`:

- `DSLValidationError` — el JSON no cumple el schema.
- `UnknownMechanismError` — mecanismo no registrado.
- `IdentityConflictError` — dos objetos con el mismo id en una escena.
- `MissingTargetError` — un mecanismo referencia un id inexistente.
- `ProjectionError` — cámara degenerada (ancho o alto <= 0).

Cada error lleva contexto: qué id, qué escena, qué mecanismo. Fail fast
siempre; nunca `return None` silencioso ni valores por defecto que
enmascaren un DSL mal escrito.

## 11. Estrategia de verificación

### Golden file

Antes de escribir el compilador se crea manualmente en PowerPoint un
`.pptx` de referencia: dos slides, un rectángulo que cambia de posición
y tamaño, transición Morph aplicada. Se guarda en
`fixtures/golden/morph_reference.pptx`.

Su XML es la fuente de verdad para la plantilla de transición y para
resolver la incertidumbre de la sección 8.

Esta acción la realiza el usuario. Bloquea el resto de la implementación.

### Niveles de test

- **Unitarios**, sin Office, en milisegundos: proyección, differ,
  identidad, expansión de cada mecanismo, validación de schemas.
- **Contra golden file**: el XML generado coincide estructuralmente con
  el de PowerPoint real.
- **Integración**: compilar un DSL de ejemplo, reabrir el `.pptx` con
  `python-pptx`, afirmar número de slides, identificadores repetidos
  entre slides y presencia del bloque de transición.

### Casos extremos obligatorios

Escena vacía; id duplicado dentro de una escena; cámara de escala cero
o negativa; objeto completamente fuera del encuadre; mecanismo con
`target` inexistente; DSL con campos desconocidos; secuencia de una sola
escena (sin transición posible).

Todos deben fallar con error tipado y mensaje accionable, salvo el
objeto fuera de encuadre y la secuencia de una escena, que son válidos.

Comportamiento de los dos casos válidos:

- **Objeto fuera de encuadre**: se emite igualmente, con coordenadas de
  slide negativas o mayores que el área visible. No se recorta ni se
  descarta. Es el mecanismo por el que un objeto entra desde fuera del
  marco, y descartarlo rompería el Morph al desaparecer su identidad.
- **Secuencia de una sola escena**: produce un `.pptx` de una slide sin
  transición. No es un error.

## 12. CLI

```
pptxc compile deck.json -o deck.pptx
pptxc validate deck.json
pptxc inspect deck.pptx
```

`inspect` vuelca transiciones e identificadores de shapes de un `.pptx`
existente. No es un extra: es la herramienta con la que se disecciona el
golden file y se depura un Morph que no funciona.

## 13. Estructura del proyecto

```
src/pptx_compiler/
  dsl/          schemas, loader
  mechanisms/   camera_zoom/ before_after/ focus_transition/ infinite_canvas/
  ir/           scene, camera, scene_object, identity
  compiler/     differ, slide_planner
  render/       projection, pptx_builder, transitions
  errors.py
  cli/
tests/
  unit/ golden/ integration/
docs/superpowers/specs/
examples/
fixtures/golden/morph_reference.pptx
```

Límites de tamaño por archivo: engine y core 150 líneas, parsers 120,
CLI 50. Tipos y tests sin límite.

Dependencias: `python-pptx`, `pydantic`, `lxml`, `typer`, `pytest`.

## 14. Orden de construcción

El orden coloca el riesgo al principio, pese a que el entregable incluye
cuatro mecanismos.

1. **Golden file y disección de su XML.** Resuelve la incertidumbre de
   identidad y fija la plantilla de transición.
2. **Scene IR, cámara y proyección.** Puro y muy testeable.
3. **Identidad y differ.** Puro.
4. **Renderer y capa OOXML.** Primer `.pptx` que morphea de verdad.
5. **Los cuatro mecanismos**, sobre un núcleo ya probado, en este orden:
   `CameraZoom`, `BeforeAfter`, `FocusTransition`, `InfiniteCanvas`.

Si el modelo de identidad resulta mal planteado, se descubre en el paso 4,
antes de que existan mecanismos que corregir.

## 15. Reglas de composición

Un DSL puede compilar sin errores y narrar mal. Las reglas descubiertas
reproduciendo presentaciones reales viven en `docs/design-rules.md`, y
`pptxc lint` detecta las automatizables.

Esto no estaba en el diseño original y resultó ser necesario: todos los
defectos encontrados tras el primer PPTX funcional fueron de composición,
no de compilación.

## 16. Criterios de aceptación

- Un DSL de ejemplo compila a `.pptx` que PowerPoint abre sin reparar.
- Ese archivo morphea visiblemente al pasar de slide.
- Los cuatro mecanismos producen escenas correctas, verificado por tests
  unitarios sin generar archivos.
- El identificador OOXML de un objeto persistente es idéntico en todas
  las slides donde aparece.
- Todos los casos extremos de la sección 11 producen el comportamiento
  especificado.
- Ningún archivo de código supera su límite de capa.
