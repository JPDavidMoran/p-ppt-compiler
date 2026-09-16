# Patrones de secuencia

Combinaciones probadas que pasan `lint` y se reproducen bien. Úsalas como
punto de partida en vez de inventar desde cero.

## P1. Portada

Una escena, sin mecanismo. El primer plano no necesita movimiento.

```json
{ "scene": "portada" }
```

Composición que funciona: una barra de acento fina sobre el título,
título grande en negrita, subtítulo menor debajo. Alineados a la
izquierda y con aire a la derecha; una portada centrada se ve genérica.

```json
{ "id": "acento",    "type": "shape", "at": { "x": 12, "y": 20, "w": 14, "h": 0.8 } }
{ "id": "titulo",    "type": "text",  "at": { "x": 12, "y": 23, "w": 64, "h": 9 } }
{ "id": "subtitulo", "type": "text",  "at": { "x": 12, "y": 33, "w": 60, "h": 5 } }
```

## P2. Recorrido con vuelta

El patrón más útil. Presenta un conjunto, visita cada parte, vuelve.

```json
{ "scene": "modulos" },
{ "mechanism": "FocusTransition", "sequence": ["modA", "modB", "modC"], "scale": 1.9 },
{ "scene": "modulos" }
```

La última línea es imprescindible: sin ella la sección termina en un
primer plano y el espectador queda encallado.

`scale` entre 1.8 y 2.2 funciona bien. Más de 2.5 pierde el contexto: el
espectador no sabe dónde está.

## P3. Antes y después que morphea

**Un objeto con el mismo id en dos escenas**, no dos objetos.

```json
"scenes": [
  { "id": "impactoAntes", "objects": [
      { "id": "titulo", "type": "text", "at": { "x": 16, "y": 11, "w": 68, "h": 8 } },
      { "id": "estado", "type": "shape", "content": "Antes\nRegistros en papel",
        "at": { "x": 30, "y": 24, "w": 40, "h": 18 } } ] },

  { "id": "impactoDespues", "objects": [
      { "id": "titulo", "type": "text", "at": { "x": 16, "y": 11, "w": 68, "h": 8 } },
      { "id": "estado", "type": "shape", "content": "Después\nTrazabilidad en tiempo real",
        "at": { "x": 22, "y": 20, "w": 56, "h": 24 } } ] }
]
```

```json
{ "scene": "impactoAntes" },
{ "scene": "impactoDespues" }
```

Que el "después" sea mayor y de color más intenso refuerza la mejora sin
necesidad de decirlo.

## P4. Énfasis en un dato

Presentar la escena y acercarse a la cifra de la que vas a hablar.

```json
{ "scene": "metricas" },
{ "mechanism": "CameraZoom", "target": "cifraClave", "scale": 2.4 }
```

Solo si vas a hablar de ese dato a continuación. Un zoom que no lleva a
ninguna parte deja al espectador esperando algo que no llega.

## P4b. Revelar sin enseñar el final

`Build`, `Reveal` y `BeforeAfter` parten de una escena que ya contiene el
estado final. Si esa escena se emite, la primera diapositiva enseña justo
lo que el mecanismo iba a revelar.

**Mal** — la slide 1 muestra los tres puntos y luego los oculta:

```json
{ "scene": "lista" },
{ "mechanism": "Build", "sequence": ["p1", "p2", "p3"] }
```

**Bien** — la escena carga el estado sin dibujarse:

```json
{ "scene": "lista", "emit": false },
{ "mechanism": "Build", "sequence": ["p1", "p2", "p3"] }
```

## P4c. Formas e imágenes entran con movimiento

Una forma o una imagen que aparece de la nada rompe la continuidad (R11).
Decláralas en **todas** las escenas: dentro donde les toca, aparcadas
fuera del encuadre donde no.

```json
{ "id": "logo", "at": { "x": 112, "y": 15, "w": 15, "h": 26 } }

{ "id": "logo", "at": { "x": 68,  "y": 15, "w": 15, "h": 26 } }
```

No basta con aparcarla en la escena contigua: si hay tres escenas y solo
se declara en dos, la tercera vuelve a hacerla aparecer. Conviene
aparcarla a la derecha en las escenas anteriores a su aparición y a la
izquierda en las posteriores, para que el recorrido sea coherente.

Los textos son la excepción: pueden fundirse sin más.

**La salida más rápida que la entrada.** La duración es única para toda
la transición, así que la velocidad la marca la distancia: aparca el
objeto saliente dos o tres veces más lejos que el entrante, y lo que se
va se irá deprisa mientras lo que llega entra con calma.

## P5. Mapa o lienzo amplio

Objetos lejos del encuadre inicial, recorridos por la cámara.

```json
{ "scene": "mapa" },
{ "mechanism": "FocusTransition", "sequence": ["zonaNorte", "zonaSur"], "scale": 1.8 },
{ "scene": "mapa" }
```

Declara siempre la escena propia antes, o el mecanismo arrastrará los
objetos del tema anterior.

Para un lienzo mucho mayor que la pantalla, `InfiniteCanvas` declara los
objetos y el recorrido en una sola llamada.

Declara las zonas en la **escena base**, no dentro del mecanismo. Si solo
existen dentro, entran en la primera transición y salen en la última: sin
objeto que emparejar, esas dos se ven como una aparición por opacidad
mientras las intermedias se deslizan. Declaradas en la escena, todas las
transiciones son deslizamiento continuo.

---

## Estructura de una presentación completa

Una de unas diez diapositivas, combinando patrones:

```json
"sequence": [
  { "scene": "portada" },

  { "scene": "contexto" },

  { "scene": "modulos" },
  { "mechanism": "FocusTransition", "sequence": ["modA", "modB", "modC"], "scale": 1.9 },
  { "scene": "modulos" },

  { "scene": "impactoAntes" },
  { "scene": "impactoDespues" },

  { "scene": "cierre" }
]
```

Ritmo: alterna secciones con movimiento y secciones estáticas. Dos
recorridos seguidos cansan.

Cada título de sección con **geometría distinta** — si comparten posición
parecerá que el texto cambia en el sitio:

```json
"tituloModulos": { "x": 12, "y": 9,  "w": 76, "h": 8 }
"tituloImpacto": { "x": 16, "y": 11, "w": 68, "h": 8 }
"tituloCierre":  { "x": 20, "y": 7,  "w": 60, "h": 8 }
```

## Paleta

Una familia de color con tres o cuatro tonos, más un neutro para lo
anterior o descartado. Ejemplo en verde:

```
1B4332  texto sobre fondo claro
2D6A4F  bloque principal
40916C  bloque secundario
52B788  bloque terciario / acento
B7B7A4  neutro (el estado "antes")
FFFFFF  texto sobre bloque oscuro
```

Texto blanco sobre los tonos oscuros; texto oscuro sobre los claros.
