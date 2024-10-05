"""
Based on the guide on UILists by Sinestesia.
https://sinestesia.co/blog/tutorials/using-uilists-in-blender/
"""

import bpy
class MY_UL_List(bpy.types.UIList):
    """Demo UIList."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # We could write some code to decide which icon to use here...
        custom_icon = 'SCENE'
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            grid = layout.grid_flow(columns=3, align=True, even_columns=False)
            grid.label(text=item.name, icon = custom_icon)
            
            #split = grid.split(factor=0.3, align=False)
            #lf,rt = (split.column(),split.column())
            grid.label(text="{}-{}".format(str(item.startFrame), str(item.endFrame)))
            grid.prop(item, "enabled", text="")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

class LIST_OT_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_idname = "scenedbmanager.new_item"
    bl_label = "Add a new item"
    
    def execute(self, context):
        val = context.scene.ScenesDB.add()
        curFrame = bpy.context.scene.frame_current
        val.name = "scene"
        # If there's a marker on the current spot, get the name of it.
        for m in bpy.context.scene.timeline_markers:
            if m.frame == curFrame:
                 val.name = m.name
                 break

        val.startFrame = curFrame
        val.endFrame = curFrame
        val.enabled = True
        return{'FINISHED'}

class LIST_OT_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_idname = "scenedbmanager.delete_item"
    bl_label = "Deletes an item"
    
    @classmethod
    def poll(cls, context):
        return context.scene.ScenesDB
        
    def execute(self, context):
        ScenesDB = context.scene.ScenesDB
        index = context.scene.ScenesDBlist_index
        ScenesDB.remove(index)
        context.scene.ScenesDBlist_index = min(max(0, index - 1), len(ScenesDB) - 1)
        return{'FINISHED'}

class LIST_OT_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "scenedbmanager.move_item"
    bl_label = "Move an item in the list"
    direction = bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),))
    
    @classmethod
    def poll(cls, context):
        return context.scene.ScenesDB
        
    def move_index(self):
        """ Move index of an item render queue while clamping it. """

        index = bpy.context.scene.ScenesDBlist_index
        list_length = len(bpy.context.scene.ScenesDB) - 1 # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        
        bpy.context.scene.ScenesDBlist_index = max(0, min(new_index, list_length))
        
    def execute(self, context):
        ScenesDB = context.scene.ScenesDB
        index = context.scene.ScenesDBlist_index
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        ScenesDB.move(neighbor, index)
        self.move_index()
        return{'FINISHED'}