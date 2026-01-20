# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

if "bpy" in locals():
    import importlib
    import sys
    importlib.reload(sys.modules[__name__])

bl_info = {
    "name": "Export Curve To Json",
    "author": "Quint Vrolijk",
    "description": "",
    "blender": (5, 0, 0),
    "version": (1, 0, 2),
    "location": "File > Import-Export",
    "warning": "",
    "category": "Import-Export",
}

import bpy
import json
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
    OperatorFileListElement,
    UILayout,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper, 
    orientation_helper, 
)


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportCurve(Operator, ImportHelper):
    """Import curve data using JSON"""
    bl_idname = "import_curve.json"
    bl_label = "Import Curve"
    bl_options = {'UNDO','PRESET'}

    import_options = [
        ('EMBEDDED', "Embedded", "Use embedded data for importing"),
        ('OVERWRITE', "Overwrite", "Include data with custom settings"),
        ('EXCLUDE', "Exclude", ""),
    ]
    
    filename_ext = ".json"
    filter_glob: StringProperty( default="*.json", options={'HIDDEN'}, maxlen=255,)
    directory: StringProperty( subtype='DIR_PATH', options={'HIDDEN', 'SKIP_PRESET'},)
    files: CollectionProperty( name="File Path", type=OperatorFileListElement, options={'HIDDEN', 'SKIP_PRESET'},)
    
    orientation_settings: EnumProperty( items=import_options, default='EMBEDDED', name="Orientation", description="Overwrite embedded export settings for axes and units")
    animations_settings : EnumProperty( items=import_options, default='EMBEDDED', name="Animations", description="Import curve animations")
    shape_keys_settings : EnumProperty( items=import_options, default='EMBEDDED', name="Shape Keys", description="Import curve shape keys")
    
    global_scale: FloatProperty(name="Scale", default=1.0, description="Scale all positions and radia")
    apply_transform: EnumProperty(
        items=[
            ('NONE', "None", "Apply no object transform (Local Space)"),
            ('APPLY_ALL', "Apply All", "Apply location, rotation, scale. (World Space)"),
            ('LOCATION', "Location", "Apply location transform"),
            ('SCALE', "Scale", "Apply scale transform"),
        ],
        name="Apply Transform",
        default='NONE',
    )


    @classmethod
    def poll(cls, context):
        return context.scene is not None
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        import_panel_main(self, layout)
        import_panel_orientation(self, layout)
        import_panel_animations(self, layout)
        import_panel_shape_keys(self, layout)
    
    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "directory", "filepath", "files", "filename_ext"))
        from . import import_json
        import os

        if self.files:
            ret = {'CANCELLED'}
            for file in self.files:
                path = os.path.join(self.directory, file.name)
                if import_json.import_curves_from_json(self, context, filename=file.name, filepath=path, **keywords) == {'FINISHED'}:
                    ret = {'FINISHED'}
            return ret
        else:
            return import_json.import_curves_from_json(self, context, self.filename, self.filepath, **keywords)
        
    def invoke(self, context, event):
        return self.invoke_popup(context)


def import_panel_main(operator:ImportCurve, layout:UILayout):
    layout.prop(operator, "apply_transform", text="Apply Transform")
    layout.prop(operator, "global_scale", text="Scale")

def import_panel_orientation(operator:ImportCurve, layout:UILayout):
    header, body = layout.panel("JSON_import_orientation", default_closed=True)
    header.use_property_split = False
    header.label(text="Orientation")
    header.prop(operator, "orientation_settings", text="")
    if body:
        body.enabled = operator.orientation_settings == 'OVERWRITE'
        body.prop(operator, "axis_forward", text="Forward")
        body.prop(operator, "axis_up", text="Up")

def import_panel_animations(operator:ImportCurve, layout:UILayout):
    header, body = layout.panel("JSON_import_animations", default_closed=True)
    header.use_property_split = False
    header.label(text="Animations")
    header.prop(operator, "animations_settings", text="")
    if body:
        body.enabled = (operator.animations_settings == 'OVERWRITE')

