from mathutils import Matrix,Vector
from bpy.types import (
    Object,
    Spline,
)
from bpy_extras.io_utils import (
    axis_conversion,
)


def get_export_settings(axis_up=None, axis_forward=None, world_space=None):
    return {k: v for k, v in locals().items() if v is not None}

def prepare_export_objects(objs, settings, scale_factor=1.0):
    """Creates a copy of each object and converts transform according to settings"""
    temp_objs = []
    for obj in objs:
        temp_obj = obj.copy()
        temp_obj.data = obj.data.copy()

        conversion_matrix  = axis_conversion( to_forward=settings["axis_forward"], to_up=settings["axis_up"] ).to_4x4()
        conversion_matrix = conversion_matrix @ Matrix.Scale(scale_factor, 4)

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
                "points": get_point_data(spline),
            }
            # if settings.get("shape_keys"):
            #     spline_data["shape_keys"] = get_shape_key_data(temp_obj)
                
            # if settings.get("animations"):
            #     spline_data["animations"] = get_animation_data(temp_obj)
            
            splines_data.append(spline_data)
        data.append(splines_data)
    return data

def get_point_data(spline: Spline):
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

def export_curve_data(operator, context, filename, filepath,
                      world_space=False,
                      axis_forward='-Z',
                      axis_up='Y',
                      global_scale=1.0,
                      ):
    import json
    import bpy

    objs = context.selected_objects
    settings = get_export_settings(axis_up, axis_forward, world_space)
    temp_objs = prepare_export_objects(objs, settings, global_scale)

    data = {
        "export_settings": settings,
        "curves": prepare_spline_data(temp_objs, settings),
    }
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    operator.report({'INFO'}, f"Exported curve to {filepath}")

    for temp_obj in temp_objs:
        bpy.data.objects.remove(temp_obj[1]) 