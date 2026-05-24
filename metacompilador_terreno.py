import sys, os

# =============================================================================
# METACOMPILADOR DE TERRENOS
# Fork de compilador_gic.py (base del profe)
# Proyecto Final - Teoria de la Computacion (UACH)
#
# CAMBIOS respecto al original:
#   - La variable `programa` ahora incluye tablas de parametros semanticos
#     y la funcion generar_script_blender()
#   - La funcion parse() generada llama a generar_script_blender() al exito
#   - Todo lo demas (lexer, parser de gramatica, generador de funciones)
#     es identico al compilador base del profe
# =============================================================================

def main():
    if len(sys.argv) != 3:
        print("USO:", sys.argv[0], "entrada salida", file=sys.stderr)
        exit(1)
    global file
    try:
        file = open(sys.argv[1], "r")
    except Exception as e:
        print(str(e), file=sys.stderr)
        exit(1)
    else:
        parse()


# -----------------------------------------------------------------------------
# parse() — lee el archivo .gic y construye el programa generado
# MODIFICADO: la variable `programa` ahora contiene las acciones semanticas
# -----------------------------------------------------------------------------
def parse():
    global programa

    # --- INICIO DEL BLOQUE MODIFICADO ---
    # Este es el codigo que se inyecta al inicio del archivo generado.
    # Agrega las tablas semanticas y la funcion que genera el script de Blender.
    programa = """
# =============================================================
# Parser de Terrenos - generado por metacompilador_terreno.py
# =============================================================

# --- Tablas de acciones semanticas ---
# escala_ruido: frecuencia del ruido (menor = formas mas anchas y naturales)
# amplitud_base: altura maxima del terreno en unidades de Blender
BIOMA = {
    'm': ('Montana',  10.0, 0.20),
    'v': ('Valle',     3.5, 0.15),
    'l': ('Llanura',   1.2, 0.10),
}
VARIANTE = {
    'e': ('Extrema', 1.0),
    's': ('Suave',   0.8),
}
AGUA = {
    'c': ('Con Agua', True),
    'a': ('Arido',    False),
}

def generar_script_blender(bioma, variante, agua):
    nombre_bioma, amplitud_base, escala = BIOMA[bioma]
    nombre_agua,  tiene_agua            = AGUA[agua]

    # Calcular multiplicador segun la cantidad de letras en variante
    # Base 1.0, cada letra extra suma 0.15
    letra_v = variante[0]  # 'e' o 's'
    repeticiones = len(variante)
    if letra_v == 'e':
        nombre_var = 'Extrema'
        multiplicador = 1.0 + (repeticiones - 1) * 0.15
    else:
        nombre_var = 'Suave'
        multiplicador = 0.5 + (repeticiones - 1) * 0.10

    amplitud   = round(amplitud_base * multiplicador, 2)
    nivel_agua = round(amplitud * 0.35, 2)

    # El "suelo" es el agua si existe, si no z=0
    suelo = nivel_agua if tiene_agua else 0.0

    lineas = [
        "import bpy",
        "import mathutils",
        "import bmesh",
        "",
        "# ====================================",
        "# Terreno: " + nombre_bioma + " | " + nombre_var + " | " + nombre_agua,
        "# Codigo DSL: " + bioma + "(" + variante + "," + agua + ")",
        "# ====================================",
        "",
        "escala_ruido = " + str(escala),
        "amplitud     = " + str(amplitud),
        "suelo        = " + str(suelo),
        "",
        "# 1. Limpiar escena",
        "bpy.ops.object.select_all(action='SELECT')",
        "bpy.ops.object.delete()",
        "",
        "# 2. Crear malla del terreno (plano subdividido)",
        "bpy.ops.mesh.primitive_plane_add(size=20)",
        "bpy.ops.object.mode_set(mode='EDIT')",
        "bpy.ops.mesh.subdivide(number_cuts=150)",
        "bpy.ops.object.mode_set(mode='OBJECT')",
        "",
        "# 3. Deformar con Ruido de Perlin (normalizado a [0, amplitud])",
        "obj = bpy.context.active_object",
        "for v in obj.data.vertices:",
        "    x = v.co.x * escala_ruido",
        "    y = v.co.y * escala_ruido",
        "    valor = mathutils.noise.noise(mathutils.Vector((x, y, 0.0)))",
        "    v.co.z = max(suelo, ((valor + 1.0) / 2.0) * amplitud)",
        "",
        "# 4. Extruir bordes del terreno hacia abajo hasta el nivel del suelo",
        "# Los vertices en el borde (abs(x)>9.85 o abs(y)>9.85) se extruden",
        "# creando paredes que siguen el contorno exacto de las montanas.",
        "bm = bmesh.new()",
        "bm.from_mesh(obj.data)",
        "bm.verts.ensure_lookup_table()",
        "bm.edges.ensure_lookup_table()",
        "borde = {v.index for v in bm.verts if abs(v.co.x) > 9.85 or abs(v.co.y) > 9.85}",
        "v_map = {}",
        "for v in bm.verts:",
        "    if v.index in borde:",
        "        nv = bm.verts.new((v.co.x, v.co.y, suelo))",
        "        v_map[v.index] = nv",
        "bm.verts.ensure_lookup_table()",
        "for edge in bm.edges:",
        "    i1, i2 = edge.verts[0].index, edge.verts[1].index",
        "    if i1 in borde and i2 in borde and i1 in v_map and i2 in v_map:",
        "        try:",
        "            bm.faces.new([edge.verts[0], v_map[i1], v_map[i2], edge.verts[1]])",
        "        except: pass",
        "bm.to_mesh(obj.data)",
        "bm.free()",
        "obj.data.update()",
        "",
        "bpy.ops.object.shade_smooth()",
        "",
        "# 5. Material del terreno",
        "mat = bpy.data.materials.new(name='Terreno')",
        "mat.use_nodes = True",
        "bsdf = mat.node_tree.nodes.get('Principled BSDF')",
        "if bsdf:",
        "    bsdf.inputs['Base Color'].default_value = (0.50, 0.48, 0.45, 1.0)",
        "    bsdf.inputs['Roughness'].default_value = 0.9",
        "obj.data.materials.append(mat)",
    ]

    if tiene_agua:
        lineas += [
            "",
            "# 6. Plano de agua (es el suelo del mundo)",
            "nivel_agua = " + str(nivel_agua),
            "bpy.ops.mesh.primitive_plane_add(size=19.9, location=(0, 0, nivel_agua + 0.05))",
            "mat_agua = bpy.data.materials.new(name='Agua')",
            "mat_agua.use_nodes = True",
            "bsdf_agua = mat_agua.node_tree.nodes.get('Principled BSDF')",
            "if bsdf_agua:",
            "    bsdf_agua.inputs['Base Color'].default_value = (0.04, 0.22, 0.50, 1.0)",
            "    bsdf_agua.inputs['Roughness'].default_value = 0.3",
            "bpy.context.active_object.data.materials.append(mat_agua)",
            "bpy.context.scene.world = None",
        ]

    nombre_archivo = "terreno_" + bioma + variante + agua + ".py"
    with open(nombre_archivo, "w") as f:
        f.write("\\n".join(lineas))

    print("")
    print("=" * 48)
    print("  Script de Blender generado exitosamente")
    print("=" * 48)
    print("  Bioma    : " + nombre_bioma)
    print("  Variante : " + nombre_var)
    print("  Agua     : " + nombre_agua)
    print("  Amplitud : " + str(round(amplitud, 2)))
    print("  Escala   : " + str(escala))
    print("  Archivo  : " + nombre_archivo)
    print("=" * 48)
    print("  Ejecuta con:")
    print("  blender --python " + nombre_archivo)
    print("=" * 48)

def main():
    global w
    global p
    print("")
    print("  Generador Procedural de Terrenos")
    print("  Formato: bioma(variante,agua)")
    print("    bioma   -> m=Montana  v=Valle  l=Llanura")
    print("    variante-> e/ee/eee=Extrema  s/ss/sss=Suave")
    print("               cada letra extra suma intensidad (+0.15)")
    print("    agua    -> c=Con agua  a=Arido")
    print("  Ejemplos : m(e,c)   m(eee,c)   v(ss,a)   l(s,c)")
    print("")
    w = input("Codigo de terreno: ")
    w = w.replace(" ", "")
    w += "\\n"
    p = 0
    parse()

def parse():
    if S() and w[p] == "\\n":
        print("Codigo valido.")
        # Extraer componentes: bioma=w[0], variante=entre '(' y ',', agua=entre ',' y ')'
        bioma = w[0]
        inicio_v = 2                          # despues del '('
        fin_v = w.index(',', inicio_v)
        variante = w[inicio_v:fin_v]          # puede ser 'e', 'ee', 'eee', 's', 'ss'...
        inicio_a = fin_v + 1
        fin_a = w.index(')', inicio_a)
        agua = w[inicio_a:fin_a]
        generar_script_blender(bioma, variante, agua)
    else:
        print("Codigo invalido. Formato esperado: [m/v/l]([e.../s...],[c/a])")

"""
    # --- FIN DEL BLOQUE MODIFICADO ---

    result = S(1)
    file.close()
    if result:
        print("Ok")
        programa += "main()"
        with open(sys.argv[2], "w") as salida:
            salida.write(programa)
        os.system("python3 " + sys.argv[2])
        exit(0)
    else:
        print("Fail")
        exit(1)