def import_panel_shape_keys(operator:ImportCurve, layout:UILayout):
    header, body = layout.panel("JSON_import_shape_keys", default_closed=True)
    header.use_property_split = False
    header.label(text="Shape Keys")
    header.prop(operator, "shape_keys_settings", text="")
    if body:
        body.enabled = operator.shape_keys_settings == 'OVERWRITE'


# TO DO: fix scale and rotation for local space, implement apply transform or remove, implement global scale 
@orientation_helper(axis_forward='-Z', axis_up='Y')
class ExportCurve(Operator, ExportHelper):
    """Export curve data to a JSON file"""
    bl_idname = "export_curve.json"
    bl_label = "Export Curve"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".json"
    filename = "Untitled.json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'}, maxlen=255,)

    world_space: BoolProperty(name="World Space", description="Export positions in world space instead of local space", default=False,)
    # export_animations: BoolProperty(name="Export Animation", description="Include animations in the export", default=False)
    # export_shape_keys: BoolProperty(name="Export Shape Keys", description="Include shape keys in the export", default=False)
    # apply_transform: EnumProperty(
    #     items=[
    #         ('NONE', "None", "Apply no object transform (Local Space)"),
    #         ('APPLY_ALL', "Apply All", "Apply location, rotation, scale. (World Space)"),
    #         ('LOCATION', "Location", "Apply location transform"),
    #         ('ROTATION', "Rotation", "Apply rotation transform"),
    #         ('SCALE', "Scale", "Apply scale transform"),
    #         ('ROT_SCALE', "Rotation & Scale", "Apply rotation and scale"),
    #     ],
    #     name="Apply Transform",
    #     default='NONE',
    # )
    # global_scale: FloatProperty(name="Scale", description="Scales the transform by this value",default=1.0)

    @classmethod
    def poll(cls, context):
        return context.object is not None and all(obj.type == 'CURVE' for obj in context.selected_objects)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        export_panel_main(layout, self)
        # export_panel_animations(layout, self)
        # export_panel_shape_keys(layout, self)

    def execute(self, context):
        from . import export_json

        self.filepath = bpy.path.ensure_ext(self.filepath, ".json")
        settings = {
            "world_space"   : self.world_space,
            "axis_up"       : self.axis_up,
            "axis_forward"  : self.axis_forward,
            "units"         : context.scene.unit_settings.length_unit
        }

        objs = context.selected_objects
        temp_objs = export_json.prepare_export_objects(objs, settings)

        data = {
            "export_settings": settings,
            "curves": export_json.prepare_spline_data(temp_objs, feat_export_settings(self) ),
        }
        with open(self.filepath, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        self.report({'INFO'}, f"Exported curve to {self.filepath}")

        for temp_obj in temp_objs:
            bpy.data.objects.remove(temp_obj[1]) 

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def feat_export_settings(operator:ExportCurve):
    settings = {} 
    # if operator.export_shape_keys:
    #     shape_keys_settings = {}
    #     settings["shape_keys"] = shape_keys_settings
    # if operator.export_animations:
    #     animations_settings = {}
    #     settings["animations"] = animations_settings
    return settings

def export_panel_main(layout:UILayout, operator:ExportCurve):
    # layout.prop(operator, "apply_transform", text="Apply Transform")
    # layout.prop(operator, "global_scale", text="Scale")
    layout.prop(operator, "world_space", text="World Space")
    layout.prop(operator, "axis_forward", text="Forward")
    layout.prop(operator, "axis_up", text="Up")

def export_panel_animations(layout:UILayout, operator:ExportCurve):
    header, body = layout.panel("JSON_export_animations", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "export_animations", text="")
    header.label(text="Animations")
    if body:
        body.enabled = operator.export_animations
        body.label(text="Unused for now")

def export_panel_shape_keys(layout:UILayout, operator:ExportCurve):
    header, body = layout.panel("JSON_export_shape_keys", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "export_shape_keys", text="")
    header.label(text="Shape Keys")
    if body:
        body.enabled = operator.export_shape_keys
        body.label(text="Unused for now")


def menu_func_export(self, context):
    self.layout.operator(ExportCurve.bl_idname, text="Export Curve (.json)")


def menu_func_import(self, context):
    self.layout.operator(ImportCurve.bl_idname, text="Import Curve (.json)")


classes = (
    ImportCurve,
    ExportCurve,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()