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
