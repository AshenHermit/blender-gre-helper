import importlib, sys

import bpy, os
from . import gre_helper
from . import operators
from pathlib import Path
from bpy.app.handlers import persistent

from .info import addon_id

# Python doesn't reload package sub-modules at the same time as __init__.py!
CFD = Path(__file__).parent.resolve()
for file in CFD.rglob("*.py"):
    if str(file.resolve()) == str(Path(__file__).resolve()): continue
    module_name = file.with_suffix("").relative_to(CFD).as_posix().replace("/", ".")
    module_name = module_name.replace(".__init__", "")
    module_name = f"{__name__}.{module_name}"
    module = sys.modules.get(module_name)
    if module: importlib.reload(module)

# clear out any scene update funcs hanging around, e.g. after a script reload
for collection in [bpy.app.handlers.depsgraph_update_post, bpy.app.handlers.load_post]:
	for func in collection:
		if func.__module__.startswith(__name__):
			collection.remove(func)

bl_info = {
    "name": "Game Resources Exporter Helper",
    "author": "Ashen Hermit",
    "version": (0, 8),
    "blender": (3, 1, 0),
    "location": "Object",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Interface"
}

from .classes_manager import CLSManager
from .res_classes_parser import res_classes_parser
from .res_panels_generator import ResPanelsGenerator
from .addon_prefs import GREHelper_PT_addon_prefs

panels_generator:ResPanelsGenerator = None

@persistent
def scene_loaded(_):
    if not panels_generator: return
    panels_generator.on_project_loaded()


def register():
    global panels_generator
    bpy.utils.register_class(GREHelper_PT_addon_prefs)

    res_classes_parser.parse_classes()
    panels_generator = ResPanelsGenerator(res_classes_parser)
    panels_generator.generate_panels()

    CLSManager.register()
    bpy.app.handlers.load_post.append(scene_loaded)

def unregister():
    CLSManager.unregister()
    bpy.utils.unregister_class(GREHelper_PT_addon_prefs)
    bpy.app.handlers.load_post.remove(scene_loaded)

if __name__ == "__main__":
    register()