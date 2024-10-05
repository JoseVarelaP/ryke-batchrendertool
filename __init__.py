bl_info = {
	"name": "RykeShrk's Batch Render Tool",
	"blender": (4, 2, 0),
	"category": "Object",
}

import bpy
from datetime import datetime
import textwrap

wrapp = textwrap.TextWrapper(width=70)

# Import UI classes for the list
from . UIListDec import (MY_UL_List, LIST_OT_NewItem, LIST_OT_DeleteItem, LIST_OT_MoveItem, LIST_OT_ImportFromMarkers)

def ui_update(self, context):
	for region in context.area.regions:
		if region.type == "WINDOW":
			region.tag_redraw()
	return None

class UIProgressData(bpy.types.PropertyGroup):
	UIcurRenderProgress: bpy.props.FloatProperty( name="Progress", default=0, update=ui_update )
	UIcurScene: bpy.props.StringProperty( name="Cur Scene", default="", set=None, update=ui_update )
	UIcurStatus: bpy.props.StringProperty( name="Status", default="", update=ui_update )
	UITotalTimeSpent: bpy.props.StringProperty( name="Total Time", default="", update=ui_update )
	
	CurJob: bpy.props.FloatProperty(name="Total Progress", default=0, update=ui_update)
	JobsLeft: bpy.props.StringProperty(name="Jobs Left", default="Calculating Jobs...", update=ui_update)
	
	IsRendering: bpy.props.BoolProperty(name="IsRendering", default=False, update=ui_update)
	# Completed: bpy.props.BoolProperty(name="Completed", default=False, update=ui_update)

	OutputFolderLocation: bpy.props.StringProperty(name="Output Folder Location", default="", update=ui_update)

"""
Scene Declarations

This class will keep track of the scenes that the user wants to render out.
"""
class ListRenderDatabase(bpy.types.PropertyGroup):
	name: bpy.props.StringProperty(
		name="Scene Name",
		description="Name for the scene. This name will be used during export",
		default="scene"
	)
	
	startFrame: bpy.props.IntProperty(
		name="Start Frame",
		description="Declare the starting point for this scene",
		default=1
	)
	
	endFrame: bpy.props.IntProperty(
		name="End Frame",
		description="Declare the ending point for this scene",
		default=1
	)
	
	enabled: bpy.props.BoolProperty(
		name="Enabled",
		description="Determines if this scene will be rendered in the batch or not",
		default=True
	)
	
