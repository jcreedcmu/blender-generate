import bpy

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

bpy.context.scene.render.filepath = "/home/jcreed/tmp/out.png"

bpy.context.scene.render.resolution_x = 640
bpy.context.scene.render.resolution_y = 480

TILE_THICK = 0.2

def tileMat():
    material = bpy.data.materials.new(name="Tile")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    # texture node
    texImage = nodes.new(type='ShaderNodeTexImage')
    texImage.extension = 'EXTEND'
    bpy.ops.image.open(filepath="/home/jcreed/proj/blender-generate/W.png")
    texImage.image = bpy.data.images.get("W.png")

    # principled bsdf node
    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_bsdf.inputs['Base Color'].default_value =( 0.95, 0.829, 0.05, 1)
    principled_bsdf.inputs['Roughness'].default_value = 0.5
    principled_bsdf.inputs['Metallic'].default_value = 0.1
    # material.node_tree.links.new(texImage.outputs['Color'], principled_bsdf.inputs['Base Color']);

    # displacement node
    material.cycles.displacement_method = 'DISPLACEMENT'
    displacement = nodes.new(type='ShaderNodeDisplacement')
    displacement.space = 'OBJECT'
    displacement.inputs['Scale'].default_value = 0.1
    displacement.inputs['Midlevel'].default_value = 0
    material.node_tree.links.new(texImage.outputs['Color'], displacement.inputs['Height']);

    # output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled_bsdf.outputs['BSDF'], output_node.inputs['Surface'])
    material.node_tree.links.new(displacement.outputs['Displacement'], output_node.inputs['Displacement'])

    return material

mat = tileMat()

def tile():
  bpy.ops.mesh.primitive_plane_add(location=(0,0,0))
  plane = bpy.context.object
  plane.scale = (1,1,TILE_THICK)
  plane.location = (0,0,1)
  plane.select_set(True)
  bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)



  mod = plane.modifiers.new(name="Subdivision", type='SUBSURF')
  plane.cycles.use_adaptive_subdivision = True
  mod.subdivision_type = 'SIMPLE'

  # mod.render_levels = 3  # The number of subdivisions during render time

  # mod = plane.modifiers.new(name="Bevel", type='BEVEL')
  # mod.width = 0.07
  # mod.segments = 3

  plane.data.materials.clear()
  plane.data.materials.append(mat)

  for poly in plane.data.polygons:
      poly.use_smooth = True

tile()
bpy.ops.render.render(animation=False, write_still=True, use_viewport=False, layer='', scene='')
bpy.ops.wm.save_as_mainfile(filepath="/home/jcreed/tmp/debug.blend")
