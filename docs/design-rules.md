# Reglas de composición

Un DSL puede compilar sin errores y aun así narrar mal. El compilador
valida la estructura; este documento recoge lo que solo se ve al
reproducir la presentación.

Cada regla nació de un defecto observado en una presentación real. Las
marcadas **[lint]** las detecta `pptxc lint`; las demás requieren ojo
humano o un modelo de visión.

Este documento es también el contexto que necesita un planner
automático: sin él, un LLM que escriba DSL repetirá estos errores.

---

## R1. Cada escena es una diapositiva **[lint]**

Un mecanismo no anima dentro de una diapositiva: emite diapositivas
nuevas, y el espectador avanza hasta ellas con un clic.

**Síntoma:** la presentación se queda en un primer plano que no lleva a
ninguna parte, y hay que pulsar otra vez para continuar.

**Mal** — el zoom acerca al título y el siguiente clic salta de tema:

```json
{ "scene": "portada" },
{ "mechanism": "CameraZoom", "target": "titulo", "scale": 1.8 },
{ "scene": "otroTema" }
```

**Bien** — el zoom enfoca aquello de lo que se va a hablar.

---

## R2. Para volver al plano general, repite la escena **[lint]**

`CameraZoom` **siempre encuadra su objetivo**. No sirve para alejarse:
`scale: 1.0` sobre un título deja la cámara sobre el título.

**Síntoma:** al cerrar un recorrido aparece un elemento aislado (un
título a pantalla completa) en lugar de la vista de conjunto.

**Mal:**

```json
{ "mechanism": "FocusTransition", "sequence": ["a", "b", "c"] },
{ "mechanism": "CameraZoom", "target": "tituloSeccion", "scale": 1.0 }
```

**Bien** — repetir la escena hace que el differ morphee de vuelta:

```json
{ "mechanism": "FocusTransition", "sequence": ["a", "b", "c"] },
{ "scene": "modulos" }
```

---

## R3. Para un antes/después, reutiliza el id **[lint]**

Dos objetos distintos solo pueden desvanecerse uno y aparecer el otro.
Un mismo id en dos escenas morphea: el bloque crece, se desplaza y
cambia de texto de forma continua.

**Síntoma:** parpadeo. Un bloque desaparece, queda un hueco, y el otro
aparece.

**Mal** — dos objetos y un estado intermedio donde se ven ambos:

```json
{ "id": "antes",   "at": { "x": 10, "y": 24, "w": 36, "h": 16 } },
{ "id": "despues", "at": { "x": 54, "y": 24, "w": 36, "h": 16 } }
```

**Bien** — un objeto que cambia de estado:

```json
{ "id": "estado", "content": "Antes\nRegistros en papel",
  "at": { "x": 30, "y": 24, "w": 40, "h": 18 } }

{ "id": "estado", "content": "Después\nTrazabilidad en tiempo real",
  "at": { "x": 22, "y": 20, "w": 56, "h": 24 } }
```

---

## R4. Objetos distintos con la misma geometría se sustituyen **[lint]**

Es el reverso de R3. Dos objetos **diferentes** que ocupan la misma
posición en escenas consecutivas parecen "cambiar de texto" en el sitio.

**Síntoma:** el título de un tema se transforma en el del siguiente
mientras el resto de la diapositiva está vacío.

Ocurre con los títulos de sección, que suelen compartir geometría por
coherencia visual. Dos salidas:

- Si los temas son independientes, que la escena no comparta más
  geometría, para que la transición sea un fade limpio.
- Si la continuidad es deliberada, reutiliza el id (R3) y el efecto pasa
  a ser intencionado.

---

## R5. Una escena no debe arrastrar objetos del tema anterior **[lint]**

Los mecanismos operan sobre la escena actual y conservan sus objetos.
Encadenar un mecanismo justo después de otro tema arrastra lo que
quedara visible.

**Síntoma:** un bloque del tema anterior aparece flotando en el nuevo.

**Bien** — declarar una escena propia antes del mecanismo:

```json
{ "scene": "mapa" },
{ "mechanism": "FocusTransition", "sequence": ["zonaA", "zonaB"] }
```

---

## R6. Los títulos necesitan alineación explícita

`align` es `left` por defecto. Un título pensado para ir centrado se ve
descentrado si no se declara.

**Síntoma:** el texto aparece pegado a la izquierda de su caja.

```json
"style": { "fontSize": 30, "bold": true, "align": "center" }
```

---

## R7. El tamaño de fuente escala con la cámara

Un texto en una escena acercada se proyecta más grande: el compilador
multiplica el tamaño por el zoom para que el texto acompañe al resto de
la composición.

**Consecuencia:** el `fontSize` del DSL es el tamaño a cámara completa,
no el que se verá si la escena está acercada. Un título de 40 pt en una
cámara 2× se verá como 80 pt.

---

## R8. Para entrar con movimiento hay que existir antes fuera del marco

Morph solo puede interpolar entre dos estados de un mismo objeto. Un
objeto que no existe en la escena anterior no tiene desde dónde venir, y
PowerPoint solo puede hacerlo aparecer por opacidad.

**Síntoma:** unos elementos se deslizan y otros surgen de la nada en la
misma transición. El corte de ritmo se nota aunque no se sepa explicar.

