bl_info = {
    "name": "Vizor Face Rigging",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy, enum, bmesh

class Lid():
    def __init__(self):
        self.indices = []
        self.coordinates = []
        self.bones = []
        self.obj = ''

class Lid_Layers(enum.IntEnum):
    TOP = 0
    BOTTOM = 1

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
        #Top Eyelid must have at least 3 verts selected (two for corners and n-amount for bone action rig)
        if self.lidLayer in ["TOP", "Top"] and len(mesh.select_history) < 3:
            raise ValueError("Please select at least 3 verts selected!")
        #top lid selection -2 should be euqual to bottom selection
        if len(context.scene.upper_lid.indices) or len(context.scene.lower_lid.indices):
            match self.lidLayer:
                case 'BOTTOM':
                    if len(context.scene.upper_lid.indices)-2 != len(mesh.select_history):
                        raise ValueError("Please select same amount of vertices")
                case 'TOP':
                    if len(context.scene.lower_lid.indices) != len(mesh.select_history)-2:
                        raise ValueError("Please select same amount of vertices")
        # Check if there's an active vertex
        if not mesh.select_history:
            raise ValueError("No Vertecies selected")
        active_vert = mesh.select_history[-1]

        sortedVerts = findConnected(active_vert, mesh)
        #store indices
        match self.lidLayer:
            case 'TOP':
                #add top lid indicies
                context.scene.upper_lid.indices = [vert.index for vert in sortedVerts]
                context.scene.upper_lid.coordinates = [vert.co for vert in sortedVerts]
                context.scene.upper_lid.obj = mesh_obj
            case 'BOTTOM':
                #add bottom lid indicies
                context.scene.lower_lid.indices = [vert.index for vert in sortedVerts]
                context.scene.lower_lid.coordinates = [vert.co for vert in sortedVerts]
                context.scene.lower_lid.obj = mesh_obj
    
    def remove_indicies(self,context):
        match self.lidLayer:
            case 'TOP':
                #remove top lid indicies
                context.scene.upper_lid.indices = []
                context.scene.upper_lid.coordinates = []
                context.scene.upper_lid.obj = ''
            case 'BOTTOM':
                #remove bottom lid indicies
                context.scene.lower_lid.indices = []
                context.scene.lower_lid.coordinates = []
                context.scene.lower_lid.obj = ''
    
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
  
classes = (
    VIEW3D_PT_rigging_vizor,
    VIEW3D_OT_vizor_add_remove_lid,
)
def register_properties():
    scene = bpy.types.Scene #property space
    scene.lid_armature = bpy.props.StringProperty(name="Armature")
    scene.object_name = bpy.props.StringProperty(name="object_name")  # Name of the object containing the vertices
    scene.armature_name = bpy.props.StringProperty("armature_name")  # Name of the selected armature
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