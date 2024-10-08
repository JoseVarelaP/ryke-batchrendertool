"""
Based on the guide on UILists by Sinestesia.
https://sinestesia.co/blog/tutorials/using-uilists-in-blender/
"""

import bpy

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class RYK_UL_ScenesListView(bpy.types.UIList):
    """Demo UIList."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # We could write some code to decide which icon to use here...
        custom_icon = 'SCENE'
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            grid = layout.grid_flow(columns=3, align=True, even_columns=False)
            # grid.label(text=item.name, icon = custom_icon)
            grid.prop(item, "name", text="", icon = custom_icon, emboss=False)
            
            #split = grid.split(factor=0.3, align=False)
            #lf,rt = (split.column(),split.column())
            grid.label(text="{}-{}".format(str(item.startFrame), str(item.endFrame)))
            grid.prop(item, "enabled", text="")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

class RYK_OT_NewItem(bpy.types.Operator):
    """Add a new item to the list"""
    bl_idname = "scenedbmanager.new_item"
    bl_label = "Add a new item"
    
    def execute(self, context):
        val = context.scene.ScenesDB.add()
        curFrame = bpy.context.scene.frame_current
        val.name = "scene"
        val.startFrame = curFrame
        val.endFrame = curFrame

        # If there's a marker on the current spot, get the name of it.
        for m in bpy.context.scene.timeline_markers:
            if m.frame == curFrame:
                val.name = m.name
            # If there so happens to be another marker next to the scene, let's set that as the end of the segment.
            if m.frame > curFrame:
                val.endFrame = m.frame
                break

        val.enabled = True
        return{'FINISHED'}

class RYK_OT_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list"""
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

class RYK_OT_ImportFromMarkers(bpy.types.Operator):
    """Creates the list based on the markers on the current scene"""
    bl_idname = "scenedbmanager.import_from_markers"
    bl_label = "Import from Markers"
        
    def execute(self, context):
        ScenesDB = context.scene.ScenesDB
        markers = bpy.context.scene.timeline_markers

        if not markers:
            ShowMessageBox("No markers were found!", "RykeShrk's Batch Render Tool")
            return{'FINISHED'}

        arraymarker = []
        ScenesDB.clear()

        for i in range(len(markers)):
            m = markers[i]
            arraymarker.append({ 'name': m.name, 'frame': m.frame })

        arraymarker.sort( key=lambda x: x['frame'] )

        for i in range(len(arraymarker)):
            val = context.scene.ScenesDB.add()
            m = arraymarker[i]
            val.name = m['name']
            val.startFrame = m['frame']
            val.enabled = True

            if (i+1) < len(arraymarker):
                nextmarker = arraymarker[i+1]
                val.endFrame = nextmarker['frame']-1
            else:
                val.endFrame = bpy.context.scene.frame_end

        return{'FINISHED'}

class RYK_OT_SearchForFolder(bpy.types.Operator):
    bl_idname = "scenedbmanager.search_for_folder"
    bl_label = "Select Folder"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(
        name="Outdir Path",
        description="Where its gonna be"
    )

    filter_folder: bpy.props.BoolProperty(
        default=True,
        options={'HIDDEN'}
    )

    def execute(self, context):
        print("I got ", self.directory)
        bpy.context.scene.rykbatchrender.OutputFolderLocation = self.directory
        return{'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}