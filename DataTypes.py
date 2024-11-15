import bpy

def ui_update(self, context):
	if context.area is not None:
		for region in context.area.regions:
			if region.type == "WINDOW":
				region.tag_redraw()
	return None
	
class RYK_PG_ProgressData(bpy.types.PropertyGroup):
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
class RYK_PG_ListRenderDatabase(bpy.types.PropertyGroup):
	name: bpy.props.StringProperty(
		name="Scene Name",
		description="Name for the scene. This name will be used during export",
		default="scene"
	)
	
	startFrame: bpy.props.IntProperty(
		name="Start Frame",
		description="Declare the starting point for this scene",
		default=1,
		min=0
	)
	
	endFrame: bpy.props.IntProperty(
		name="End Frame",
		description="Declare the ending point for this scene",
		default=1,
		min=0
	)
	
	enabled: bpy.props.BoolProperty(
		name="Enabled",
		description="Determines if this scene will be rendered in the batch or not",
		default=True
	)