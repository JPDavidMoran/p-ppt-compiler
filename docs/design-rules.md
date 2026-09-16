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

**El orden de declaración es el orden de dibujo**, y con sectores que se
solapan eso deja de ser un detalle. En un tren de sectores, el primero
declarado queda al fondo; si el tren retrocede, ese sector vuelve a
cruzar el marco **por debajo** de los que se declararon después, y se
asoma entre ellos en vez de taparlos. Es la misma rueda recorrida al
revés (`color_layers.json`).

**Un objeto puede vivir solo en la transición.** Si está fuera del marco
en las dos escenas pero su recorrido lo cruza, no se ve en ninguna
diapositiva y sin embargo aparece mientras Morph lo interpola. Dos
diapositivas idénticas separadas por un destello de color
(`color_between.json`). La duración manda aquí más que en ningún otro
sitio: con 900 ms el destello se escapa, y conviene subir a 1400.

---

## R11. El texto puede fundirse; las formas y las imágenes, no

Un objeto con peso visual que surge de la nada rompe la continuidad. El
texto es lo bastante ligero como para que un fundido no moleste, pero un
módulo, una tarjeta o un logo deben **entrar y salir con movimiento**.

**Síntoma:** una imagen aparece en el sitio al pasar de diapositiva, o un
bloque de color se desvanece donde estaba. La escena se siente montada,
no narrada.

Por defecto:

| Tipo | Entrada y salida |
|---|---|
| `text` | fundido, o movimiento si acompaña a una forma |
| `shape` | **movimiento** |
| `image` | **movimiento** |

En la práctica es R8 aplicada por tipo: toda forma o imagen que no
persista entre dos escenas se declara en la otra fuera del encuadre, y
Morph la desplaza en lugar de fundirla.

```json
{ "id": "logo", "at": { "x": 112, "y": 15, "w": 15, "h": 26 } }

{ "id": "logo", "at": { "x": 68,  "y": 15, "w": 15, "h": 26 } }
```

Un objeto que **persiste** entre escenas ya morphea por su cuenta: la
regla habla de los que entran o salen.

### La salida, más rápida que la entrada

`transitionMs` vale para la transición entera: PowerPoint no da una
velocidad por objeto sin animaciones intra-slide, que quedan fuera del
compilador. Lo que sí se controla es la **distancia**, y en el mismo
tiempo quien recorre más camino se ve más rápido.

Por defecto, el objeto que sale se aparca **más lejos** que el que entra,
en torno al doble o el triple de recorrido. Lo que se va conviene que se
vaya pronto, para que la atención quede en lo que llega:

```json
"logoPepsi": 68 -> -62    (recorre 130: sale deprisa)
"logoCoca":  112 -> 66    (recorre  46: entra con calma)
```

---

## R12. Una imagen ocupa el espacio que le queda libre

Una imagen pequeña en una diapositiva medio vacía se ve como un icono
perdido, no como el protagonista. Su tamaño no se elige al azar: se
calcula a partir del hueco que dejan el texto y los módulos, y se agota
ese hueco hasta el margen.

**Síntoma:** la mitad derecha de la diapositiva está casi vacía y el logo
mide lo mismo que una línea de texto.

El procedimiento:

1. **Margen estándar de 6 unidades** por los cuatro lados (el mundo mide
   100 × 56.25). Nada de contenido los invade; los fondos sí pueden.
2. **Delimita la zona libre**: donde acaba el bloque de texto más ancho,
   más unas 4 unidades de aire, hasta el margen opuesto.
3. **Encaja la imagen en esa zona** conservando su proporción: se ajusta
   al lado que primero toque el límite, y se centra en el sobrante.

```
zona libre: x 64..94 (30 de ancho)   y 6..50 (44 de alto)

ratio 0.58 -> 25.7 x 44.2   (limita el alto)
ratio 1.00 -> 30.0 x 30.0   (limita el ancho)
```

La proporción original manda siempre: `at` no la conserva por su cuenta,
así que una caja mal calculada deforma la imagen. Calcula un lado a
partir del otro.

Y la jerarquía se mantiene: si la imagen es el sujeto, debe pesar más que
el texto que la acompaña. Un logo al 79% del alto junto a un título al
20% se lee como una composición; los dos al 25%, como una lista.

### Varias imágenes: iguala el área, no el alto

Dos imágenes de proporciones distintas encajadas cada una por su cuenta
acaban con pesos visuales muy diferentes: una vertical llena el alto
mientras una cuadrada se queda a medias, y la marca de la segunda parece
más pequeña. Lo que el ojo compara es la **superficie**, no el lado.

Da a todas la misma área: la mayor que ninguna supere, ni por la zona
libre ni por el límite de ampliación. Luego cada una reparte esa área
según su proporción.

```
área común 1136 u²
  ratio 0.58 -> 25.7 x 44.2
  ratio 1.00 -> 33.7 x 33.7
```

### No amplíes más del 135%

