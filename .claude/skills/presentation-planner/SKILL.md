---
name: presentation-planner
description: Use when the user wants to create a presentation, slide deck, or .pptx from a topic or brief - writes Presentation DSL for this repo's compiler, then lints and compiles it. Covers creative concept, scene composition and verification.
---

# Planificador de presentaciones

Traduce un encargo en un `.pptx` con transiciones Morph, escribiendo DSL
para el compilador de este repositorio.

**Tú no escribes XML ni tocas PowerPoint.** Escribes DSL; el compilador
hace el resto. Tu trabajo es el concepto y la composición.

## Antes de empezar

Lee estos dos archivos. No los resumas de memoria: cambian.

- `docs/design-rules.md` — las reglas de composición. **Obligatorio.**
- `reference/schema.md` — todos los campos válidos del DSL.

## El flujo

Cuatro fases. No saltes la cuarta.

### 1. Entender el encargo

Pregunta solo lo que cambia el resultado, una cosa a la vez:

- ¿De qué trata y para quién?
- ¿Cuántas diapositivas, aproximadamente?
- ¿Hay datos, cifras o un producto concreto que mostrar?

Si el usuario ya lo dijo todo en su mensaje, no preguntes. Pasa a la 2.

### 2. Proponer el concepto

Ofrece **2 o 3 conceptos** breves y distintos entre sí. Cinco líneas cada
uno, no más. Ejemplos de dirección:

- **Editorial técnico** — tipografía grande, mucho aire, zooms sobre datos.
- **Mapa interactivo** — lienzo amplio, navegación por recorrido.
- **Demo cinematográfica** — un objeto protagonista, acercamientos, detalle.

El usuario elige. No empieces a escribir DSL antes de que elija.

### 3. Escribir el DSL

Aplica las reglas de `docs/design-rules.md`. Las cuatro que más se
incumplen:

- **Cada escena es una diapositiva.** Un mecanismo emite diapositivas
  nuevas; no anima dentro de una.
- **Para volver al plano general, repite la escena.** `CameraZoom`
  siempre encuadra su objetivo; no sirve para alejarse.
- **Para un antes/después, reutiliza el id.** Dos objetos distintos
  parpadean; un mismo id morphea.
- **Títulos de secciones distintas, geometría distinta.** Si comparten
  posición, parecerá que el texto cambia en el sitio.

Dosifica la información: `Build` revela los puntos de uno en uno en
lugar de mostrarlos de golpe, y `Spotlight` destaca sin perder de vista
el conjunto.

Consulta `reference/patterns.md` para secuencias ya probadas.

Escribe el archivo en `examples/` o donde el usuario indique.

### 4. Verificar — no es opcional

```bash
pptxc lint <archivo>.json
pptxc compile <archivo>.json -o <archivo>.pptx
```

**`lint` debe salir limpio.** Si avisa, corrige el DSL — nunca ignores el
aviso ni pidas desactivar la regla. Cada regla existe porque un defecto
real llegó a una presentación.

Si `lint` señala algo que crees deliberado (por ejemplo, dos títulos que
quieres que se sustituyan en el sitio), dilo explícitamente al usuario y
deja que decida; no lo silencies por tu cuenta.

Cuando compile, dile al usuario que lo abra y reproduzca las
transiciones. Lo que ningún linter ve —desbordes de texto, contraste,
ritmo— solo aparece mirando.

## Lo que no debes hacer

- Inventar mecanismos. Solo existen ocho: `CameraZoom`, `BeforeAfter`,
  `FocusTransition`, `InfiniteCanvas`, `Build`, `Regroup`, `Spotlight`
  y `Reveal`.
- Escribir OOXML, XML o llamar a python-pptx directamente.
- Saltarte el lint porque "el DSL se ve bien".
- Amontonar zooms: tres seguidos cansan. Un recorrido se cierra volviendo
  al plano general.
- Llenar una diapositiva. El espacio vacío es parte de la composición.
