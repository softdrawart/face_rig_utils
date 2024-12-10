import bpy
import bmesh
from mathutils import Vector

class VertexGroups(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(name="Index")
    co: bpy.props.FloatVectorProperty(name="Coordinates", size=3)
    bone: bpy.props.StringProperty(name="Bone")
    weight: bpy.props.StringProperty(name="Weight")

# Function to add a vertex to the collection
def add_vertex(obj, index, co, bone="", weight=""):
    if not hasattr(obj, 'vertices'):
        raise Valu eError(f"No vertices parameter in {obj.name}")
    
    # Initialize the index map if not already done
    if not hasattr(obj, 'vertex_index_map'):
        obj.vertex_index_map = {v.index: i for i, v in enumerate(obj.vertices)}
    
    if index in obj.vertex_index_map:
        vertex = obj.vertices[obj.vertex_index_map[index]]
    else:
        vertex = obj.vertices.add()
        obj.vertex_index_map[index] = len(obj.vertices) - 1
    
    vertex.index = index
    vertex.co = co
    vertex.bone = bone
    vertex.weight = weight
    


def generate_bones(mesh_obj):
    #internal method
    def findConnected(vertex, mesh, visited=None):
        if visited is None:
            visited = set()
        
        visited.add(vertex.index)  # Store index of the vertex
        connected_vertices = [vertex]  # Store vertex
        
        for edge in vertex.link_edges:
            linked_vert = edge.other_vert(vertex)
            if linked_vert.select and linked_vert.index not in visited:
                connected_vertices.extend(findConnected(linked_vert, mesh, visited))
        
        return connected_vertices
    #internal class
    class Vertex:
        def __init__(self, index, vertex_co):
            self.co = vertex_co
            self.index = index
            self.bone = ""
            self.weight = ""
    
    # Ensure we are in Edit Mode
    assert bpy.context.mode == 'EDIT_MESH'

    mesh = bmesh.from_edit_mesh(mesh_obj.data)

    # Check if there's an active vertex
    if not mesh.select_history:
        raise ValueError("No active vertex found in select history")

    active_vert = mesh.select_history[-1]

    sortedVerts = findConnected(active_vert, mesh)
    verts = [Vertex(vert.index, vert.co) for vert in sortedVerts] #store currently selected verts
    
    # Switch to Object Mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    obj = bpy.context.scene.objects['metarig']
    armature = obj.data
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Iterate over sorted vertices and create bones
    for i, vert in enumerate(verts):
        bone_name = f"eyeLidT_{i}.L" #name of the bone
        if bone_name in armature.edit_bones:
            armature.edit_bones.remove(armature.edit_bones[bone_name])  # Remove if bone exists in armature
        bone = armature.edit_bones.new(name=bone_name)
        bone.head = mesh_obj.matrix_world @ vert.co
        bone.tail = bone.head + Vector((0, 0, 0.001))  # Adjust the tail position as needed
        vert.bone = bone.name  # Assign bone name to Vertex instance
        vert.weight = f"DEF-{bone.name}"
    #add verts to the list
    for vert in verts:
        add_vertex(mesh_obj, vert.index, vert.co, vert.bone, vert.weight)

    # Return to initial mesh
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')

def assign_weights(obj, vert_group: str): #assign vertex weight from object
    if vert_group in obj: #if property exist in object
        verts = obj[vert_group]
        if verts and obj:
            for vert in verts:
                group_index = obj.vertex_groups.find(vert['weight'])
                if group_index != -1: #if weight exist
                    weight = obj.vertex_groups[vert['weight']] #add weight
                    weight.add([vert['index']], 1, 'REPLACE')
                    weight.lock_weight = True
            
def removeProps(prop):
    if hasattr(bpy.types.Object, prop):
        del bpy.types.Object.vertices
    for obj in bpy.data.objects:
        if prop in obj:
            del obj[prop]
            print(f"Property {prop} removed from object {obj.name}")
prop_name = 'vertices'
'''            
bpy.utils.register_class(VertexGroups)
removeProps(prop_name)
bpy.types.Object.vertices = bpy.props.CollectionProperty(type=VertexGroups)
bpy.types.Object.vertex_index_map = {}
'''

#test call
mesh_obj = bpy.context.active_object
#generate_bones(mesh_obj)
assign_weights(mesh_obj, prop_name)