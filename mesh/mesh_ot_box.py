import bpy
import gpu
from struct import pack
from gpu_extras.batch import batch_for_shader
from bgl import glEnable, glDisable, GL_BLEND
from ..functions.intersect import select_elems_in_poly
from ..functions.mesh_modal import *


class MESH_OT_select_box_xray(bpy.types.Operator):
    """Select items using box selection with x-ray"""
    bl_idname = "mesh.select_box_xray"
    bl_label = "Box Select X-Ray"
    bl_options = {'REGISTER', 'GRAB_CURSOR'}

    mode: bpy.props.EnumProperty(
        name="Mode",
        description="Default selection mode",
        items=[('SET', "Set", "Set a new selection", 'SELECT_SET', 1),
               ('ADD', "Extend", "Extend existing selection", 'SELECT_EXTEND', 2),
               ('SUB', "Subtract", "Subtract existing selection", 'SELECT_SUBTRACT', 3),
               ('XOR', "Difference", "Inverts existing selection", 'SELECT_DIFFERENCE', 4),
               ('AND', "Intersect", "Intersect existing selection", 'SELECT_INTERSECT', 5)
               ],
        default='SET',
        options={'SKIP_SAVE'}
    )
    alt_mode: bpy.props.EnumProperty(
        name="Alternate Mode",
        description="Alternate selection mode",
        items=[('SET', "Select", "Set a new selection", 'SELECT_SET', 1),
               ('ADD', "Extend Selection", "Extend existing selection", 'SELECT_EXTEND', 2),
               ('SUB', "Deselect", "Subtract existing selection", 'SELECT_SUBTRACT', 3)
               ],
        default='SUB',
        options={'SKIP_SAVE'}
    )
    alt_mode_toggle_key: bpy.props.EnumProperty(
        name="Alternate Mode Toggle Key",
        description="Toggle selection mode by holding this key",
        items=[('CTRL', "CTRL", ""),
               ('ALT', "ALT", ""),
               ('SHIFT', "SHIFT", "")
               ],
        default='SHIFT',
        options={'SKIP_SAVE'}
    )
    wait_for_input: bpy.props.BoolProperty(
        name="Wait for Input",
        description="Wait for mouse input or initialize box selection immediately (usually you "
                    "should enable it when you assign the operator to a keyboard key)",
        default=False,
        options={'SKIP_SAVE'}
    )
    override_global_props: bpy.props.BoolProperty(
        name="Override Global Properties",
        description="Use properties in this keymaps item instead of properties in the global "
                    "addon settings",
        default=False,
        options={'SKIP_SAVE'}
    )
    select_through: bpy.props.BoolProperty(
        name="Select Through",
        description="Select verts, faces and edges laying underneath",
        default=True,
        options={'SKIP_SAVE'}
    )
    select_through_toggle_key: bpy.props.EnumProperty(
        name="Selection Through Toggle Key",
        description="Toggle selection through by holding this key",
        items=[('CTRL', "CTRL", ""),
               ('ALT', "ALT", ""),
               ('SHIFT', "SHIFT", ""),
               ('DISABLED', "DISABLED", "")
               ],
        default='DISABLED',
        options={'SKIP_SAVE'}
    )
    select_through_toggle_type: bpy.props.EnumProperty(
        name="Selection Through Toggle Press / Hold",
        description="Toggle selection through by holding or by pressing key",
        items=[('HOLD', "Holding", ""),
               ('PRESS', "Pressing", "")
               ],
        default='HOLD',
        options={'SKIP_SAVE'}
    )
    default_color: bpy.props.FloatVectorProperty(
        name="Default Color",
        description="Tool color when disabled selection through",
        subtype='COLOR',
        soft_min=0.0,
        soft_max=1.0,
        size=3,
        default=(1.0, 1.0, 1.0),
        options={'SKIP_SAVE'}
    )
    select_through_color: bpy.props.FloatVectorProperty(
        name="Select Through Color",
        description="Tool color when enabled selection through",
        subtype='COLOR',
        soft_min=0.0,
        soft_max=1.0,
        size=3,
        default=(1.0, 1.0, 1.0),
        options={'SKIP_SAVE'}
    )
    show_xray: bpy.props.BoolProperty(
        name="Show X-Ray",
        description="Enable x-ray shading during selection",
        default=True,
        options={'SKIP_SAVE'}
    )
    select_all_edges: bpy.props.BoolProperty(
        name="Select All Edges",
        description="Additionally select edges that are partially inside the selection box, "
                    "not just the ones completely inside the selection box. Works only in "
                    "select through mode",
        default=False,
        options={'SKIP_SAVE'}
    )
    select_all_faces: bpy.props.BoolProperty(
        name="Select All Faces",
        description="Additionally select faces that are partially inside the selection box, "
                    "not just the ones with centers inside the selection box. Works only in "
                    "select through mode",
        default=False,
        options={'SKIP_SAVE'}
    )
    hide_mirror: bpy.props.BoolProperty(
        name="Hide Mirror",
        description="Hide mirror modifiers during selection",
        default=True,
        options={'SKIP_SAVE'}
    )
    hide_solidify: bpy.props.BoolProperty(
        name="Hide Solidify",
        description="Hide solidify modifiers during selection",
        default=True,
        options={'SKIP_SAVE'}
    )
    show_crosshair: bpy.props.BoolProperty(
        name="Show Crosshair",
        description="Show crosshair when wait_for_input is enabled",
        default=True,
        options={'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' and context.mode == 'EDIT_MESH'

    def __init__(self):
        self.stage = None
        self.curr_mode = self.mode

        self.start_mouse_region_x = 0
        self.start_mouse_region_y = 0
        self.last_mouse_region_x = 0
        self.last_mouse_region_y = 0

        self.init_mods = None
        self.init_overlays = None

        self.override_wait_for_input = False
        self.override_selection = False
        self.override_intersect_tests = False

        self.select_through_toggle_key_list = get_select_through_toggle_key_list()

        self.handler = None
        self.crosshair_shader = None
        self.crosshair_batch = None
        self.border_shader = None
        self.border_batch = None
        self.inner_shader = None
        self.inner_batch = None
        self.unif_dash_color = None
        self.unif_gap_color = None
        self.unif_inner_color = None

        # https://docs.blender.org/api/blender2.8/gpu.html#custom-shader-for-dotted-3d-line
        # https://stackoverflow.com/questions/52928678/dashed-line-in-opengl3
        self.crosshair_vertex_shader = '''
            in vec2 pos;
            in float len;
            out float v_Len;
            
            uniform mat4 u_ViewProjectionMatrix;
            uniform float u_X;
            uniform float u_Y;

            void main()
            {
                v_Len = len;
                gl_Position = u_ViewProjectionMatrix * vec4(pos.x + u_X, pos.y + u_Y, 0.0f, 1.0f);
            }
        '''
        self.crosshair_fragment_shader = '''
            in float v_Len;
            out vec4 fragColor;
            
            uniform vec4 u_DashColor;
            uniform vec4 u_GapColor;
            
            float dash_size = 4;
            float gap_size = 4;
            vec4 col = u_DashColor;

            void main()
            {
                if (fract(v_Len/(dash_size + gap_size)) > dash_size/(dash_size + gap_size)) 
                    col = u_GapColor;
                    
                fragColor = col;
            }
        '''
        self.border_vertex_shader = '''
            in vec2 pos;
            in vec2 len;
            out float v_Len;

            uniform mat4 u_ViewProjectionMatrix;
            uniform float u_X;
            uniform float u_Y;
            uniform float u_Height;
            uniform float u_Width;

            void main()
            {
                v_Len = len.x * u_Width + len.y * u_Height;
                gl_Position = u_ViewProjectionMatrix * vec4(pos.x * u_Width + u_X, 
                pos.y * u_Height + u_Y, 0.0f, 1.0f);
            }
        '''
        self.border_fragment_shader = '''
            in float v_Len;
            out vec4 fragColor;

            uniform vec4 u_DashColor;
            uniform vec4 u_GapColor;
            
            float dash_size = 4;
            float gap_size = 4;
            vec4 col = u_DashColor;

            void main()
            {
                if (fract(v_Len/(dash_size + gap_size)) > dash_size/(dash_size + gap_size)) 
                    col = u_GapColor;
                fragColor = col;
            }
        '''
        self.inner_vertex_shader = '''
            in vec2 pos;

            uniform mat4 u_ViewProjectionMatrix;
            uniform float u_X;
            uniform float u_Y;
            uniform float u_Height;
            uniform float u_Width;

            void main()
            {
                gl_Position = u_ViewProjectionMatrix * vec4(pos.x * u_Width + u_X, 
                pos.y * u_Height + u_Y, 0.0f, 1.0f);
            }
        '''
        self.inner_fragment_shader = '''
            out vec4 fragColor;

            uniform vec4 u_Color;
            
            void main()
            {
                fragColor = u_Color;
            }
        '''

    def invoke(self, context, event):
        set_properties(self)

        self.override_intersect_tests = \
            self.select_all_faces and context.tool_settings.mesh_select_mode[2] or \
            self.select_all_edges and context.tool_settings.mesh_select_mode[1]

        self.override_selection = \
            self.select_through_toggle_key != 'DISABLED' or \
            self.alt_mode_toggle_key != 'SHIFT' or \
            self.alt_mode != 'SUB' or \
            not self.select_through and self.default_color[:] != (1.0, 1.0, 1.0) or \
            self.select_through and self.select_through_color[:] != (1.0, 1.0, 1.0) or \
            self.override_intersect_tests

        self.override_wait_for_input = \
            not self.show_crosshair or \
            self.override_selection

        self.init_mods = gather_modifiers(self, context)  # save initial modifier states
        self.init_overlays = gather_overlays(context)  # save initial x-ray overlay states

        # sync operator properties with current shading
        sync_properties(self, context)

        # hide modifiers and enable x-ray overlays
        if self.select_through:
            toggle_overlays(self, context)
            toggle_modifiers(self)

        context.window_manager.modal_handler_add(self)

        # jump to
        if self.wait_for_input and self.override_wait_for_input:
            self.begin_custom_wait_for_input_stage(context, event)
        elif self.override_selection:
            self.begin_custom_selection_stage(context, event)
        else:
            self.invoke_inbuilt_box_select()

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.stage == 'CUSTOM_WAIT_FOR_INPUT':
            # update shader
            if event.type == 'MOUSEMOVE':
                self.update_shader_position(context, event)

            # toggle modifiers and overlays
            if event.type in self.select_through_toggle_key_list:
                if event.value in {'PRESS', 'RELEASE'} and \
                        self.select_through_toggle_type == 'HOLD' or \
                        event.value == 'PRESS' and \
                        self.select_through_toggle_type == 'PRESS':
                    self.select_through = not self.select_through
                    toggle_overlays(self, context)
                    toggle_modifiers(self)
                    update_shader_color(self, context)

            # finish stage
            if event.value == 'PRESS' and event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'}:
                self.finish_custom_wait_for_input_stage(context)
                toggle_alt_mode(self, event)
                if self.override_selection:
                    self.begin_custom_selection_stage(context, event)
                else:
                    self.invoke_inbuilt_box_select()

        if self.stage == 'CUSTOM_SELECTION':
            # update shader
            if event.type == 'MOUSEMOVE':
                self.update_shader_position(context, event)

            # toggle modifiers and overlays
            if event.type in self.select_through_toggle_key_list:
                if event.value in {'PRESS', 'RELEASE'} and \
                        self.select_through_toggle_type == 'HOLD' or \
                        event.value == 'PRESS' and \
                        self.select_through_toggle_type == 'PRESS':
                    self.select_through = not self.select_through
                    toggle_overlays(self, context)
                    toggle_modifiers(self)
                    update_shader_color(self, context)

            # finish stage
            if event.value in {'RELEASE'} and \
                    event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE'}:
                self.finish_custom_selection_stage(context)
                if self.override_intersect_tests and self.select_through:
                    self.begin_custom_intersect_tests(context, )
                    self.finish_modal(context)
                    bpy.ops.ed.undo_push(message="Box Select")
                    return {'FINISHED'}
                else:
                    self.exec_inbuilt_box_select()
                    self.finish_modal(context)
                    bpy.ops.ed.undo_push(message="Box Select")
                    return {'FINISHED'}

        if self.stage == 'INBUILT_OP':
            # inbuilt op was finished, now finish modal
            if event.value == 'RELEASE':
                self.finish_modal(context)
                return {'FINISHED'}

        # cancel modal
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            if self.stage == 'CUSTOM_WAIT_FOR_INPUT':
                self.finish_custom_wait_for_input_stage(context)
            elif self.stage == 'CUSTOM_SELECTION':
                self.finish_custom_selection_stage(context)
            self.finish_modal(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def begin_custom_wait_for_input_stage(self, context, event):
        """Set status text, draw wait_for_input shader"""
        self.stage = 'CUSTOM_WAIT_FOR_INPUT'
        enum_items = self.properties.bl_rna.properties["mode"].enum_items
        curr_mode_name = enum_items[self.curr_mode].name
        enum_items = self.properties.bl_rna.properties["alt_mode"].enum_items
        alt_mode_name = enum_items[self.alt_mode].name
        status_text = "RMB, ESC: Cancel  |  LMB: %s  |  %s+LMB: %s" \
                      % (curr_mode_name, self.alt_mode_toggle_key, alt_mode_name)
        if self.select_through_toggle_key != 'DISABLED':
            status_text += "  |  %s: Toggle Select Through" % self.select_through_toggle_key
        context.workspace.status_text_set(text=status_text)
        if self.show_crosshair:
            self.build_crosshair_shader(context)
            self.handler = context.space_data.draw_handler_add(
                self.draw_crosshair_shader, (), 'WINDOW', 'POST_PIXEL')
            self.update_shader_position(context, event)

    def finish_custom_wait_for_input_stage(self, context):
        """Restore status text, remove wait_for_input shader"""
        self.wait_for_input = False
        context.workspace.status_text_set(text=None)
        if self.show_crosshair:
            context.space_data.draw_handler_remove(self.handler, 'WINDOW')
            context.region.tag_redraw()

    def begin_custom_selection_stage(self, context, event):
        self.stage = 'CUSTOM_SELECTION'
        status_text = "RMB, ESC: Cancel"
        if self.select_through_toggle_key != 'DISABLED':
            status_text += "  |  %s: Toggle Select Through" % self.select_through_toggle_key
        context.workspace.status_text_set(text=status_text)

        self.start_mouse_region_x = event.mouse_region_x
        self.start_mouse_region_y = event.mouse_region_y
        self.build_box_shader()
        self.handler = context.space_data.draw_handler_add(
            self.draw_box_shader, (), 'WINDOW', 'POST_PIXEL')
        self.update_shader_position(context, event)

    def finish_custom_selection_stage(self, context):
        context.workspace.status_text_set(text=None)
        context.space_data.draw_handler_remove(self.handler, 'WINDOW')
        context.region.tag_redraw()

    def invoke_inbuilt_box_select(self):
        self.stage = 'INBUILT_OP'
        bpy.ops.view3d.select_box('INVOKE_DEFAULT', mode=self.curr_mode,
                                  wait_for_input=self.wait_for_input)

    def exec_inbuilt_box_select(self):
        # get selection rectangle coordinates
        xmin = min(self.start_mouse_region_x, self.last_mouse_region_x)
        xmax = max(self.start_mouse_region_x, self.last_mouse_region_x)
        ymin = min(self.start_mouse_region_y, self.last_mouse_region_y)
        ymax = max(self.start_mouse_region_y, self.last_mouse_region_y)
        bpy.ops.view3d.select_box(mode=self.curr_mode, wait_for_input=False,
                                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

    def begin_custom_intersect_tests(self, context):
        # get selection rectangle coordinates
        xmin = min(self.start_mouse_region_x, self.last_mouse_region_x)
        xmax = max(self.start_mouse_region_x, self.last_mouse_region_x)
        ymin = min(self.start_mouse_region_y, self.last_mouse_region_y)
        ymax = max(self.start_mouse_region_y, self.last_mouse_region_y)
        poly = (xmin, xmax, ymin, ymax)

        # do selection
        select_elems_in_poly(context, mode=self.curr_mode, shape=0, poly=poly,
                             select_all_edges=self.select_all_edges,
                             select_all_faces=self.select_all_faces)

    def finish_modal(self, context):
        restore_overlays(self, context)
        restore_modifiers(self)

    def update_shader_position(self, context, event):
        self.last_mouse_region_x = event.mouse_region_x
        self.last_mouse_region_y = event.mouse_region_y
        context.region.tag_redraw()

    def build_crosshair_shader(self, context):
        width = context.region.width
        height = context.region.height

        vertices = ((0, -height),
                    (0, height),
                    (-width, 0),
                    (width, 0))
        lengths = (0, 2 * height, 0, 2 * width)

        self.crosshair_shader = gpu.types.GPUShader(self.crosshair_vertex_shader,
                                                    self.crosshair_fragment_shader)
        self.crosshair_batch = batch_for_shader(self.crosshair_shader, 'LINES', {"pos": vertices,
                                                                                 "len": lengths})
        self.unif_dash_color = self.crosshair_shader.uniform_from_name("u_DashColor")
        self.unif_gap_color = self.crosshair_shader.uniform_from_name("u_GapColor")

    def draw_crosshair_shader(self):
        matrix = gpu.matrix.get_projection_matrix()
        gap_color = (0.0, 0.0, 0.0, 1.0)
        if self.select_through:
            dash_color = (*self.select_through_color, 1)
        else:
            dash_color = (*self.default_color, 1)

        self.crosshair_shader.bind()
        self.crosshair_shader.uniform_float("u_ViewProjectionMatrix", matrix)
        self.crosshair_shader.uniform_float("u_X", self.last_mouse_region_x)
        self.crosshair_shader.uniform_float("u_Y", self.last_mouse_region_y)
        self.crosshair_shader.uniform_vector_float(self.unif_dash_color, pack("4f", *dash_color),
                                                   4)
        self.crosshair_shader.uniform_vector_float(self.unif_gap_color, pack("4f", *gap_color), 4)
        self.crosshair_batch.draw(self.crosshair_shader)

    def build_box_shader(self):
        vertices = ((0, 0), (1, 0), (1, 1), (0, 1), (0, 0))
        lengths = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))
        self.border_shader = gpu.types.GPUShader(self.border_vertex_shader,
                                                 self.border_fragment_shader)
        self.border_batch = batch_for_shader(self.border_shader, 'LINE_STRIP', {"pos": vertices,
                                                                                "len": lengths})
        self.unif_dash_color = self.border_shader.uniform_from_name("u_DashColor")
        self.unif_gap_color = self.border_shader.uniform_from_name("u_GapColor")

        vertices = ((0, 0), (1, 0), (0, 1), (1, 1))
        self.inner_shader = gpu.types.GPUShader(self.inner_vertex_shader,
                                                self.inner_fragment_shader)
        self.inner_batch = batch_for_shader(self.inner_shader, 'TRI_STRIP', {"pos": vertices})
        self.unif_inner_color = self.inner_shader.uniform_from_name("u_Color")

    def draw_box_shader(self):
        matrix = gpu.matrix.get_projection_matrix()
        gap_color = (0.0, 0.0, 0.0, 1.0)
        if self.select_through:
            dash_color = (*self.select_through_color, 1)
            inner_color = (*self.select_through_color, 0.04)
        else:
            dash_color = (*self.default_color, 1)
            inner_color = (*self.default_color, 0.04)

        width = self.last_mouse_region_x - self.start_mouse_region_x
        height = self.last_mouse_region_y - self.start_mouse_region_y

        self.border_shader.bind()
        self.border_shader.uniform_float("u_ViewProjectionMatrix", matrix)
        self.border_shader.uniform_float("u_X", self.start_mouse_region_x)
        self.border_shader.uniform_float("u_Y", self.start_mouse_region_y)
        self.border_shader.uniform_float("u_Height", height)
        self.border_shader.uniform_float("u_Width", width)
        self.border_shader.uniform_vector_float(self.unif_dash_color, pack("4f", *dash_color), 4)
        self.border_shader.uniform_vector_float(self.unif_gap_color, pack("4f", *gap_color), 4)
        self.border_batch.draw(self.border_shader)

        glEnable(GL_BLEND)
        self.inner_shader.bind()
        self.inner_shader.uniform_float("u_ViewProjectionMatrix", matrix)
        self.inner_shader.uniform_float("u_X", self.start_mouse_region_x)
        self.inner_shader.uniform_float("u_Y", self.start_mouse_region_y)
        self.inner_shader.uniform_float("u_Height", height)
        self.inner_shader.uniform_float("u_Width", width)
        self.inner_shader.uniform_vector_float(self.unif_inner_color, pack("4f", *inner_color), 4)
        self.inner_batch.draw(self.inner_shader)
        glDisable(GL_BLEND)


classes = (
    MESH_OT_select_box_xray,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