# =============================================================================
# TODO LO SIGUIENTE ES IDENTICO AL COMPILADOR BASE DEL PROFE
# =============================================================================

def S(i: int) -> bool:
    return PS(i)

def PS(i: int) -> bool:
    if(P(i)): return P1(i)
    return False

def P1(i: int) -> bool:
    token = next_token()
    if token['type'] == 'endl':
        token = next_token()
        unget_token(token)
        if token['type'] == 'n': return PS(i)
        return True
    elif token['type'] == 'endf': return True
    else:
        unget_token(token)
        return False

def P(i: int) -> bool:
    global programa
    token = next_token()
    if token['type'] == 'n':
        token2 = next_token()
        if token2['type'] == 'f':
            programa += """
def """ + token['lexema'] + """() -> bool:
    global p
"""
            if DS(i):
                programa += """
    return False
"""
                return True
    unget_token(token)
    return False

def DS(i: int) -> bool:
    if (D(i)): return D1(i)
    return False

def D1(i: int) -> bool:
    token = next_token()
    if token['type'] == 'o':
        return DS(i)
    unget_token(token)
    return True

def D(i: int) -> bool:
    global programa
    token = next_token()
    if token['type'] == 'n':
        programa += "    "*i + "t"+str(i)+" = p\n"
        programa += "    "*i + "if " + token['lexema']+"():\n"
        token = next_token()
        unget_token(token)
        if token['type'] in ['n', 't', 'e']:
            if D(i+1):
                programa += "    "*i + "p = t"+str(i)+"\n"
                return True
        programa += "    "*(i+1) + "return True\n"
        programa += "    "*i + "p = t"+str(i)+"\n"
        return True
    if token['type'] == 't':
        programa += "    "*i + "t"+str(i)+" = p\n"
        programa += "    "*i + "c = w[p]\n"
        programa += "    "*i + "p += 1\n"
        programa += "    "*i + "if c == '" + token['lexema']+"':\n"
        token = next_token()
        unget_token(token)
        if token['type'] in ['n', 't', 'e']:
            if D(i+1):
                programa += "    "*i + "p = t"+str(i)+"\n"
                return True
        programa += "    "*(i+1) + "return True\n"
        programa += "    "*i + "p = t"+str(i)+"\n"
        return True
    if token['type'] == 'e':
        programa += "    "*i + "p = t"+str(i)+"\n"
        programa += "    "*i + "return True\n"
        return True
    unget_token(token)
    return False

