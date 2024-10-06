bl_info = {
	"name": "RykeShrk's Batch Render Tool",
	"blender": (4, 1, 0),
	"category": "Object",
}

import bpy
from datetime import datetime
import textwrap

wrapp = textwrap.TextWrapper(width=70)

# Import UI classes for the list
from . UIListDec import (
	MY_UL_List, LIST_OT_NewItem,
	LIST_OT_DeleteItem,
	LIST_OT_MoveItem,
	LIST_OT_ImportFromMarkers,
	LIST_OT_SearchForFolder)

from . RenderModal import ( RenderAllScenes )
from . DataTypes import ( UIProgressData, ListRenderDatabase )

def ui_update(self, context):
	for region in context.area.regions:
		if region.type == "WINDOW":
			region.tag_redraw()
	return None

class UIDemo(bpy.types.Panel):
	bl_label = "RykeShrk's Batch Render Tool"
	bl_idname = "render.progressCustom"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "render"
	
	def draw(self, context):
		scene = context.scene
		layout = self.layout
		
		mytool = scene.mytool
		
		if mytool.IsRendering is False:
			row = layout.row(align=True)

			row.prop(mytool, "OutputFolderLocation", text='')
			row.operator('scenedbmanager.search_for_folder', text='', icon='FILE_FOLDER')
			layout.label(text="Defined Scenes:")
			row = layout.row()
			row.template_list("MY_UL_List", "The_List", scene, "ScenesDB", scene, "ScenesDBlist_index")

			col = row.column(align=True)

			col.operator('scenedbmanager.new_item', text='', icon='ADD')
			col.operator('scenedbmanager.delete_item', text='', icon='REMOVE')

			col.separator()
			col = col.row(align=True)

			col.operator('scenedbmanager.import_from_markers', text='', icon='MARKER')

			row = layout.row(align=True)
			#row.operator('scenedbmanager.new_item', text='New', icon='ADD')
			#row.operator('scenedbmanager.delete_item', text='Remove', icon='X')

			row = layout.row()
			#row.operator('scenedbmanager.import_from_markers', text='Import from Markers', icon='MARKER')
			
			if scene.ScenesDBlist_index >= 0 and scene.ScenesDB: 
				item = scene.ScenesDB[scene.ScenesDBlist_index]
				row = layout.row()
				row.prop(item, "name")
				row = layout.row()
				row.prop(item, "enabled", text="Render Scene?")
				row = layout.row(align=True)
				row.prop(item, "startFrame")
				row.prop(item, "endFrame")

				box = layout.box()
				row = box.split(factor=0.3, align=False)
				col1,col2 = (row.column(),row.column())
				col1.label(text="Scene Output Location:")
				col2.label(text="{0}{1}\\".format(context.scene.mytool.OutputFolderLocation,item.get('name', '')))
			
			activeScenes = 0
			for scene in scene.ScenesDB:
				if scene.get("enabled", False):
					activeScenes += 1
					
			if activeScenes > 0 and context.scene.mytool.OutputFolderLocation:
				row = layout.row()
				layout.operator(RenderAllScenes.bl_idname, icon="VIEW_CAMERA")
			else:
				### TODO: This can be optimized into its own method.
				if activeScenes == 0:
					wList = wrapp.wrap(text="You must declare at least ONE scene to use the tool.")
					for text in wList:
						row = layout.row(align = True)
						row.alignment = 'EXPAND'
						if( text is wList[0] ):
							row.label(text=text, icon="ERROR")
						else:
							row.label(text=text)
				if not context.scene.mytool.OutputFolderLocation:
					wList = wrapp.wrap(text="A folder output name must be provided for the scenes to be exported to.")
					for text in wList:
						row = layout.row(align = True)
						row.alignment = 'EXPAND'
						if( text is wList[0] ):
							row.label(text=text, icon="ERROR")
						else:
							row.label(text=text)
		 
		if mytool.IsRendering is True:

			box = layout.box()
			#row = box.split(factor=0.3, align=False)
			#col1,col2 = (row.column(),row.column())
			#box.label(text="Overall Progress:")
			box.progress(factor=mytool.CurJob, text=mytool.JobsLeft)
			box.label(text="Total Time: {}".format(mytool.UITotalTimeSpent))
			layout.row().separator()
			#layout.prop(mytool, "UIcurStatus")
			
			box = layout.box()
			box.prop(mytool, "UIcurScene")
			box.progress(factor=mytool.UIcurRenderProgress, text=mytool.UIcurStatus)
			layout.row().separator()
			#col1.label(text="Total Time: {}".format(mytool.UITotalTimeSpent))
			layout.row().separator()
			
			layout.label(text="Tip: Press ESC on the render to cancel.", icon="INFO")

def register():
	bpy.utils.register_class(RenderAllScenes)
	bpy.utils.register_class(UIDemo)
	
	bpy.utils.register_class(UIProgressData)
	bpy.types.Scene.mytool = bpy.props.PointerProperty(type=UIProgressData)
	
	# Register the scene database.
	bpy.utils.register_class(ListRenderDatabase)
	bpy.types.Scene.ScenesDB = bpy.props.CollectionProperty(type=ListRenderDatabase)
	bpy.types.Scene.ScenesDBlist_index = bpy.props.IntProperty(name = "List of defined scenes", default = 0)
	
	bpy.utils.register_class(MY_UL_List)
	bpy.utils.register_class(LIST_OT_NewItem)
	bpy.utils.register_class(LIST_OT_DeleteItem)
	bpy.utils.register_class(LIST_OT_MoveItem)
	bpy.utils.register_class(LIST_OT_ImportFromMarkers)
	bpy.utils.register_class(LIST_OT_SearchForFolder)
	
def unregister():
	bpy.utils.unregister_class(RenderAllScenes)
	bpy.utils.unregister_class(UIDemo)
	bpy.utils.unregister_class(UIProgressData)
	bpy.utils.unregister_class(ListRenderDatabase)
	
	bpy.utils.unregister_class(MY_UL_List)
	bpy.utils.unregister_class(LIST_OT_NewItem)
	bpy.utils.unregister_class(LIST_OT_DeleteItem)
	bpy.utils.unregister_class(LIST_OT_MoveItem)
	bpy.utils.unregister_class(LIST_OT_ImportFromMarkers)
	bpy.utils.unregister_class(LIST_OT_SearchForFolder)
	
	del bpy.types.Scene.mytool
	
	del bpy.types.Scene.ScenesDB
	del bpy.types.Scene.ScenesDBlist_index

if __name__ == "__main__":
	register()