Una imagen estirada por encima de su resolución se ve borrosa. El tope es
**135%** de su tamaño natural —el que tendría a 96 DPI—, y se aplica
antes de repartir el área: si una imagen no puede alcanzar el área común
sin pasarse, esa área baja para todas.

Conviene comprobar los DPI resultantes: por debajo de 100 la imagen ya se
nota blanda en pantalla grande.

---

## R13. Un texto sobre fondo movido necesita un velo

Cuando el texto cae sobre figuras, una imagen o una textura animada, no
basta con que el color contraste: el fondo cambia bajo cada letra y la
lectura se vuelve incómoda. Una capa semitransparente y desenfocada entre
ambos lo resuelve sin ocultar la escena.

**Síntoma:** hay que entornar los ojos para leer un titular, o el texto se
pierde justo donde pasa una figura clara.

Se aplica cuando el texto **no** está dentro de un módulo con relleno
propio —ese ya hace de velo— y el fondo tiene algo más que un color
plano.

### Un panel en la columna de texto

Un velo por cada bloque produce cajas superpuestas que se notan como
cajas. Lo que se busca es **una zona de lectura**: un solo panel que
ocupe la columna donde vive el texto.

```json
{ "id": "panelTexto", "type": "shape",
  "at": { "x": -10, "y": -8, "w": 52, "h": 72.25 },
  "style": { "shape": "rect", "fill": "000000",
             "opacity": 0.42, "blur": 55 } }
```

Con el mundo por defecto (100 × 56.25) ese panel se ve de `x: 0` a
`x: 42` y de arriba abajo del marco.

Cuatro detalles que deciden si se ve bien:

- **Vertical, no horizontal.** Cubre el alto entero del marco pero solo
  el ancho de la columna de texto —en torno a un 40%—, y deja libre la
  zona de la imagen. Una banda que cruza de lado a lado atenúa también lo
  que no debía.
- **Desborda por arriba, abajo y el lado exterior** (`x: -10`, `y: -8`).
  Un borde difuminado dentro del encuadre se ve como el canto de una
  caja; fuera, el panel parece parte del fondo. Solo el borde interior
  queda dentro, y ahí el desenfoque lo funde con la escena.
- **Va detrás de las imágenes**, no delante. Su trabajo es atenuar el
  fondo; si se dibuja después, apaga también el logo.
- **El texto se ciñe al panel.** Si lo desborda, el panel deja de
  cumplir su función justo donde hacía falta.

El desenfoque necesita ser alto para que el degradado se aprecie: **50 a
60 puntos** en un panel de este tamaño. Con 10 o 15 el borde sigue
leyéndose como una línea recta.

### El fondo no se difumina a través del panel

PowerPoint no tiene *backdrop-filter*: una capa no puede desenfocar lo
que hay debajo. `blur` afecta siempre al objeto que lo declara, así que
un panel difuminado sigue dejando ver nítido lo que tiene detrás.

Para que el fondo se vea borroso hay que **difuminar las figuras**, no la
capa. Dos condiciones:

- **Relleno, no contorno.** Una línea de 1 pt no tiene tinta que
  difuminar: por mucho blur que reciba, se desvanece antes de verse
  borrosa. Un círculo relleno y semitransparente sí produce la mancha
  suave que se lee como fondo desenfocado.
- **Sin `p:style`.** Cada forma trae un `effectRef` del tema que gana al
  `effectLst` propio, y PowerPoint aplica el del tema descartando el
  desenfoque en silencio. El compilador lo retira al aplicar blur.

La alternativa, cuando el efecto no compensa, es dejar la zona del panel
sin figuras.

El campo `veil` de un texto sigue sirviendo para un rótulo suelto, donde
una sola línea necesita fondo propio.

```json
"style": { "color": "FFFFFF", "veil": { "opacity": 0.45, "blur": 10 } }
```

### Qué color de velo

Lo decide la luminancia del texto, no el gusto:

| Texto | Velo |
|---|---|
| claro (luminancia ≥ 0.5) | **oscuro** |
| oscuro (luminancia < 0.5) | **claro** |

Es el contraste que sobrevive a cualquier fondo: oscurecer bajo un texto
blanco aumenta la diferencia justo donde hacía falta. La luminancia se
calcula con los coeficientes ITU-R BT.601, que pesan el verde mucho más
que el azul, así que un amarillo cuenta como claro y un azul saturado
como oscuro.

El velo se deduce solo si no se declara `color`. Fijarlo a mano vale para
un velo de marca —un azul corporativo muy oscuro en lugar de negro—, no
para invertir la regla.

### Opacidad y desenfoque

Entre **0.35 y 0.55** de opacidad el fondo sigue viéndose y el texto se
lee. Por debajo de 0.3 el velo no hace su trabajo; por encima de 0.6
tapa la escena y más valdría un módulo con relleno.

El desenfoque no difumina el fondo —PowerPoint no tiene *frosted glass*—
sino el borde del propio velo, y eso es justo lo que evita que se lea
como una caja recortada sobre la imagen.

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
