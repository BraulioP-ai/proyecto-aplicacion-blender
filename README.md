# Generador Procedural de Terrenos — Blender DSL

**Proyecto Final — Teoría de la Computación | UACH**

Aplicación que usa un lenguaje propio (DSL) para generar terrenos 3D en Blender mediante gramáticas formales. Escribes un código corto como `m(eee,c)` y el sistema genera automáticamente un script de Blender con el terreno.

---

## ¿Cómo funciona?

El flujo tiene tres etapas:

```
terreno.gic  →  metacompilador_terreno.py  →  parser_terreno.py  →  script de Blender
  (gramática)        (metacompilador)              (parser generado)      (.py ejecutado en Blender)
```

1. **`terreno.gic`** define la gramática del DSL (tipo Chomsky libre de contexto).
2. **`metacompilador_terreno.py`** lee la gramática y genera el archivo `parser_terreno.py`.
3. **`parser_terreno.py`** valida tu código de terreno y genera un script `.py` listo para Blender.
4. **Blender** ejecuta ese script y construye el terreno con ruido de Perlin, materiales y agua opcional.

### Gramática del DSL

```
S -> T(V,A)
T -> m | v | l        (Montana, Valle, Llanura)
V -> eE | e | sU | s  (Extrema o Suave, repetida para mayor intensidad)
A -> c | a            (Con agua, Árido)
```

### Ejemplos de códigos

| Código      | Significado                          |
|-------------|--------------------------------------|
| `m(e,c)`    | Montaña extrema con agua             |
| `m(eee,c)`  | Montaña muy extrema con agua         |
| `v(ss,a)`   | Valle suave árido                    |
| `l(s,c)`    | Llanura suave con agua               |

Cada letra extra en la variante (`ee`, `eee`, `ss`...) aumenta la intensidad del terreno en ±0.15.

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
2. Te pide que escribas un código de terreno.
3. Valida el código y genera el script de Blender.
4. Abre Blender directamente con el terreno generado.

Si Blender no se detecta automáticamente, el programa te indica el comando para abrirlo manualmente:

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
