import sys, os

# =============================================================================
# METACOMPILADOR DE TERRENOS v2
# Fork de compilador_gic.py (base del profe)
# Proyecto Final - Teoria de la Computacion (UACH)
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


def parse():
    global programa

    programa = """
# =============================================================
# Parser de Terrenos v2 - generado por metacompilador_terreno.py
# =============================================================

BIOMA = {
    'm': ('Montana',  10.0, 0.20),
    'v': ('Valle',     3.5, 0.15),
    'l': ('Llanura',   4.0, 0.25),
    'k': ('Canones',  10.0, 0.18),
    'd': ('Dunas',     2.0, 0.00),
}
AGUA = {
    'c': ('Con Agua', True),
    'a': ('Arido',    False),
}

# Biomas que no admiten agua
SIN_AGUA = {'d'}
# Biomas que no admiten variante extrema
SOLO_SUAVE = {'l'}

def generar_script_blender(bioma, variante, agua):
    nombre_bioma, amplitud_base, escala = BIOMA[bioma]
    nombre_agua,  tiene_agua            = AGUA[agua]

    letra_v      = variante[0]
    repeticiones = len(variante)
    if letra_v == 'e':
        nombre_var    = 'Extrema'
        multiplicador = 1.0 + (repeticiones - 1) * 0.15
    else:
        nombre_var    = 'Suave'
        multiplicador = max(0.1, 0.5 - (repeticiones - 1) * 0.10)

    amplitud   = round(amplitud_base * multiplicador, 2)

    # Canones: el modificador s no debe reducir tanto la altura
    if bioma == 'k' and letra_v == 's':
        amplitud = round(amplitud_base * max(0.75, multiplicador), 2)
    # Llanura: siempre tiene algo de ondulacion, nunca perfectamente plana
    if bioma == 'l':
        amplitud = round(max(1.8, amplitud), 2)

    nivel_agua = round(amplitud * 0.45, 2)
    suelo      = nivel_agua if tiene_agua else 0.0

    # Parametros de valle
    ALTURA_MONTANA_VALLE = 15.0 if letra_v == 'e' else 8.0
    inicio_m = 0.15 if letra_v == 'e' else 0.50
    rango_m  = round(1.0 - inicio_m, 2)

    lineas = [
        "import bpy",
        "import mathutils",
        "import bmesh",
        "import math",
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
        "obj = bpy.context.active_object",
    ]

    # ------------------------------------------------------------------ VALLE
    if bioma == 'v':
        lineas += [
            "# 3. Valle: piso plano + montanas en anillo exterior",
            "altura_montana = " + str(ALTURA_MONTANA_VALLE),
            "for v in obj.data.vertices:",
            "    x = v.co.x",
            "    y = v.co.y",
            "    dist = min(math.sqrt(x*x + y*y) / 10.0, 1.0)",
            "    nx = x * escala_ruido",
            "    ny = y * escala_ruido",
            "    piso = suelo",
            "    factor_m = max(0.0, (dist - " + str(inicio_m) + ") / " + str(rango_m) + ") ** 1.6",
            "    r1 = (mathutils.noise.noise(mathutils.Vector((nx*0.8, ny*0.8, 5.0))) + 1.0) / 2.0",
            "    r2 = (mathutils.noise.noise(mathutils.Vector((nx*2.5, ny*2.5, 9.0))) + 1.0) / 2.0",
            "    montana = (r1*0.7 + r2*0.3) * altura_montana * factor_m",
            "    v.co.z = max(suelo, piso + montana)",
        ]

    # --------------------------------------------------------------- LLANURA
    elif bioma == 'l':
        nivel_rio_baked = round(suelo + 0.08, 2)
        lineas += [
            "# 3. Llanura: Perlin suave + canal del rio tallado",
            "for v in obj.data.vertices:",
            "    x = v.co.x * escala_ruido",
            "    y = v.co.y * escala_ruido",
            "    valor = mathutils.noise.noise(mathutils.Vector((x, y, 0.0)))",
            "    v.co.z = max(suelo, ((valor + 1.0) / 2.0) * amplitud)",
        ]
        if tiene_agua:
            lineas += [
                "# Tallar canal del rio",
                "import math as _math2",
                "ancho_canal = 2.2",
                "nivel_canal = " + str(nivel_rio_baked),
                "for v in obj.data.vertices:",
                "    t_c = max(0.0, min(1.0, (v.co.y + 10.0) / 20.0))",
                "    x_rio_c = 2.5 * _math2.sin(t_c * _math2.pi * 2.0) + 1.0 * _math2.sin(t_c * _math2.pi * 5.0)",
                "    d_rio = abs(v.co.x - x_rio_c)",
                "    if d_rio < ancho_canal:",
                "        blend = (1.0 - (d_rio / ancho_canal) ** 2)",
                "        v.co.z = min(v.co.z, nivel_canal - 0.08 * blend)",
                "obj.data.update()",
            ]

    # --------------------------------------------------------------- CANONES
    elif bioma == 'k':
        # e = canon estrecho con paredes mas texturizadas
        # s = canon ancho con paredes mas suaves
        ancho_canon = 3.5 if letra_v == 'e' else 6.0
        detalle_pared = 0.55 if letra_v == 'e' else 0.20
        lineas += [
            "# 3. Canon: plateau rocoso con corte e irregular por el centro",
            "ancho_canon = " + str(ancho_canon),
            "detalle_pared = " + str(detalle_pared),
            "for v in obj.data.vertices:",
            "    x = v.co.x",
            "    y = v.co.y",
            "    # Plateau con doble capa de ruido para textura rocosa",
            "    rb1 = (mathutils.noise.noise(mathutils.Vector((x*0.18, y*0.18, 0.0))) + 1.0) / 2.0",
            "    rb2 = (mathutils.noise.noise(mathutils.Vector((x*0.50, y*0.50, 5.0))) + 1.0) / 2.0",
            "    base = amplitud * (0.60 + 0.28 * rb1 + 0.12 * rb2)",
            "    # Canon con camino ligeramente sinuoso",
            "    warp = mathutils.noise.noise(mathutils.Vector((y*0.15, 0.0, 8.0))) * 1.8",
            "    x_c = x + warp",
            "    var_w = 1.0 + mathutils.noise.noise(mathutils.Vector((y*0.22, 0.0, 3.0))) * 0.30",
            "    ancho_local = ancho_canon * var_w",
            "    dist_c = abs(x_c)",
            "    if dist_c < ancho_local:",
            "        t = 1.0 - (dist_c / ancho_local)",
            "        # Detalle de pared: e=mas rugoso, s=mas liso",
            "        pared_n = (mathutils.noise.noise(mathutils.Vector((x*0.6, y*0.5, 2.0))) + 1.0) / 2.0",
            "        profundidad = (t ** 1.2) * amplitud * 0.84 * (1.0 - detalle_pared + detalle_pared * pared_n)",
            "        v.co.z = max(suelo, base - profundidad)",
            "    else:",
            "        v.co.z = max(suelo, base)",
        ]

    # --------------------------------------------------------------- DUNAS
    elif bioma == 'd':
        # e = dunas mas altas y separadas (desierto de arena profundo)
        # s = dunas bajas y muy suaves (zona costera o desierto joven)
        frec_duna  = 0.45 if letra_v == 'e' else 0.65
        frec_duna2 = 0.75 if letra_v == 'e' else 1.10
        lineas += [
            "# 3. Dunas: seno con domain warping, forma segun variante",
            "frec1 = " + str(frec_duna),
            "frec2 = " + str(frec_duna2),
            "for v in obj.data.vertices:",
            "    x = v.co.x",
            "    y = v.co.y",
            "    warp1 = mathutils.noise.noise(mathutils.Vector((y * 0.12, 0.0, 1.0))) * 4.5",
            "    warp2 = mathutils.noise.noise(mathutils.Vector((y * 0.07, x * 0.04, 4.0))) * 2.0",
            "    x_w1 = x + warp1",
            "    onda1 = math.sin(x_w1 * frec1 * math.pi) * 0.5 + 0.5",
            "    x_w2 = x + warp2",
            "    onda2 = math.sin(x_w2 * frec2 * math.pi + 1.9) * 0.5 + 0.5",
            "    mod_h = (mathutils.noise.noise(mathutils.Vector((x * 0.06, y * 0.06, 8.0))) + 1.0) / 2.0",
            "    onda_final = onda1 * 0.60 + onda2 * 0.40",
            "    altura = onda_final * amplitud * (0.45 + 0.55 * mod_h)",
            "    v.co.z = max(suelo, altura)",
        ]

    # --------------------------------------------------------------- MONTANA
    else:
        if letra_v == 'e':
            # Montana extrema: Perlin directo, picos agudos y escarpados
            lineas += [
                "# 3. Montana extrema: Perlin directo con picos agudos",
                "for v in obj.data.vertices:",
                "    x = v.co.x * escala_ruido",
                "    y = v.co.y * escala_ruido",
                "    valor = mathutils.noise.noise(mathutils.Vector((x, y, 0.0)))",
                "    norm = (valor + 1.0) / 2.0",
                "    # Exponente > 1 acentua los picos y profundiza los valles",
                "    v.co.z = max(suelo, (norm ** 1.4) * amplitud)",
            ]
        else:
            # Montana suave: cimas redondeadas (montana antigua/erosionada)
            lineas += [
                "# 3. Montana suave: cimas redondeadas como montana erosionada",
                "for v in obj.data.vertices:",
                "    x = v.co.x * escala_ruido",
                "    y = v.co.y * escala_ruido",
                "    valor = mathutils.noise.noise(mathutils.Vector((x, y, 0.0)))",
                "    norm = (valor + 1.0) / 2.0",
                "    # Exponente < 1 aplana las cimas y suaviza la forma",
                "    v.co.z = max(suelo, (norm ** 0.60) * amplitud)",
            ]

    # ----------------------------------------------- BORDES Y MATERIAL (TODOS)
    lineas += [
        "",
        "# 4. Extruir bordes hacia abajo",
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

    # ----------------------------------------------------------- AGUA / BIOMA
    if tiene_agua:
        if bioma == 'k':
            nivel_rio_k = round(suelo + 0.20, 2)
            lineas += [
                "",
                "# 6. Rio en el fondo del canon",
                "nivel_rio_k = " + str(nivel_rio_k),  # encima del piso del canon
                "import math as _mk",
                "verts_rk = []",
                "faces_rk = []",
                "pasos_k = 60",
                "ancho_k = 0.6",
                "for i in range(pasos_k + 1):",
                "    t = i / pasos_k",
                "    y = -10.0 + t * 20.0",
                "    # El rio sigue el mismo warp sinuoso del canon",
                "    warp_r = mathutils.noise.noise(mathutils.Vector((y*0.15, 0.0, 8.0))) * 1.8",
                "    x_c = 0.0 - warp_r",  # negativo para seguir el centro real del canon
                "    verts_rk.append((x_c - ancho_k, y, nivel_rio_k))",
                "    verts_rk.append((x_c + ancho_k, y, nivel_rio_k))",
                "for i in range(pasos_k):",
                "    b = i * 2",
                "    faces_rk.append((b, b+1, b+3, b+2))",
                "mesh_rk = bpy.data.meshes.new('RioCanon')",
                "mesh_rk.from_pydata(verts_rk, [], faces_rk)",
                "mesh_rk.update()",
                "obj_rk = bpy.data.objects.new('RioCanon', mesh_rk)",
                "bpy.context.collection.objects.link(obj_rk)",
                "mat_rk = bpy.data.materials.new(name='RioCanon')",
                "mat_rk.use_nodes = True",
                "bsdf_rk = mat_rk.node_tree.nodes.get('Principled BSDF')",
                "if bsdf_rk:",
                "    bsdf_rk.inputs['Base Color'].default_value = (0.04, 0.25, 0.55, 1.0)",
                "    bsdf_rk.inputs['Roughness'].default_value = 0.4",
                "obj_rk.data.materials.append(mat_rk)",
            ]
        elif bioma == 'v' and letra_v == 'e':
            # Valle extremo con agua: rio estrecho en el fondo (no lago)
            nivel_rio_v = round(suelo + 0.20, 2)
            lineas += [
                "",
                "# 6. Rio en el fondo del valle estrecho",
                "nivel_rio_v = " + str(nivel_rio_v),
                "import math as _mv",
                "verts_rv = []",
                "faces_rv = []",
                "pasos_v = 50",
                "ancho_v = 0.8",
                "for i in range(pasos_v + 1):",
                "    t = i / pasos_v",
                "    y = -10.0 + t * 20.0",
                "    x_c = 0.8 * _mv.sin(t * _mv.pi * 1.5)",
                "    verts_rv.append((x_c - ancho_v, y, nivel_rio_v))",
                "    verts_rv.append((x_c + ancho_v, y, nivel_rio_v))",
                "for i in range(pasos_v):",
                "    b = i * 2",
                "    faces_rv.append((b, b+1, b+3, b+2))",
                "mesh_rv = bpy.data.meshes.new('RioValle')",
                "mesh_rv.from_pydata(verts_rv, [], faces_rv)",
                "mesh_rv.update()",
                "obj_rv = bpy.data.objects.new('RioValle', mesh_rv)",
                "bpy.context.collection.objects.link(obj_rv)",
                "mat_rv = bpy.data.materials.new(name='RioValle')",
                "mat_rv.use_nodes = True",
                "bsdf_rv = mat_rv.node_tree.nodes.get('Principled BSDF')",
                "if bsdf_rv:",
                "    bsdf_rv.inputs['Base Color'].default_value = (0.04, 0.25, 0.55, 1.0)",
                "    bsdf_rv.inputs['Roughness'].default_value = 0.4",
                "obj_rv.data.materials.append(mat_rv)",
            ]
        elif bioma == 'v':
            nivel_lago = round(suelo + 0.30, 2)
            lineas += [
                "",
                "# 6. Lago irregular en el centro del valle",
                "nivel_lago = " + str(nivel_lago),
                "bpy.ops.mesh.primitive_circle_add(vertices=48, radius=3.2, fill_type='TRIFAN', location=(0, 0, nivel_lago))",
                "lago_obj = bpy.context.active_object",
                "bpy.ops.object.mode_set(mode='EDIT')",
                "bpy.ops.mesh.subdivide(number_cuts=3)",
                "bpy.ops.object.mode_set(mode='OBJECT')",
                "for lv in lago_obj.data.vertices:",
                "    dist_lv = math.sqrt(lv.co.x**2 + lv.co.y**2)",
                "    if dist_lv > 0.1:",
                "        ang = math.atan2(lv.co.y, lv.co.x)",
                "        r1 = mathutils.noise.noise(mathutils.Vector((math.cos(ang)*2.0, math.sin(ang)*2.0, 7.0)))",
                "        r2 = mathutils.noise.noise(mathutils.Vector((math.cos(ang)*5.0, math.sin(ang)*5.0, 11.0)))",
                "        escala_lago = 1.0 + (r1*0.7 + r2*0.3) * 0.45 * (dist_lv / 3.2)",
                "        lv.co.x *= escala_lago",
                "        lv.co.y *= escala_lago",
                "lago_obj.data.update()",
                "mat_lago = bpy.data.materials.new(name='Lago')",
                "mat_lago.use_nodes = True",
                "bsdf_lago = mat_lago.node_tree.nodes.get('Principled BSDF')",
                "if bsdf_lago:",
                "    bsdf_lago.inputs['Base Color'].default_value = (0.04, 0.20, 0.55, 1.0)",
                "    bsdf_lago.inputs['Roughness'].default_value = 0.6",
                "lago_obj.data.materials.append(mat_lago)",
            ]
        elif bioma == 'l':
            nivel_rio = round(suelo + 0.08, 2)
            lineas += [
                "",
                "# 6. Rio sinusoidal que cruza la llanura",
                "nivel_rio = " + str(nivel_rio),
                "import math as _math",
                "verts_rio = []",
                "faces_rio = []",
                "pasos = 60",
                "ancho = 1.0",
                "for i in range(pasos + 1):",
                "    t = i / pasos",
                "    y = -10.0 + t * 20.0",
                "    x_c = 2.5 * _math.sin(t * _math.pi * 2.0) + 1.0 * _math.sin(t * _math.pi * 5.0)",
                "    verts_rio.append((x_c - ancho, y, nivel_rio))",
                "    verts_rio.append((x_c + ancho, y, nivel_rio))",
                "for i in range(pasos):",
                "    b = i * 2",
                "    faces_rio.append((b, b+1, b+3, b+2))",
                "mesh_rio = bpy.data.meshes.new('Rio')",
                "mesh_rio.from_pydata(verts_rio, [], faces_rio)",
                "mesh_rio.update()",
                "obj_rio = bpy.data.objects.new('Rio', mesh_rio)",
                "bpy.context.collection.objects.link(obj_rio)",
                "mat_rio = bpy.data.materials.new(name='Rio')",
                "mat_rio.use_nodes = True",
                "bsdf_rio = mat_rio.node_tree.nodes.get('Principled BSDF')",
                "if bsdf_rio:",
                "    bsdf_rio.inputs['Base Color'].default_value = (0.04, 0.25, 0.55, 1.0)",
                "    bsdf_rio.inputs['Roughness'].default_value = 0.5",
                "obj_rio.data.materials.append(mat_rio)",
            ]
        else:
            # Montana y Colinas con agua: plano completo
            lineas += [
                "",
                "# 6. Plano de agua",
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
    print("=" * 52)
    print("  Script de Blender generado exitosamente")
    print("=" * 52)
    print("  Bioma    : " + nombre_bioma)
    print("  Variante : " + nombre_var)
    print("  Agua     : " + nombre_agua)
    print("  Amplitud : " + str(round(amplitud, 2)))
    print("  Escala   : " + str(escala))
    print("  Archivo  : " + nombre_archivo)
    print("=" * 52)
    print("  Ejecuta con:")
    print("  blender --python " + nombre_archivo)
    print("=" * 52)

def main():
    global w
    global p
    print("")
    print("  Generador Procedural de Terrenos v2")
    print("  Formato: bioma(relieve,agua)")
    print("    bioma   -> m=Montana  v=Valle   l=Llanura")
    print("               h=Colinas  k=Canones p=Meseta  d=Dunas")
    print("    relieve -> e/ee/eee=Extrema  s/ss/sss=Suave")
    print("    agua    -> c=Con agua  a=Arido")
    print("  Nota: d solo admite arido (a)")
    print("        l solo admite relieve suave (s)")
    print("  Ejemplos: m(e,c)  v(ss,a)  l(s,c)  k(ee,a)  d(e,a)")
    print("")
    w = input("Codigo de terreno: ")
    w = w.replace(" ", "")
    w += "\\n"
    p = 0
    parse()

def parse():
    if S() and w[p] == "\\n":
        print("Codigo valido.")
        bioma    = w[0]
        inicio_v = 2
        fin_v    = w.index(',', inicio_v)
        variante = w[inicio_v:fin_v]
        inicio_a = fin_v + 1
        fin_a    = w.index(')', inicio_a)
        agua     = w[inicio_a:fin_a]

        # --- Validaciones semanticas ---
        letra_v      = variante[0]
        repeticiones = len(variante)
        if bioma == 'l' and letra_v == 'e':
            print("")
            print("Error semantico: Llanura (l) solo admite relieve suave (s).")
            print("Una llanura es por definicion un terreno plano.")
            return
        if bioma in SIN_AGUA and agua == 'c':
            nombres = {'d': 'Dunas'}
            print("")
            print("Error semantico: " + nombres[bioma] + " no admite agua (c).")
            print("Este bioma se presenta en zonas aridas. Usa (a) en vez de (c).")
            return
        if bioma == 'm' and letra_v == 's' and repeticiones > 2:
            print("")
            print("Error semantico: Montana (m) admite maximo ss en variante suave.")
            print("Con mas de ss el terreno pierde las caracteristicas de una montana.")
            print("Usa m(s,?) o m(ss,?) para montanas suaves/antiguas.")
            return
        if bioma == 'd' and letra_v == 'e' and repeticiones > 1:
            print("")
            print("Error semantico: Dunas (d) admite maximo e simple en variante extrema.")
            print("Las dunas son por definicion de baja altura y formas suaves.")
            print("Usa d(e,a) o d(s,a) o d(ss,a).")
            return

        generar_script_blender(bioma, variante, agua)
    else:
        print("Codigo invalido. Formato esperado: [m/v/l/k/d]([e.../s...],[c/a])")

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