**Mal** — los detalles solo existen en la escena de destino:

```json
{ "id": "moduloPleno",   "objects": ["modulo"] },
{ "id": "moduloDetalle", "objects": ["modulo", "detalle1", "detalle2"] }
```

**Bien** — existen ya en la primera, aparcados fuera del encuadre:

```json
{ "id": "detalle1", "at": { "x": 112, "y": 19, "w": 54, "h": 10 } }

{ "id": "detalle1", "at": { "x": 38,  "y": 19, "w": 54, "h": 10 } }
```

El mundo mide 100 de ancho por defecto, así que una `x` de 112 queda
fuera de la pantalla. Conservar la misma `y` en ambas escenas hace que el
objeto entre en línea recta; variarla lo hace llegar en diagonal.

Lo mismo vale para `InfiniteCanvas`: sus zonas van declaradas en la
escena base, no dentro del mecanismo. Declaradas solo dentro, entran en
la primera transición y salen en la última, y esas dos se ven como un
fundido mientras las intermedias se deslizan.

---

## R9. Que viaje más de un objeto

Un solo objeto que permanece mientras todo lo demás cambia no se lee como
continuidad, sino como un resto olvidado del tema anterior.

**Síntoma:** el objeto que sobrevive parece haberse quedado ahí por
descuido, aunque sea el protagonista de la transición.

Es lo que detecta **R5** en el linter. La salida no es silenciar el
aviso: es dar al protagonista un acompañante. Un módulo que encoge hacia
una esquina llega mejor con su etiqueta, que además puede cambiar de
texto para situar al espectador:

```json
{ "id": "leyenda", "content": "El primero de los tres módulos" }

{ "id": "leyenda", "content": "Módulo 1 de 3" }
```

---

## R10. Una rueda gira sobre el centro de su caja

PowerPoint rota cada forma sobre el centro de su propia caja, no sobre un
punto que se pueda elegir. Para que un sector orbite un eje concreto, su
caja tiene que estar **centrada en ese eje**, por grande que resulte.

**Síntoma:** los sectores se esparcen por la pantalla en vez de girar
juntos, o asoman colores que deberían quedar fuera del marco.

Para que solo se vea un sector, el eje va fuera del marco y lo bastante
lejos: desde él, el marco abarca un ángulo que debe ser **menor** que el
del sector. Con el eje pegado al borde izquierdo (`x: -18`) el marco
abarca casi 115°, así que un cuarto de 90° no llega y los vecinos asoman
por las esquinas. Alejándolo a `x: -40` el marco baja a 70° y el cuarto
lo cubre con holgura.

Y los sectores necesitan `sectorStart`/`sectorEnd` explícitos: por
defecto, `pie` dibuja de 0 a 162 grados.

**Sitúa cada sector por sus ángulos, no rotándolo.** PowerPoint normaliza
la rotación —un `-45` se escribe como `315`—, y combinada con los ángulos
del sector el resultado deja de ser el previsto: asoman colores de
cuartos que deberían quedar fuera. Con `sectorStart`/`sectorEnd` la
posición es absoluta y no hay ambigüedad de signo.

Coloca además el eje de modo que el marco **no cruce el origen de
ángulos**: un sector que iría de 315° a 405° no se puede expresar de una
pieza. Con el eje arriba a la izquierda (`-40, -20`) el marco ocupa
8°..62°, y cada cuarto cabe entero.

**En cada transición debe moverse un solo sector: el que entra.** Si el
saliente también cambia de ángulo, su borde barre la pantalla al retirarse
y se ven dos olas cruzando a la vez. El sector que ya cubrió el marco se
queda quieto y la capa siguiente lo tapa: al espectador le llega un color
nuevo sobre uno estable, que es como se lee una ola.

Los que aún no han entrado esperan todos en el mismo ángulo, fuera del
marco. Los ángulos no se normalizan con módulo: el schema los admite
entre -720 y 720 para que un sector pueda avanzar sin dar la vuelta.

Un sector grande anclado a un eje exterior no se percibe como un giro,
sino como una **ola de color que invade el marco**: el borde del sector
barre la pantalla.

De ahí salen dos efectos opuestos, y la diferencia está en cuántos
sectores se mueven y en su ancho:

- **Una ola** (`color_waves.json`): sectores más anchos que el marco y
  solo el entrante en movimiento. Llega un color sobre uno estable, como
  una marea que invade el marco.
- **Una rueda** (`color_wheel.json`): sectores más **estrechos** que el
  marco, pegados unos a otros como radios, y todos avanzando a la vez.
  Cada escena reparte el marco entre dos colores, y el conjunto se lee
  como un disco que gira.

El ancho es lo que decide: más que el marco y una ola lo tapa entero;
menos, y varias conviven en pantalla.

---

## Lo que el linter no puede ver

Estas reglas requieren mirar el resultado:

- Texto que desborda su caja.
- Contraste insuficiente entre relleno y color de texto.
- Jerarquía visual pobre: todo del mismo tamaño.
- Demasiados elementos simultáneos.
- Ritmo: tres zooms seguidos cansan.

Es el argumento para un loop de QA visual: renderizar las diapositivas
a imagen y que un modelo de visión las evalúe.
