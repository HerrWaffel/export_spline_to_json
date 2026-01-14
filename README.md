# Blender Addon - Export Curve to JSON
A simple exporter to write curve data to JSON. 
In the export panel, you can convert to your desired forward and up axes and specify whether the positions are in world or local space.

Currently, it exports the following data:
- Export Settings
  - world space coordinates
  - up & forward axis
  - units
- Curves Data
  - object name
  - type (Poly, Bezier, Nurbs)
  - spline length
  - cyclic u & cyclic v
  - points data
    - tilt
    - radius
    - position
    - handles (only if type is 'Bezier' )

For now, animations and shape keys are not included.

## Installation

To install this addon, do the following:

1. Download the latest release from the [releases page](https://github.com/HerrWaffel/export_curve_to_json/releases).
2. In Blender, go to Edit > Preferences > Add-ons.
3. Click the "Install" button, and select the downloaded .zip file.
4. Enable the addon by checking the checkbox next to its name.


## Usage

To use this addon, do the following:

1. Select a curve or curves you want to export.
2. Go to File->Export->Export Spline. (if this option is disabled, check if you only have curve objects selected)
3. Select your desired export settings.
4. Change the filename and filepath.
5. And finally press 'Export Curve'.


## Troubleshooting

If you experience any issues with this addon, try the following:

1. Make sure you have installed the latest version of the addon.
2. Check the Blender console (Window > Toggle System Console) for any error messages.
3. If you still can't resolve the issue, open an issue on the [GitHub repository](https://github.com/HerrWaffel/export_curve_to_json/issues).


## License

This addon is released under the GNU General Public License (GPL). See [LICENSE](LICENSE) for details.