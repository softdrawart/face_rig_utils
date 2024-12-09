bl_info = {
    "name": "Vizor Face Rigging",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy

class Lid():
    def __init__(self):
        self.indices = []
        self.bones = []
        self.obj = ''
        self.arm = ''
class VIEW3D_PT_rigging_vizor(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vizor Rigging'
    bl_label = 'Eye Lids'

    def draw(self, context):
        layout = self.layout
        
        #store Armature for rigging
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
        #if we are in edit mode and we have vertex mode selected then show tools
        if context.scene.lid_armature and bpy.context.mode == 'EDIT_MESH' and context.tool_settings.mesh_select_mode[0] == True:
            context.scene.list.arm = context.scene.lid_armature
            print(f"this is my Lid Armature {context.scene.list.arm}")

classes = (
    VIEW3D_PT_rigging_vizor,
)
def register_properties():
    scene = bpy.types.Scene #property space
    scene.lid_armature = bpy.props.StringProperty(name="Armature")
    scene.object_name = bpy.props.StringProperty(name="object_name")  # Name of the object containing the vertices
    scene.armature_name = bpy.props.StringProperty("armature_name")  # Name of the selected armature
    scene.list = Lid()
    '''
    #lists of int or str values
    active_scene = bpy.context.scene #active scene
    active_scene['upper_lid_indices'] = []  # Upper lid vertex indices
    active_scene['lower_lid_indices'] = []  # Lower lid vertex indices
    active_scene['upper_lid_bones'] = []  # Upper lid bone names
    active_scene['lower_lid_bones'] = []  # Lower lid bone names
    '''

    

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__== "__main__":
    register()