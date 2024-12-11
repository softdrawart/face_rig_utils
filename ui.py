bl_info = {
    "name": "Vizor Face Rigging",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy, enum, bmesh
from mathutils import Vector

_BOME_SCALE = 0.1 

class Lid():
    def __init__(self):
        self.indices = []
        self.coordinates = []
        self.bones = []

class Lid_Layers(enum.IntEnum):
    TOP = 0
    BOTTOM = 1

def findConnected(vertex, mesh, visited=None):
    if visited is None:
        visited = set()
    
    visited.add(vertex.index)  # Store index of the vertex
    connected_vertices = [vertex]  # Store Active vertex
    
    for edge in vertex.link_edges:
        linked_vert = edge.other_vert(vertex)
        if linked_vert.select and linked_vert.index not in visited:
            connected_vertices.extend(findConnected(linked_vert, mesh, visited))
    return connected_vertices

class VIEW3D_OT_vizor_add_remove_lid(bpy.types.Operator):
    bl_idname = "object.vizor_add_lid"
    bl_label = "Operator to add Lid"

    lidLayer: bpy.props.EnumProperty(
        items=[
            ("TOP", "Top", ""),
            ("BOTTOM", "Bottom", ""),
        ],
        name="Lid Layer",
        default="TOP",
    )
    lidIndex: bpy.props.IntProperty(default=0)
    add: bpy.props.BoolProperty(default=True)

    
    def add_indicies(self, context):
        assert bpy.context.mode == 'EDIT_MESH' # Ensure we are in Edit Mode
        mesh_obj = context.active_object
        mesh = bmesh.from_edit_mesh(mesh_obj.data)
        selected_verts = [v for v in mesh.verts if v.select]
        #Top Eyelid must have at least 3 verts selected (two for corners and n-amount for bone action rig)
        if self.lidLayer in ["TOP", "Top"] and len(selected_verts) < 3:
            raise ValueError("Please select at least 3 verts!")
        #top lid selection -2 should be euqual to bottom selection
        if len(context.scene.upper_lid.indices) or len(context.scene.lower_lid.indices):
            match self.lidLayer:
                case 'BOTTOM':
                    top_lid_size = len(context.scene.upper_lid.indices)-2
                    if top_lid_size != len(selected_verts):
                        raise ValueError(f"Please select {top_lid_size-(len(selected_verts))} more vertices")
                case 'TOP':
                    low_lid_size = len(context.scene.lower_lid.indices)
                    if low_lid_size != len(selected_verts)-2:
                        raise ValueError(f"Please select {low_lid_size-(len(selected_verts)-2)} more vertices")
        # Check if there's an active vertex
        if not mesh.select_history:
            raise ValueError("No Active Vertex selected")
        active_vert = mesh.select_history[-1]
        #starting from active vertex sort list of selected verticies
        sortedVerts = findConnected(active_vert, mesh)
        #store indices
        indicies = [vert.index for vert in sortedVerts]
        match self.lidLayer:
            case 'TOP':
                #if lower indx list exist check if they have common indx
                if context.scene.lower_lid.indices:
                    common = set(indicies) & set(context.scene.lower_lid.indices)
                    if common:
                        raise ValueError(f"Top and Bottom lid have common verts{common}")
                #add top lid indicies
                context.scene.upper_lid.indices = indicies
                context.scene.upper_lid.coordinates = [vert.co.copy() for vert in sortedVerts]
                context.scene.lid_object = mesh_obj.name
            case 'BOTTOM':
                #if upper indx list exist check if they have common indx
                if context.scene.upper_lid.indices:
                    common = set(indicies) & set(context.scene.upper_lid.indices)
                    if common:
                        raise ValueError(f"Top and Bottom lid have common verts{common}")
                #add bottom lid indicies
                context.scene.lower_lid.indices = indicies
                context.scene.lower_lid.coordinates = [vert.co.copy() for vert in sortedVerts]
                context.scene.lid_object = mesh_obj.name
    
    def remove_indicies(self,context):
        match self.lidLayer:
            case 'TOP':
                #remove top lid indicies
                context.scene.upper_lid.indices = []
                context.scene.upper_lid.coordinates = []
                context.scene.lid_object = ''
            case 'BOTTOM':
                #remove bottom lid indicies
                context.scene.lower_lid.indices = []
                context.scene.lower_lid.coordinates = []
                context.scene.lid_object = ''
    
    def execute(self, context):
        match self.add:
            case True:
                #add lid
                self.add_indicies(context)
                print(f"{self.lidLayer} Lid {self.lidIndex} is Added")
            case False:
                #remove Lid
                self.remove_indicies(context)
                print(f"{self.lidLayer} Lid {self.lidIndex} is Removed")

        return {'FINISHED'}

class VIEW3D_OT_vizor_generate_lid_rig(bpy.types.Operator):
    bl_idname = "object.vizor_generate_lid_rig"
    bl_label = "Operator to rig lid"

    def generate_bones(self, context, verts: Lid, bone_name: str, top: bool):
        '''Generates bones for all indices of the lid'''
        # Switch to Object Mode
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

        obj = bpy.data.objects.get(context.scene.lid_armature) #armature object
        if not obj:
            raise ValueError(f"Armature {context.scene.lid_armature} doesnt exist!")
        mesh_obj = bpy.data.objects.get(context.scene.lid_object) #mesh object

        if not mesh_obj:
            raise ValueError(f"Mesh Object {context.scene.lid_object} doesnt exist!")
        armature = obj.data
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Iterate over sorted vertices and create bones
        for i, vert in enumerate(verts.indices):
            if (i == 0 or i == len(verts.indices)-1) and top:
                #corner bone name
                if i == 0:
                    name = f"corner_{bone_name}_start" #name of the bone
                else:
                    name = f"corner_{bone_name}_end" #name of the bone
            elif top:
                name = f"{bone_name}_{i-1}" #name of the bone - 1 corner bone
            else:
                name = f"{bone_name}_{i}" #name of the bone
            if name in armature.edit_bones:
                armature.edit_bones.remove(armature.edit_bones[name])  # Remove if bone exists in armature
            bone = armature.edit_bones.new(name=name)
            #add bone to the list
            verts.bones.append(bone.name)
            #set bone position
            bone.head = mesh_obj.matrix_world @ verts.coordinates[i]
            bone.tail = bone.head + Vector((0, 0, _BOME_SCALE))  # Adjust the tail position as needed

            #vert.weight = f"DEF-{bone.name}"
    
    def generate_controller(self, context, bone_name: str, position: Vector):
        obj = bpy.data.objects.get(context.scene.lid_armature) #armature object
        if not obj:
            raise ValueError(f"Armature {context.scene.lid_armature} doesnt exist!")
        armature = obj.data
        #create Action ctrl bone
        if bone_name in armature.edit_bones:
            armature.edit_bones.remove(armature.edit_bones[bone_name])  # Remove if bone exists in armature
        bone = armature.edit_bones.new(name=bone_name)

        mesh_obj = bpy.data.objects.get(context.scene.lid_object)
        if not mesh_obj:
            raise ValueError(f"Mesh Object {context.scene.lid_object} doesnt exist!")
        
        #set bone position
        bone.head = mesh_obj.matrix_world @ position
        bone.tail = bone.head + Vector((0, 0, _BOME_SCALE/2))  # Adjust the tail position as needed

    def generate_action(self, context):
        '''add action to selected armature and add three keyframes opened and closed eyelids'''
        #check if armature, bones exist
        obj = bpy.data.objects.get(context.scene.lid_armature) #armature object
        if not obj:
            raise ValueError(f"Armature {context.scene.lid_armature} doesnt exist!")
        armature = obj.data
        for b in context.scene.upper_lid.bones + context.scene.lower_lid.bones:
            bone = armature.bones.get(b)
            if not bone:
                raise ValueError(f"Bone {b} doesnt exist")
        

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT') #set object mode
        #clear bones just in case we run generate 2nd time
        context.scene.upper_lid.bones = []
        context.scene.lower_lid.bones = []
        context.scene.lid_ctrl_bone = ''

        assert bpy.context.mode == 'OBJECT'
        #generate bones for lid and CTRL bone for Action trigger
        self.generate_bones(context, context.scene.upper_lid, 'upper_lid', True)
        self.generate_bones(context, context.scene.lower_lid, 'lower_lid', False)
        position = (context.scene.upper_lid.coordinates[0] + context.scene.upper_lid.coordinates[-1]) / 2 #find mid position for ctrl
        self.generate_controller(context, 'ctrl_lid', position)
        #generate action with keyframes
        self.generate_action(context)
        #add Action constrains
        return {'FINISHED'}

class VIEW3D_PT_rigging_vizor(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vizor Rigging'
    bl_label = 'Eye Lids'

    def draw_lid(self, context, lid_layer):
        #size of current lid indicies
        lid_size = len((context.scene.upper_lid.indices if lid_layer == 'TOP' else context.scene.lower_lid.indices))
        #dont DRAW bottom lid row if TOP is not set 
        if (lid_layer in ["BOTTOM", "Bottom"]):
            if lid_size == 0 and len(context.scene.upper_lid.indices) == 0:
                return None
        layout = self.layout
        
        
        if context.scene.lid_armature and bpy.context.mode == 'EDIT_MESH' and context.tool_settings.mesh_select_mode[0] == True or lid_size > 0:
            #draw add lid label with button
            #draw label
            up_lid_row = layout.row() # stack label and button
            text = f"{lid_layer} Lid {lid_size} Indicies Selected"
            up_lid_row.label(text=text)

            if lid_size > 0:
                #show - button operator
                op = up_lid_row.operator(VIEW3D_OT_vizor_add_remove_lid.bl_idname, icon="REMOVE")
                op.lidLayer = lid_layer
                op.lidIndex = 0 #you might want multiple lids attached using action
                op.add = False
            else:
                #show + button operator
                op = up_lid_row.operator(VIEW3D_OT_vizor_add_remove_lid.bl_idname, icon="PLUS")
                op.lidLayer = lid_layer
                op.lidIndex = 0 #you might want multiple lids attached using action
                op.add = True
        
    def draw(self, context):
        layout = self.layout

        

        #ARMATURE ADD
        layout.label(text='Fisrt select the Armature for Rig')
        layout.prop_search(
            data=context.scene, # Object data to store the result
            property="lid_armature",    # Property to store the selected material
            search_data=bpy.data,          # Where to search for materials
            search_property="armatures",   # Property that holds the list of materials
            text="Armature"                # Label for the field
        )

        #draw next layout for vertex selection
        if context.scene.lid_armature:
            layout.label(text='(EDIT mode) select vertices and add them using + ')

        #UPPER LID ADD/REMOVE
        self.draw_lid(context, 'TOP')
            
        #UPPER LID ADD/REMOVE
        self.draw_lid(context, 'BOTTOM')
        
        #GENERATE
        if context.scene.upper_lid.indices and context.scene.lower_lid.indices:
            #draw Generate button
            row = layout.row()
            row.label(text='Generate rig')
            row.operator(VIEW3D_OT_vizor_generate_lid_rig.bl_idname, text="generate")


        
  
classes = (
    VIEW3D_PT_rigging_vizor,
    VIEW3D_OT_vizor_add_remove_lid,
    VIEW3D_OT_vizor_generate_lid_rig,
)
def register_properties():
    scene = bpy.types.Scene #property space
    scene.lid_armature = bpy.props.StringProperty(name="Armature")
    scene.lid_object = bpy.props.StringProperty(name="Mesh object")
    scene.lid_ctrl_bone = bpy.props.StringProperty(name="Action Controller bone")
    scene.upper_lid = Lid()
    scene.lower_lid = Lid()

    

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__== "__main__":
    register()