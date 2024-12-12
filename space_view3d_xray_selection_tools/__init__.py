# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "X-Ray Selection Tools",
    "author": "MarshmallowCirno",
    "version": (4, 7, 0),
    "blender": (4, 3, 0),
    "location": "Toolbar > Selection Tools",
    "description": "Box, lasso and circle selection tools with x-ray",
    "warning": "",
    "category": "3D View",
    "doc_url": "https://gumroad.com/l/DaLdj",
    "tracker_url": "https://blenderartists.org/t/x-ray-selection-tools/1212316",
}


RELOADABLE_MODULES = (
    "types",
    "edge_attr",
    "loop_attr",
    "poly_attr",
    "vert_attr",
    "view3d",
    "timer",
    "geometry_tests",
    "selection_utils",
    "mesh_intersect",
    "object_intersect",
    "object_intersect_box",
    "object_intersect_circle",
    "object_intersect_lasso",
    "object_intersect_shared",
    "mesh_modal",
    "object_modal",
    "mesh_ot_box",
    "mesh_ot_circle",
    "mesh_ot_lasso",
    "mesh_ot_toggle",
    "object_ot_box",
    "object_ot_circle",
    "object_ot_lasso",
    "help",
    "ot_keymap",
    "tools",
    "tools_main",
    "tools_dummy",
    "tools_keymap",
    "tools_utils",
    "preferences",
    "startup",
)

# when bpy is already in local, we know this is not the initial import...
if "bpy" in locals():
    # ...so we need to reload our submodule(s) using importlib
    import importlib

    for module in RELOADABLE_MODULES:
        if module in locals():
            importlib.reload(locals()[module])
else:
    import bpy

    if not bpy.app.background:  # Prevent imports when run in background
        from .functions.mesh_attr import edge_attr, loop_attr, poly_attr, vert_attr
        from .functions import (
            geometry_tests,
            timer,
            view3d,
        )
        from .functions.intersections import selection_utils
        from .functions.intersections.object_intersect import (
            object_intersect_box,
            object_intersect_circle,
            object_intersect_lasso,
            object_intersect_shared,
        )
        from .functions.intersections import mesh_intersect, object_intersect
        from .functions.modals import mesh_modal, object_modal
        from .operators.mesh_ot import mesh_ot_box, mesh_ot_circle, mesh_ot_lasso, mesh_ot_toggle
        from .operators.object_ot import object_ot_box, object_ot_circle, object_ot_lasso
        from .operators import help_ot, ot_keymap
        from . import types, tools, startup, preferences
        from .tools import tools_main, tools_dummy, tools_keymap, tools_utils


import bpy  # noqa


def register():
    if bpy.app.background:
        return
    mesh_ot_box.register()
    mesh_ot_circle.register()
    mesh_ot_lasso.register()
    mesh_ot_toggle.register()
    object_ot_box.register()
    object_ot_circle.register()
    object_ot_lasso.register()
    help_ot.register()
    preferences.register()
    ot_keymap.register()
    tools_main.register()
    tools_dummy.register()
    startup.register()


def unregister():
    if bpy.app.background:
        return
    mesh_ot_box.unregister()
    mesh_ot_circle.unregister()
    mesh_ot_lasso.unregister()
    mesh_ot_toggle.unregister()
    object_ot_box.unregister()
    object_ot_circle.unregister()
    object_ot_lasso.unregister()
    help_ot.unregister()
    preferences.unregister()
    ot_keymap.unregister()
    tools_utils.reset_active_tool()
    tools_main.unregister()
    tools_dummy.unregister()
    startup.unregister()
