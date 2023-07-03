import bpy
import os
addon_name = os.path.basename(os.path.dirname(__file__))

from .info import addon_id
from .classes_manager import CLSManager

class GREHelper_PT_addon_prefs(bpy.types.AddonPreferences):
    bl_idname = addon_name

    gr_exporter_path : bpy.props.StringProperty(
        name = "GR Exporter Path",
        description = "Path to the Folder of the Game Resources Exporter, used to read properties",
        subtype = "FILE_PATH",
        # update = update_gr_exporter_path,
        )

    def draw(self, context):
        layout = self.layout
        
        row = layout.row(align=True)
        row.prop(self, "gr_exporter_path")
        
# get addon preferences
def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(addon_name)
    return getattr(addon, "preferences", None)

def get_gr_exporter_path():
    return get_addon_preferences().gr_exporter_path