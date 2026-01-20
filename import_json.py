import bpy
from mathutils import Matrix,Vector
from bpy_extras.io_utils import axis_conversion


def overwrite_orientation(axis_up=None, axis_forward=None):
    return {k: v for k, v in locals().items() if v is not None}

def load_json_file(filepath):
    import json
    """Load and parse JSON file"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)
    
def import_curves_from_json(operator, context, filename, filepath,
                            orientation_settings='EMBEDDED',
                            axis_forward='-Z',
                            axis_up='Y',
                            animations_settings='EMBEDDED',
                            shape_keys_settings='EMBEDDED',
                            global_scale=1.0,
                            apply_transform='NONE',
                            ):
    """Main import function - creates curve objects from JSON data"""
    data = load_json_file(filepath)
    curves_data = data.get("curves")
    if not curves_data: 
        operator.report({'INFO'}, f"No curves data found in {filename}")
        return {'CANCELLED'}

    export_data = data.get("export_settings")
    if not export_data:
        orientation_settings = 'EXCLUDE'

    settings = overwrite_orientation(axis_up, axis_forward)
    if orientation_settings == 'EMBEDDED':
        settings = { k: export_data.get(k) for k in ("axis_up", "axis_forward") }

    conversion_matrix = axis_conversion(
        to_forward=settings.get("axis_forward"),
        to_up=settings.get("axis_up")
    ).to_4x4()
    invert_convert_matrix = conversion_matrix.inverted() 

    if apply_transform == 'NONE' or apply_transform == 'LOCATION':
        scale_factor = global_scale
    else:
        invert_convert_matrix = invert_convert_matrix @ Matrix.Scale(global_scale, 4)
        scale_factor = 1.0

    imported_objects = []
    for splines_list in curves_data:
        for spline_data in splines_list:
            curve_obj = create_curve_object(
                context,
                spline_data,
                invert_convert_matrix,
                global_scale,
            )
            curve_obj.scale = Vector.Fill(3, scale_factor)
            imported_objects.append(curve_obj)
    
    return {'FINISHED'}


def create_curve_object(context:bpy.types.Context, spline_data, invert_convert_matrix, scale):
    """Create a single curve object from spline data"""
    curve_name = spline_data.get("name", "Untitled")
    spline_type = spline_data.get("type", "POLY")

    # Create a new curve data block
    curve_data = bpy.data.curves.new(name=curve_name, type="CURVE")
    curve_data.dimensions = '3D'
    
    # Create curve object
    curve_obj = bpy.data.objects.new(curve_name, curve_data)
    context.collection.objects.link(curve_obj)
    
    # Create spline
    spline = curve_data.splines.new(type=spline_type)
    spline.use_cyclic_u = spline_data.get("cyclic_u", False)
    spline.use_cyclic_v = spline_data.get("cyclic_v", False)
    
    # Add points
    points_data = spline_data.get("points", [])
    
    if spline_type == 'BEZIER':
        spline.bezier_points.add(len(points_data) - 1)
    else:
        spline.points.add(len(points_data) - 1)

    for i, point_data in enumerate(points_data):
        position = Vector(point_data.get("position"))
        position = invert_convert_matrix @ position

        if spline_type == 'BEZIER':
            point = spline.bezier_points[i]

            left_handle = Vector(point_data.get("left_handle"))
            left_handle = invert_convert_matrix @ left_handle
            point.handle_left = left_handle
            
            right_handle = Vector(point_data.get("right_handle"))
            right_handle = invert_convert_matrix @ right_handle
            point.handle_right = right_handle
            
            point.co = position
        else:
            point = spline.points[i]
            point.co = (*position, 1.0)
        
        # Set properties
        point.tilt = point_data.get("tilt", 0.0)
        point.radius = point_data.get("radius", 1.0) * scale
    
    # Update the curve
    curve_data.update_tag()
    
    return curve_obj
