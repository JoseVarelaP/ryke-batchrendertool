import bpy
from datetime import datetime

class RYK_OP_RenderAllScenes(bpy.types.Operator):
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
		scene.rykbatchrender.IsRendering = True
		
	def render_complete(self, scene, depsgraph):
		self.render_queue.pop(0)
		self.rendering = False
		
	def render_cancel(self, scene, depsgraph):
		self.cancel_render = True
		print("RENDER CANCEL")
		scene.rykbatchrender.IsRendering = False
		
	def render_post(self, scene, despgraph):
		# Get the current frame that we're in, and report the current progress from that.
		curFrame = scene.frame_current
		curFrameInSequence = (curFrame - self.render_queue[0]['startFrame'])
		lastFrameInSequence = (self.render_queue[0]['endFrame'] - self.render_queue[0]['startFrame'])
		
		scene.rykbatchrender.UIcurRenderProgress = ( curFrameInSequence/lastFrameInSequence )
		scene.rykbatchrender.UIcurStatus = "Rendering frame {} of {} ({:3.2f}%)".format(
			curFrameInSequence+1, lastFrameInSequence+1, ( curFrameInSequence/lastFrameInSequence ) * 100
		)
		
	def execute(self, context):
		self.cancel_render = False
		self.rendering = False
		self.render_queue = []
		
		## Update UI Info
		self.TIMERStartTime = datetime.now()
		context.scene.rykbatchrender.UIcurRenderProgress = 0.0
		context.scene.rykbatchrender.UIcurScene = ""
		context.scene.rykbatchrender.UIcurStatus = ""
		context.scene.rykbatchrender.UITotalTimeSpent = ""
		context.scene.rykbatchrender.CurJob = -1
		
		#################################
		
		## Time to fill in the data.
		for scene in context.scene.ScenesDB:
			print(scene['enabled'])
			if scene['enabled']:
				self.render_queue.append(scene)
		
		self.total = len(self.render_queue)
		
		context.scene.rykbatchrender.TotalJobs = self.total
		
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
			context.scene.rykbatchrender.IsRendering = False
			print("CANCELLED")
			return {'CANCELLED'}
		elif event.type == 'TIMER':
			## Update the total time.
			context.scene.rykbatchrender.UITotalTimeSpent = str(datetime.now() - self.TIMERStartTime)
			
			if len(self.render_queue) == 0 or self.cancel_render is True:
				
				# Remove render callbacks
				bpy.app.handlers.render_init.clear()
				bpy.app.handlers.render_complete.clear()
				bpy.app.handlers.render_cancel.clear()
				bpy.app.handlers.render_post.clear()
				
				# Remove timer
				context.window_manager.event_timer_remove(self.timer_event)
				
				bpy.types.RenderSettings.use_lock_interface = False
				context.scene.rykbatchrender.IsRendering = False
				
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
				bpy.context.scene.render.filepath = "{0}{1}\\".format(context.scene.rykbatchrender.OutputFolderLocation,currentscene['name'])
				
				timestart = str(currentscene['startFrame'])
				timeend = str(currentscene['endFrame'])
				scenename = currentscene['name']
				
				## Update UI Info
				sc.rykbatchrender.UIcurScene = scenename
				sc.rykbatchrender.CurJob = (self.total - len(self.render_queue)) / self.total
				sc.rykbatchrender.JobsLeft = "{} {} completed of {}.".format(self.total - len(self.render_queue), "job" if (self.total - len(self.render_queue)) == 1 else "jobs" , self.total)
				print(sc.rykbatchrender.CurJob)
				
				# And now, render!
				bpy.ops.render.render('INVOKE_DEFAULT', animation=True, write_still=True)
			
		return {"PASS_THROUGH"}