def next_token():
    global file
    matrix = []
    #.            '',L,l,|,?,-,\,>,*
    matrix.append([0,1,2,3,4,5,7,8,8])
    matrix.append([8,8,8,8,8,8,8,8,8])
    matrix.append([8,8,8,8,8,8,8,8,8])
    matrix.append([8,8,8,8,8,8,8,8,8])
    matrix.append([8,8,8,8,8,8,8,8,8])
    matrix.append([9,9,9,9,9,9,9,6,9])
    matrix.append([8,8,8,8,8,8,8,8,8])
    matrix.append([8,8,8,8,8,8,8,8,8])
    matrix.append([8,8,8,8,8,8,8,8,8])
    matrix.append([8,8,8,8,8,8,8,8,8])
    q = 0
    lexema = ""
    while True:
        try:
            p = file.tell()
            c = file.read(1)
        except:
            return {'type': 'endf', 'lexema': '\0', 'position': p}
        else:
            if c == '?':
                lexema += c
                q = matrix[q][4]
            elif c == '|':
                lexema += c
                q = matrix[q][3]
            elif c == '-':
                lexema += c
                q = matrix[q][5]
            elif c == '\n':
                lexema += c
                q = matrix[q][6]
            elif c == '>':
                lexema += c
                q = matrix[q][7]
            elif c.isspace():
                q = matrix[q][0]
            elif c.isupper():
                lexema += c
                q = matrix[q][1]
            elif c.islower() or c.isprintable():
                lexema += c
                q = matrix[q][2]
            elif c == '':
                return {'type': 'endf', 'lexema': lexema, 'position': p}
            else:
                q = matrix[q][8]

            if q == 1: return {'type': 'n', 'lexema': lexema, 'position': p}
            elif q == 2: return {'type': 't', 'lexema': lexema, 'position': p}
            elif q == 3: return {'type': 'o', 'lexema': lexema, 'position': p}
            elif q == 4: return {'type': 'e', 'lexema': lexema, 'position': p}
            elif q == 6: return {'type': 'f', 'lexema': lexema, 'position': p}
            elif q == 7: return {'type': 'endl', 'lexema': lexema, 'position': p}
            elif q == 8: return {'type': 'error', 'lexema': lexema, 'position': p}
            elif q == 9:
                p -= 1
                return {'type': 't', 'lexema': lexema.removesuffix(c), 'position': p}

def unget_token(token: dict):
    global file
    file.seek(token['position'], 0)

if __name__ == "__main__": main()
