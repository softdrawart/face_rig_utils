import bpy
import bmesh
from mathutils import Vector

class Vertex:
    def __init__(self, index, vertex_co):
        self.co = vertex_co
        self.index = index
        self.bone = ""  # Initialize bone attribute

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

# Ensure we are in Edit Mode
assert bpy.context.mode == 'EDIT_MESH'

# Get the active object (assumed to be the mesh)
mesh_obj = bpy.context.active_object
mesh = bmesh.from_edit_mesh(mesh_obj.data)

# Check if there's an active vertex
if not mesh.select_history:
    raise ValueError("No active vertex found in select history")

active_vert = mesh.select_history[-1]

sortedVerts = findConnected(active_vert, mesh)
#sortedVerts.reverse()  # Reverse the list of connected vertices
verts = [Vertex(vert.index, vert.co) for vert in sortedVerts]  # Add vertex instances from sorted list

# Switch to Object Mode
if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

obj = bpy.context.scene.objects['metarig']
armature = obj.data
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

# Iterate over sorted vertices and create bones
for i, vert in enumerate(verts):
    bone_name = f"eyeLidB_{i}"
    if bone_name in armature.edit_bones:
        armature.edit_bones.remove(armature.edit_bones[bone_name])  # Remove if bone exists in armature
    bone = armature.edit_bones.new(name=bone_name)
    bone.head = mesh_obj.matrix_world @ vert.co
    bone.tail = bone.head + Vector((0, 0, 0.001))  # Adjust the tail position as needed
    vert.bone = bone.name  # Assign bone name to Vertex instance

# Return to initial mesh
if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

bpy.context.view_layer.objects.active = mesh_obj

# Add all weights and lock them
for vert in verts:
    group_index = mesh_obj.vertex_groups.find(vert.bone)
    if group_index != -1:
        group = mesh_obj.vertex_groups[group_index]
        mesh_obj.vertex_groups.remove(group)
    weight = mesh_obj.vertex_groups.new(name=vert.bone)
    weight.add([vert.index], 1, 'REPLACE')
    weight.lock_weight = True

bpy.ops.object.mode_set(mode='EDIT')
