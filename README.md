# Generador Procedural de Terrenos — Blender DSL

**Proyecto Final — Teoría de la Computación | UACH**

Aplicación que usa un lenguaje propio (DSL) para generar terrenos 3D en Blender mediante gramáticas formales. Escribes un código corto como `k(ee,a)` y el sistema genera automáticamente un script de Blender con el terreno.

---

## ¿Cómo funciona?

El flujo tiene tres etapas:

    terreno.gic  →  metacompilador_terreno.py  →  parser_terreno.py  →  script de Blender
      (gramática)        (metacompilador)              (parser generado)      (.py ejecutado en Blender)

1. **`terreno.gic`** define la gramática del DSL (tipo Chomsky libre de contexto).
2. **`metacompilador_terreno.py`** lee la gramática y genera el archivo `parser_terreno.py`.
3. **`parser_terreno.py`** valida tu código de terreno (sintáctica y semánticamente) y genera un script `.py` listo para Blender.
4. **Blender** ejecuta ese script y construye el terreno con geometría avanzada (BMesh), materiales dinámicos y agua procedural.

### Gramática del DSL

    S -> T(R,A)
    T -> m | v | l | k | d          (Montaña, Valle, Llanura, Cañones, Dunas)
    R -> E | U                      (Relieve)
    E -> eE | e                     (Extrema recursiva)
    U -> sU | s                     (Suave recursiva)
    A -> c | a                      (Con agua, Arido)

**Nota Semántica:** El parser incluye validaciones lógicas según el bioma. Por ejemplo, la Llanura (`l`) solo admite relieve suave (`s`), y las Dunas (`d`) solo admiten terreno árido (`a`).

### Ejemplos de códigos

| Código      | Significado                          |
|-------------|--------------------------------------|
| `m(e,c)`    | Montaña extrema con agua             |
| `k(ee,a)`   | Cañones muy extremos áridos          |
| `v(ss,a)`   | Valle muy suave árido                |
| `l(s,c)`    | Llanura suave con agua               |
| `d(e,a)`    | Dunas extremas áridas                |

Cada letra extra en la variante (`ee`, `eee`, `ss`...) aumenta o disminuye la intensidad del relieve (multiplicador acumulativo sobre la amplitud base).

---

## Requisitos

- Python 3.8+
- [Blender](https://www.blender.org/download/) instalado (versión 4.0 o superior recomendada)

No se requieren librerías externas de Python.

---

## Cómo correrlo

```bash
python main.py
```

El programa te guía paso a paso:

1. Genera el parser automáticamente desde la gramática.
2. Te muestra la especificación del lenguaje y te pide que escribas un código de terreno.
3. Valida el código y genera el script de Blender.
4. Abre Blender directamente con el terreno generado en modo Material para su visualización.

Si Blender no se detecta automáticamente, el programa te indica el comando para abrirlo manualmente, por ejemplo:

```bash
blender --python terreno_meec.py
```

---

## Archivos del proyecto

| Archivo                     | Descripción                                              |
|-----------------------------|----------------------------------------------------------|
| `main.py`                   | Punto de entrada, orquesta todo el flujo                 |
| `terreno.gic`               | Gramática formal del DSL                                 |
| `metacompilador_terreno.py` | Lee la gramática y genera el parser                      |
| `parser_terreno.py`         | Generado automáticamente, valida y produce scripts       |
| `terreno_*.py`              | Scripts de Blender generados (uno por terreno)           |