class RenderAllScenes(bpy.types.Operator):
	bl_idname = "render.allscenes"
	bl_label = "Render Selected Scenes"
	
	UIRenderStatus = None
	
	cancel_render = None
	rendering = None
	render_queue = None
	timer_event = None
	total = 0
	
	TIMERStartTime = datetime.now()
	
	def render_init(self, scene, depsgraph):
		scene.mytool.IsRendering = True
		
	def render_complete(self, scene, depsgraph):
		self.render_queue.pop(0)
		self.rendering = False
		
	def render_cancel(self, scene, depsgraph):
		self.cancel_render = True
		print("RENDER CANCEL")
		scene.mytool.IsRendering = False
		
	def render_post(self, scene, despgraph):
		# Get the current frame that we're in, and report the current progress from that.
		curFrame = scene.frame_current
		curFrameInSequence = (curFrame - self.render_queue[0]['startFrame'])
		lastFrameInSequence = (self.render_queue[0]['endFrame'] - self.render_queue[0]['startFrame'])
		
		scene.mytool.UIcurRenderProgress = ( curFrameInSequence/lastFrameInSequence )
		scene.mytool.UIcurStatus = "Rendering frame {} of {} ({:3.2f}%)".format(
			curFrameInSequence+1, lastFrameInSequence+1, ( curFrameInSequence/lastFrameInSequence ) * 100
		)
		
	def execute(self, context):
		self.cancel_render = False
		self.rendering = False
		self.render_queue = []
		
		## Update UI Info
		self.TIMERStartTime = datetime.now()
		context.scene.mytool.UIcurRenderProgress = 0.0
		context.scene.mytool.UIcurScene = ""
		context.scene.mytool.UIcurStatus = ""
		context.scene.mytool.UITotalTimeSpent = ""
		context.scene.mytool.CurJob = -1
		
		#################################
		
		## Time to fill in the data.
		for scene in context.scene.ScenesDB:
			print(scene['enabled'])
			if scene['enabled']:
				self.render_queue.append(scene)
		
		self.total = len(self.render_queue)
		
		context.scene.mytool.TotalJobs = self.total
		
		#################################
		
		# Register callback functions
		bpy.app.handlers.render_init.clear()
		bpy.app.handlers.render_init.append(self.render_init)

		bpy.app.handlers.render_complete.clear()
		bpy.app.handlers.render_complete.append(self.render_complete)

		bpy.app.handlers.render_cancel.clear()
		bpy.app.handlers.render_cancel.append(self.render_cancel)
		
		bpy.app.handlers.render_post.clear()
		bpy.app.handlers.render_post.append(self.render_post)

		# Lock interface
		bpy.types.RenderSettings.use_lock_interface = True
		
		# Create timer event that runs every second to check if render render_queue needs to be updated
		self.timer_event = context.window_manager.event_timer_add(1.0, window=context.window)
		
		# register this as running in background
		context.window_manager.modal_handler_add(self)
		
		return {"RUNNING_MODAL"}
		
	def modal(self, context, event):
		if event.type == 'ESC':
			bpy.types.RenderSettings.use_lock_interface = False
			context.scene.mytool.IsRendering = False
			print("CANCELLED")
			return {'CANCELLED'}
		elif event.type == 'TIMER':
			## Update the total time.
			context.scene.mytool.UITotalTimeSpent = str(datetime.now() - self.TIMERStartTime)
			
			if len(self.render_queue) == 0 or self.cancel_render is True:
				
				# Remove render callbacks
				bpy.app.handlers.render_init.clear()
				bpy.app.handlers.render_complete.clear()
				bpy.app.handlers.render_cancel.clear()
				bpy.app.handlers.render_post.clear()
				
				# Remove timer
				context.window_manager.event_timer_remove(self.timer_event)
				
				bpy.types.RenderSettings.use_lock_interface = False
				context.scene.mytool.IsRendering = False
				
				print("FINISHED")
				return {'FINISHED'}
			
			# Nothing is rendering...
			elif self.rendering is False:
				sc=bpy.context.scene
				currentscene = self.render_queue[0]
				
				# Change the start and end frames.
				sc.frame_start = currentscene['startFrame']
				sc.frame_end = currentscene['endFrame']
				# Change the render file path to the correct location.
				bpy.context.scene.render.filepath = "{0}/{1}\\".format(context.scene.mytool.OutputFolderLocation,currentscene['name'])
				
				timestart = str(currentscene['startFrame'])
				timeend = str(currentscene['endFrame'])
				scenename = currentscene['name']
				
				## Update UI Info
				sc.mytool.UIcurScene = scenename
				sc.mytool.CurJob = (self.total - len(self.render_queue)) / self.total
				sc.mytool.JobsLeft = "{} jobs completed of {}.".format(self.total - len(self.render_queue), self.total)
				print(sc.mytool.CurJob)
				
				# And now, render!
				bpy.ops.render.render('INVOKE_DEFAULT', animation=True, write_still=True)
			
		return {"PASS_THROUGH"}

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
			row = layout.row()
			row.prop(mytool, "OutputFolderLocation")
			layout.label(text="Defined Scenes:")
			row = layout.row()
			row.template_list("MY_UL_List", "The_List", scene, "ScenesDB", scene, "ScenesDBlist_index")
			
			row = layout.row()
			row.operator('scenedbmanager.new_item', text='New')
			row.operator('scenedbmanager.delete_item', text='Remove')
			
			if scene.ScenesDBlist_index >= 0 and scene.ScenesDB: 
				item = scene.ScenesDB[scene.ScenesDBlist_index]
				row = layout.row()
				row.prop(item, "name")
				row = layout.row()
				row.prop(item, "enabled", text="Render Scene?")
				row = layout.row()
				row.prop(item, "startFrame")
				row.prop(item, "endFrame")

				box = layout.box()
				row = box.split(factor=0.3, align=False)
				col1,col2 = (row.column(),row.column())
				col1.label(text="Scene Output Location:")
				col2.label(text="{0}/{1}\\".format(context.scene.mytool.OutputFolderLocation,item.get('name', '')))
			
			activeScenes = 0
			for scene in scene.ScenesDB:
				if scene.get("enabled", False):
					activeScenes += 1
					
			if activeScenes > 0 and context.scene.mytool.OutputFolderLocation:
				row = layout.row()
				layout.operator(RenderAllScenes.bl_idname, icon="VIEW_CAMERA")
			else:
				### TODO: This can be optimized into its own method.
				if not bpy.data.is_saved:
					wList = wrapp.wrap(text="You haven't saved this blend file! Either set a output location or save the file before continuing.")
					for text in wList:
						row = layout.row(align = True)
						row.alignment = 'EXPAND'
						if( text is wList[0] ):
							row.label(text=text, icon="ERROR")
						else:
							row.label(text=text)
					# layout.label(text="You haven't saved this blend file! Either set a output location or save the file before continuing.", icon="ERROR")
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
			row = box.split(factor=0.3, align=False)
			col1,col2 = (row.column(),row.column())
			col1.label(text="Overall Progress:")
			col2.progress(factor=mytool.CurJob, text=mytool.JobsLeft)
			layout.row().separator()
			#layout.prop(mytool, "UIcurStatus")
			
			box = layout.box()
			box.prop(mytool, "UIcurScene")
			box.progress(factor=mytool.UIcurRenderProgress, text=mytool.UIcurStatus)
			layout.row().separator()
			col1.label(text="Total Time: {}".format(mytool.UITotalTimeSpent))
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
	
	del bpy.types.Scene.mytool
	
	del bpy.types.Scene.ScenesDB
	del bpy.types.Scene.ScenesDBlist_index