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
bpy.context.scene.render.filepath = "/tmp/out.png"

bpy.context.scene.render.resolution_x = 960
bpy.context.scene.render.resolution_y = 540

LAYER_HEIGHT = 0.2

def makemat():
    material = bpy.data.materials.new(name="MyMaterial")

    # Enable 'Use nodes' for the material
    material.use_nodes = True

    # Get the node tree of the material
    nodes = material.node_tree.nodes

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create a principled shader node
    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')

    # Set properties of the principled shader node
    principled_bsdf.inputs['Base Color'].default_value = (1, 1, 0.8, 1)  # RGBA color
    principled_bsdf.inputs['Roughness'].default_value = 0.4  # Roughness value
    principled_bsdf.inputs['Metallic'].default_value = 0.3  # Metallic value

    # Create an output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # Link the principled shader node to the output node
    material.node_tree.links.new(principled_bsdf.outputs['BSDF'], output_node.inputs['Surface'])
    return material

mat = makemat()

def layer(n, s):
    for xx in range(s):
      for yy in range(s):
        # instead of 0..s-1 we want to go -s/2+1/2..s/2-1/2
        x = xx - s/2 + 1/2
        y = yy - s/2 + 1/2
        bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
        cube = bpy.context.object
        cube.scale = (1/s,1/s,LAYER_HEIGHT)
        cube.location = (2*x/s,2*y/s,3*n*LAYER_HEIGHT+LAYER_HEIGHT)
        cube.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # mod = cube.modifiers.new(name="Subdivision", type='SUBSURF')
        # mod.render_levels = 3  # The number of subdivisions during render time

        mod = cube.modifiers.new(name="Bevel", type='BEVEL')
        mod.width = 0.07
        mod.segments = 3

        cube.data.materials.clear()
        cube.data.materials.append(mat)

        for poly in cube.data.polygons:
            poly.use_smooth = True

layer(0, 1)
layer(1, 2)
layer(2, 4)
layer(3, 8)

bpy.ops.render.render(animation=False, write_still=True, use_viewport=False, layer='', scene='')
