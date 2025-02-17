# pyright: reportAttributeAccessIssue = false
import bpy

from .. import addon_info

me_keyboard_keymap: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []
me_mouse_keymap: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []
ob_keyboard_keymap: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []
ob_mouse_keymap: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []
toggles_keymap: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def _register_me_keyboard_keymap():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Mesh", space_type='EMPTY')

        kmi = km.keymap_items.new("mesh.select_lasso_xray", 'L', 'PRESS')
        kmi.properties.mode = 'ADD'
        kmi.properties.wait_for_input = True
        me_keyboard_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_circle_xray", 'C', 'PRESS')
        kmi.properties.mode = 'ADD'
        kmi.properties.wait_for_input = True
        me_keyboard_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_box_xray", 'B', 'PRESS')
        kmi.properties.mode = 'ADD'
        kmi.properties.wait_for_input = True
        me_keyboard_keymap.append((km, kmi))


def _register_me_mouse_keymap():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Mesh", space_type='EMPTY')

        kmi = km.keymap_items.new("mesh.select_lasso_xray", 'LEFTMOUSE', 'CLICK_DRAG', ctrl=True, shift=True)
        kmi.properties.mode = 'SUB'
        me_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_lasso_xray", 'LEFTMOUSE', 'CLICK_DRAG', ctrl=True)
        kmi.properties.mode = 'ADD'
        me_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_box_xray", 'RIGHTMOUSE', 'CLICK_DRAG', ctrl=True)
        kmi.properties.mode = 'SUB'
        me_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_box_xray", 'RIGHTMOUSE', 'CLICK_DRAG', shift=True)
        kmi.properties.mode = 'ADD'
        me_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_box_xray", 'RIGHTMOUSE', 'CLICK_DRAG')
        kmi.properties.mode = 'SET'
        me_mouse_keymap.append((km, kmi))


def _register_ob_keyboard_keymap():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Object Mode", space_type='EMPTY')

        kmi = km.keymap_items.new("object.select_lasso_xray", 'L', 'PRESS')
        kmi.properties.mode = 'ADD'
        kmi.properties.wait_for_input = True
        ob_keyboard_keymap.append((km, kmi))

        kmi = km.keymap_items.new("object.select_circle_xray", 'C', 'PRESS')
        kmi.properties.mode = 'ADD'
        kmi.properties.wait_for_input = True
        ob_keyboard_keymap.append((km, kmi))

        kmi = km.keymap_items.new("object.select_box_xray", 'B', 'PRESS')
        kmi.properties.mode = 'ADD'
        kmi.properties.wait_for_input = True
        ob_keyboard_keymap.append((km, kmi))


def _register_ob_mouse_keymap():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Object Mode", space_type='EMPTY')

        kmi = km.keymap_items.new("object.select_lasso_xray", 'LEFTMOUSE', 'CLICK_DRAG', ctrl=True, shift=True)
        kmi.properties.mode = 'SUB'
        ob_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("object.select_lasso_xray", 'LEFTMOUSE', 'CLICK_DRAG', ctrl=True)
        kmi.properties.mode = 'ADD'
        ob_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("object.select_box_xray", 'RIGHTMOUSE', 'CLICK_DRAG', ctrl=True)
        kmi.properties.mode = 'SUB'
        ob_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("object.select_box_xray", 'RIGHTMOUSE', 'CLICK_DRAG', shift=True)
        kmi.properties.mode = 'ADD'
        ob_mouse_keymap.append((km, kmi))

        kmi = km.keymap_items.new("object.select_box_xray", 'RIGHTMOUSE', 'CLICK_DRAG')
        kmi.properties.mode = 'SET'
        ob_mouse_keymap.append((km, kmi))


def _register_toggles_keymap():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Mesh", space_type='EMPTY')

        kmi = km.keymap_items.new(
            "mesh.select_tools_xray_toggle_select_backfacing", 'X', 'PRESS', ctrl=True, shift=True, alt=True
        )
        toggles_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_tools_xray_toggle_mesh_behavior", 'X', 'PRESS', ctrl=True, shift=True)
        toggles_keymap.append((km, kmi))

        kmi = km.keymap_items.new("mesh.select_tools_xray_toggle_select_through", 'X', 'PRESS', ctrl=True, alt=True)
        toggles_keymap.append((km, kmi))


def _unregister_me_keyboard_keymap():
    for km, kmi in me_keyboard_keymap:
        km.keymap_items.remove(kmi)
    me_keyboard_keymap.clear()


def _unregister_me_mouse_keymap():
    for km, kmi in me_mouse_keymap:
        km.keymap_items.remove(kmi)
    me_mouse_keymap.clear()


def _unregister_ob_keyboard_keymap():
    for km, kmi in ob_keyboard_keymap:
        km.keymap_items.remove(kmi)
    ob_keyboard_keymap.clear()


def _unregister_ob_mouse_keymap():
    for km, kmi in ob_mouse_keymap:
        km.keymap_items.remove(kmi)
    ob_mouse_keymap.clear()


def _unregister_toggles_keymap():
    for km, kmi in toggles_keymap:
        km.keymap_items.remove(kmi)
    toggles_keymap.clear()


def toggle_me_keyboard_keymap(_pg: bpy.types.PropertyGroup, _context: bpy.types.Context):
    if addon_info.get_preferences().keymaps.is_mesh_keyboard_keymap_enabled:
        _register_me_keyboard_keymap()
    else:
        _unregister_me_keyboard_keymap()


def toggle_me_mouse_keymap(_pg: bpy.types.PropertyGroup, _context: bpy.types.Context):
    if addon_info.get_preferences().keymaps.is_mesh_mouse_keymap_enabled:
        _register_me_mouse_keymap()
    else:
        _unregister_me_mouse_keymap()


def toggle_ob_keyboard_keymap(_pg: bpy.types.PropertyGroup, _context: bpy.types.Context):
    if addon_info.get_preferences().keymaps.is_object_keyboard_keymap_enabled:
        _register_ob_keyboard_keymap()
    else:
        _unregister_ob_keyboard_keymap()


def toggle_ob_mouse_keymap(_pg: bpy.types.PropertyGroup, _context: bpy.types.Context):
    if addon_info.get_preferences().keymaps.is_object_mouse_keymap_enabled:
        _register_ob_mouse_keymap()
    else:
        _unregister_ob_mouse_keymap()


def toggle_toggles_keymap(_pg: bpy.types.PropertyGroup, _context: bpy.types.Context):
    if addon_info.get_preferences().keymaps.is_toggles_keymap_enabled:
        _register_toggles_keymap()
    else:
        _unregister_toggles_keymap()


def register():
    if addon_info.get_preferences().keymaps.is_mesh_mouse_keymap_enabled:
        _register_me_mouse_keymap()
    if addon_info.get_preferences().keymaps.is_mesh_keyboard_keymap_enabled:
        _register_me_keyboard_keymap()
    if addon_info.get_preferences().keymaps.is_object_mouse_keymap_enabled:
        _register_ob_mouse_keymap()
    if addon_info.get_preferences().keymaps.is_object_keyboard_keymap_enabled:
        _register_ob_keyboard_keymap()
    if addon_info.get_preferences().keymaps.is_toggles_keymap_enabled:
        _register_toggles_keymap()


def unregister():
    _unregister_me_mouse_keymap()
    _unregister_me_keyboard_keymap()
    _unregister_ob_mouse_keymap()
    _unregister_ob_keyboard_keymap()
    _unregister_toggles_keymap()
