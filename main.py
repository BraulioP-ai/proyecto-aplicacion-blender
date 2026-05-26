import os
import sys
import subprocess
import shutil

# =============================================================================
# GENERADOR PROCEDURAL DE TERRENOS — Punto de entrada principal
# Proyecto Final - Teoria de la Computacion (UACH)
#
# Uso: python main.py
# =============================================================================

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
GRAMATICA  = os.path.join(DIRECTORIO, "terreno.gic")
METACOMP   = os.path.join(DIRECTORIO, "metacompilador_terreno.py")
PARSER     = os.path.join(DIRECTORIO, "parser_terreno.py")
PYTHON     = sys.executable

BLENDER_PATHS = [
    r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
    "blender",
]

def encontrar_blender():
    # shutil.which busca en el PATH del sistema (la forma correcta en Linux)
    if shutil.which("blender"):
        return "blender"
        
    # Respaldo para Windows por si tu compa lo corre allá
    for ruta in BLENDER_PATHS:
        if os.path.isfile(ruta):
            return ruta
    return None

def encabezado():
    print("")
    print("=" * 52)
    print("   GENERADOR PROCEDURAL DE TERRENOS V3")
    print("   Teoria de la Computacion - UACH")
    print("=" * 52)
    print("   Gramatica del DSL:")
    print("     S -> T(R,A)")
    print("     T -> m | v | l | k | d         (Biomas)")
    print("     R -> E | U                     (Relieve)")
    print("     E -> eE | e                    (Extrema recursiva)")
    print("     U -> sU | s                    (Suave recursiva)")
    print("     A -> c | a                     (Con agua, Arido)")
    print("   Ejemplo: k(ee,a) = Canones Muy Extremos Aridos")
    print("=" * 52)

def paso1_generar_parser():
    if os.path.exists(PARSER):
        print("\n[1/3] Parser ya existe, omitiendo generacion.")
        return
    print("\n[1/3] Leyendo gramatica y generando parser...")
    resultado = subprocess.run(
        [PYTHON, METACOMP, GRAMATICA, PARSER],
        capture_output=True, text=True
    )
    if resultado.returncode != 0:
        print("    ERROR al generar el parser:")
        print(resultado.stderr)
        sys.exit(1)
    print(f"    Parser generado: {os.path.basename(PARSER)}")

def paso2_pedir_codigo():
    print("")
    print("[2/3] Ingresa el codigo de terreno.")
    print("      Formato : bioma(relieve,agua)")
    print("      bioma   : m=Montana  v=Valle  l=Llanura  k=Canones  d=Dunas")
    print("      relieve : e/ee/eee/... o s/ss/sss/...")
    print("      agua    : c=Con agua  a=Arido")
    print("      Nota    : d solo arido(a) | l solo suave(s)")
    print("      Ejemplos: m(e,c)  v(ss,a)  l(s,c)  k(ee,a)  d(e,a)")
    print("")
    while True:
        codigo = input("    Codigo: ").strip().replace(" ", "")
        if codigo:
            return codigo
        print("    Escribe un codigo valido.")

def paso3_ejecutar_parser(codigo):
    print("\n[3/3] Validando codigo y generando script de Blender...")
    resultado = subprocess.run(
        [PYTHON, PARSER],
        input=codigo,
        capture_output=True, text=True
    )
    salida = resultado.stdout
    
    # Filtramos la salida del parser para no imprimir el menu doble en la consola
    lineas_limpias = [linea for linea in salida.splitlines() if not ("Generador Procedural" in linea or "Formato:" in linea or "->" in linea or "Ejemplos :" in linea or "cada letra extra" in linea or "Nota:" in linea)]
    print("\n" + "\n".join(lineas_limpias).strip())

    if "invalido" in salida.lower():
        return None

    for linea in salida.splitlines():
        if "Archivo" in linea and ".py" in linea:
            return linea.split(":")[-1].strip()
    return None

def paso4_abrir_blender(nombre_script):
    ruta_script = os.path.join(DIRECTORIO, nombre_script)
    blender     = encontrar_blender()

    if not blender:
        print("=" * 52)
        print("  Blender no encontrado automaticamente.")
        print("  Corre manualmente:")
        print('  blender --python ' + ruta_script)
        print("=" * 52)
        return

    print("\nAbriendo Blender...")
    subprocess.run([blender, "--python", ruta_script])

def main():
    paso1_generar_parser()

    while True:
        encabezado()
        codigo        = paso2_pedir_codigo()
        nombre_script = paso3_ejecutar_parser(codigo)

        if nombre_script:
            paso4_abrir_blender(nombre_script)
            print("")
            otra = input("Generar otro terreno? (s/n): ").strip().lower()
            if otra != "s":
                break
        else:
            print("    Codigo invalido, intenta de nuevo.")

    print("\nProyecto terminado.")

if __name__ == "__main__":
    main()