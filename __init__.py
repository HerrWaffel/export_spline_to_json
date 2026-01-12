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
    "name": "Export Spline To Json",
    "author": "Quint Vrolijk",
    "description": "",
    "blender": (5, 0, 0),
    "version": (1, 0, 0),
    "location": "File > Import-Export",
    "warning": "",
    "category": "Import-Export",
}

import bpy
import json
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    StringProperty,
)
from bpy.types import (
    Object,
    Operator,
    UILayout,
    Spline,
)
from bpy_extras.io_utils import (
    ExportHelper, 
    orientation_helper, 
    axis_conversion,
)


def prepare_export_objects(objs, settings):
    """Creates a copy of each object and converts transform according to settings"""
    temp_objs = []
    for obj in objs:
        temp_obj = obj.copy()
        temp_obj.data = obj.data.copy()

        conversion_matrix  = axis_conversion( to_forward=settings["axis_forward"], to_up=settings["axis_up"] ).to_4x4()
        temp_obj_matrix = temp_obj.matrix_world if settings["world_space"] else temp_obj.matrix_parent_inverse * temp_obj.matrix_basis
        temp_obj.data.transform( conversion_matrix @ temp_obj_matrix )
        
        temp_objs.append( [obj.name, temp_obj] )
    return temp_objs

def prepare_spline_data(temp_objs, settings):
    """Collects spline data: name, type, length, cyclic_u, cyclic_v, point data, shape_keys, animations"""
    data = []
    for name, temp_obj in temp_objs:
        splines_data = []             
        for spline in temp_obj.data.splines:
            spline_data = {
                "name": name,
                "type": spline.type,
                "length": spline.calc_length(),
                "cyclic_u": spline.use_cyclic_u,
                "cyclic_v": spline.use_cyclic_v,
                "points": get_point_data(spline, settings),
            }
            if settings.get("shape_keys"):
                spline_data["shape_keys"] = get_shape_key_data(temp_obj)
                
            if settings.get("animations"):
                spline_data["animations"] = get_animation_data(temp_obj)
            
            splines_data.append(spline_data)
        data.append(splines_data)
    return data

def get_point_data(spline: Spline, settings):
    """Collects spline point data: tilt, radius, position, (handles*)"""
    points_data = []
    points = spline.points if spline.type != 'BEZIER' else spline.bezier_points
    for point in points:
        point_data = {
            "tilt": point.tilt,
            "radius": point.radius,
            "position": point.co.to_tuple(),
        }
        if spline.type == 'BEZIER':
            point_data['left_handle'] = point.handle_left.to_tuple()
            point_data['right_handle'] = point.handle_right.to_tuple()

        points_data.append(point_data)
    return points_data

# TO DO: add point position, tilt, radius data
def get_shape_key_data(obj: Object):
    shape_key_data = []
    keys_blocks = obj.data.shape_keys.key_blocks
    for key in keys_blocks:
        shape_key_data.append( {
            "relative_key": key.relative_key.name,
            "key_name": key.name,
            "value": key.value,
        })

    return shape_key_data

# TO DO: add animation data: actions, slots
def get_animation_data(obj: Object):
    animation_data = []
    return animation_data

# TO DO: fix scale and rotation for local space, implement apply transform or remove, implement global scale 
@orientation_helper(axis_forward='-Z', axis_up='Y')
class ExportSpline(Operator, ExportHelper):
    """Export spline data to a JSON file"""
    bl_idname = "export_spline.json"
    bl_label = "Export Spline"
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
        self.filepath = bpy.path.ensure_ext(self.filepath, ".json")
        settings = {
            "world_space"   : self.world_space,
            "axis_up"       : self.axis_up,
            "axis_forward"  : self.axis_forward,
            "units"         : context.scene.unit_settings.length_unit
        }

        objs = context.selected_objects
        temp_objs = prepare_export_objects(objs, settings)

        data = {
            "export_settings": settings,
            "splines": prepare_spline_data(temp_objs, feat_export_settings(self) ),
        }
        with open(self.filepath, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        self.report({'INFO'}, f"Exported spline to {self.filepath}")

        for temp_obj in temp_objs:
            bpy.data.objects.remove(temp_obj[1]) 

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def feat_export_settings(operator:ExportSpline):
    settings = {} 
    if operator.export_shape_keys:
        shape_keys_settings = {}
        settings["shape_keys"] = shape_keys_settings
    if operator.export_animations:
        animations_settings = {}
        settings["animations"] = animations_settings
    return settings

def export_panel_main(layout:UILayout, operator:ExportSpline):
    # layout.prop(operator, "apply_transform", text="Apply Transform")
    # layout.prop(operator, "global_scale", text="Scale")
    layout.prop(operator, "world_space", text="World Space")
    layout.prop(operator, "axis_forward", text="Forward")
    layout.prop(operator, "axis_up", text="Up")

def export_panel_animations(layout:UILayout, operator:ExportSpline):
    header, body = layout.panel("JSON_export_animations", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "export_animations", text="")
    header.label(text="Animations")
    if body:
        body.enabled = operator.export_animations
        body.label(text="Unused for now")

def export_panel_shape_keys(layout:UILayout, operator:ExportSpline):
    header, body = layout.panel("JSON_export_shape_keys", default_closed=True)
    header.use_property_split = False
    header.prop(operator, "export_shape_keys", text="")
    header.label(text="Shape Keys")
    if body:
        body.enabled = operator.export_shape_keys
        body.label(text="Unused for now")


def menu_func(self, context):
    self.layout.operator(ExportSpline.bl_idname, text="Export Spline (.json)")


classes = (
    ExportSpline,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()