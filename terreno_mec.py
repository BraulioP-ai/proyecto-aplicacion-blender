import bpy
import mathutils
import bmesh
import math

# ====================================
# Terreno: Montana | Extrema | Con Agua
# Codigo DSL: m(e,c)
# ====================================

escala_ruido = 0.2
amplitud     = 10.0
suelo        = 4.5

# 1. Limpiar escena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 2. Crear malla del terreno (plano subdividido)
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=150)
bpy.ops.object.mode_set(mode='OBJECT')

obj = bpy.context.active_object
# 3. Montana extrema: Perlin directo con picos escarpados
for v in obj.data.vertices:
    x = v.co.x * escala_ruido
    y = v.co.y * escala_ruido
    valor = mathutils.noise.noise(mathutils.Vector((x, y, 0.0)))
    norm = (valor + 1.0) / 2.0
    v.co.z = max(suelo, (norm ** 1.4) * amplitud)

# 4. Extruir bordes hacia abajo
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
borde = {v.index for v in bm.verts if abs(v.co.x) > 9.85 or abs(v.co.y) > 9.85}
v_map = {}
for v in bm.verts:
    if v.index in borde:
        nv = bm.verts.new((v.co.x, v.co.y, suelo))
        v_map[v.index] = nv
bm.verts.ensure_lookup_table()
for edge in bm.edges:
    i1, i2 = edge.verts[0].index, edge.verts[1].index
    if i1 in borde and i2 in borde and i1 in v_map and i2 in v_map:
        try:
            bm.faces.new([edge.verts[0], v_map[i1], v_map[i2], edge.verts[1]])
        except: pass
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

bpy.ops.object.shade_smooth()

# 5. Material del terreno (Paleta Minecraft)
mat = bpy.data.materials.new(name='Terreno')
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.072, 0.068, 0.068, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.9
obj.data.materials.append(mat)

# 6. Plano de agua estatico (Montanas)
nivel_agua = 4.5
bpy.ops.mesh.primitive_plane_add(size=19.9, location=(0, 0, nivel_agua + 0.05))
mat_agua = bpy.data.materials.new(name='Agua')
mat_agua.use_nodes = True
bsdf_agua = mat_agua.node_tree.nodes.get('Principled BSDF')
if bsdf_agua:
    bsdf_agua.inputs['Base Color'].default_value = (0.04, 0.22, 0.50, 1.0)
    bsdf_agua.inputs['Roughness'].default_value = 0.3
bpy.context.active_object.data.materials.append(mat_agua)
bpy.context.scene.world = None

# 7. Forzar vista a Modo Material
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'