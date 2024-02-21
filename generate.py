import bpy

TILE_THICK = 0.2
yellowColor = (0.95, 0.829, 0.05, 1)
brownColor = (0.0451939, 0.00518128, 0.00802261, 1)

# got this from
# https://blender.stackexchange.com/questions/104651/selecting-gpu-with-python-script
def use_gpu_render():
    bpy.data.scenes[0].render.engine = "CYCLES"

    # Set the device_type
    bpy.context.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "CUDA" # or "OPENCL"

    # Set the device and feature set
    bpy.context.scene.cycles.device = "GPU"

    # get_devices() to let Blender detects GPU device
    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    print(bpy.context.preferences.addons["cycles"].preferences.compute_device_type)
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        d["use"] = 1 # Using all devices, include GPU and CPU
        print(d["name"], d["use"])

use_gpu_render()

bpy.context.scene.cycles.feature_set = 'EXPERIMENTAL' # for adaptive subdivision
bpy.context.scene.cycles.dicing_rate = 0.25

bpy.context.scene.render.filepath = "/home/jcreed/tmp/out.png"

bpy.context.scene.render.resolution_x = 640*2
bpy.context.scene.render.resolution_y = 480*2

def letterMat(letterImage):
    material = bpy.data.materials.new(name="Letter")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    # texture node
    texImage = nodes.new(type='ShaderNodeTexImage')
    texImage.extension = 'EXTEND'
    bpy.ops.image.open(filepath="/home/jcreed/proj/blender-generate/W.png")
    texImage.image = bpy.data.images.get(letterImage)

    # mix node
    mix = nodes.new(type='ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = yellowColor
    mix.inputs['B'].default_value = brownColor
    material.node_tree.links.new(texImage.outputs['Color'], mix.inputs['Factor']);

    # principled bsdf node
    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_bsdf.inputs['Roughness'].default_value = 0.5
    principled_bsdf.inputs['Metallic'].default_value = 0.1
    material.node_tree.links.new(mix.outputs['Result'], principled_bsdf.inputs['Base Color'])

    # displacement node
    material.cycles.displacement_method = 'DISPLACEMENT'
    displacement = nodes.new(type='ShaderNodeDisplacement')
    displacement.space = 'OBJECT'
    displacement.inputs['Scale'].default_value = -0.07
    displacement.inputs['Midlevel'].default_value = 0
    material.node_tree.links.new(texImage.outputs['Color'], displacement.inputs['Height']);

    # output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled_bsdf.outputs['BSDF'], output_node.inputs['Surface'])
    material.node_tree.links.new(displacement.outputs['Displacement'], output_node.inputs['Displacement'])

    return material

def tileMat():
    material = bpy.data.materials.new(name="Tile")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    # principled bsdf node
    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_bsdf.inputs['Base Color'].default_value = yellowColor
    principled_bsdf.inputs['Roughness'].default_value = 0.5
    principled_bsdf.inputs['Metallic'].default_value = 0.1

    # output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled_bsdf.outputs['BSDF'], output_node.inputs['Surface'])

    return material

matLetter = letterMat("W.png")
matTile = tileMat()

def tile():
  bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
  cube = bpy.context.object
  cube.scale = (1,1,TILE_THICK)
  cube.location = (0,0,1-TILE_THICK)
  bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

  mod = cube.modifiers.new(name="Bevel", type='BEVEL')
  mod.width = 0.07
  mod.segments = 3

  for poly in cube.data.polygons:
      poly.use_smooth = True

  bpy.context.view_layer.objects.active = cube
  bpy.ops.object.modifier_apply(modifier=mod.name)

  top_face = None
  for face in cube.data.polygons:
     if face.normal[0] == 0 and face.normal[1] == 0 and face.normal[2] > 0:
        top_face = face

  top_face_vertex_indices = [cube.data.vertices[v].index for v in top_face.vertices]
  print("Top Face Vertex Indices", top_face_vertex_indices)
  cube_vertices = [cube.data.vertices[v] for v in top_face.vertices]
  print("Cube Vertices:", [v.co for v in cube_vertices])
  orig_vertex_normals = [[cube.data.vertices[v].normal[i] for i in range(3)] for v in range(len(cube.data.vertices))]
  top_face_vertex_normals = [orig_vertex_normals[v] for v in top_face.vertices]

  ### print("Cube Vertex Normals:", orig_vertex_normals)

  cube.data.materials.clear()
  cube.data.materials.append(matTile)

  # Duplicate the cube so that we can restore normals after doing some surgery to it
  bpy.ops.object.duplicate()
  orig_cube = bpy.context.object

  # Delete the top face
  top_face.select = True
  cube.select_set(True)
  bpy.ops.object.mode_set(mode='EDIT')
  bpy.ops.mesh.delete(type='FACE')
  bpy.ops.object.mode_set(mode='OBJECT')

  def restore_normals_to(obj):
    obj.data.use_auto_smooth = True
    mod = obj.modifiers.new(name="DataTransfer", type='DATA_TRANSFER')
    mod.object = orig_cube
    mod.use_loop_data = True
    mod.data_types_loops = {'CUSTOM_NORMAL'}
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

  restore_normals_to(cube)

  ### Make Letter
  bpy.ops.mesh.primitive_plane_add(location=(0,0,0))
  plane = bpy.context.object
  plane.scale = (cube_vertices[0].co[0], cube_vertices[0].co[1], 1)
  plane.location = (0,0,1)
  plane.select_set(True)
  bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

  restore_normals_to(plane)

  mod = plane.modifiers.new(name="Subdivision", type='SUBSURF')
  plane.cycles.use_adaptive_subdivision = True
  mod.subdivision_type = 'SIMPLE'

  plane.data.materials.clear()
  plane.data.materials.append(matLetter)


tile()

camera = bpy.context.scene.camera
camera.location *= 0.5
camera.location.z += 0.5

# bpy.ops.render.render(animation=False, write_still=True, use_viewport=False, layer='', scene='')
bpy.ops.wm.save_as_mainfile(filepath="/home/jcreed/tmp/debug.blend")
