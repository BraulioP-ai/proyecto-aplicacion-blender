import bpy
import mathutils
import bmesh

# ====================================
# Terreno: Valle | Suave | Arido
# Codigo DSL: v(ss,a)
# ====================================

escala_ruido = 0.15
amplitud     = 2.1
suelo        = 0.0

# 1. Limpiar escena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 2. Crear malla del terreno (plano subdividido)
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=150)
bpy.ops.object.mode_set(mode='OBJECT')

# 3. Deformar con Ruido de Perlin (normalizado a [0, amplitud])
obj = bpy.context.active_object
for v in obj.data.vertices:
    x = v.co.x * escala_ruido
    y = v.co.y * escala_ruido
    valor = mathutils.noise.noise(mathutils.Vector((x, y, 0.0)))
    v.co.z = max(suelo, ((valor + 1.0) / 2.0) * amplitud)

# 4. Extruir bordes del terreno hacia abajo hasta el nivel del suelo
# Los vertices en el borde (abs(x)>9.85 o abs(y)>9.85) se extruden
# creando paredes que siguen el contorno exacto de las montanas.
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

# 5. Material del terreno
mat = bpy.data.materials.new(name='Terreno')
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.50, 0.48, 0.45, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.9
obj.data.materials.append(mat)