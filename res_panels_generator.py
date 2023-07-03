import importlib, sys

import bpy, os
from . import gre_helper
from . import operators
from .utils import *
from .res_classes_parser import *
from pathlib import Path
from .classes_manager import CLSManager
from functools import partial

@CLSManager.reg_bpy_class
class GRE_DescriptionBoxOperator(bpy.types.Operator):
    bl_idname = "ui.gre_show_info_box"
    bl_label = "Description"
    res_class:ResClass = None

    text: bpy.props.StringProperty(
        name = 'text',
        default = ''
    )

    def execute(self, context):
        #this is where I send the message
        self.report({'INFO'}, self.text)
        
        return {'FINISHED'}

class GRE_PT_Resource_Props_Panel(bpy.types.Panel):
    res_class:ResClass = None

    def draw_header(self, context):
        op = self.layout.operator("ui.gre_show_info_box", text="", icon="RADIOBUT_OFF")
        op.text = self.res_class.description

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        reg_info = ResPanelsGenerator.get_res_bl_reg_info(self.res_class.type)
        if not self.res_class.object_fits(reg_info.active_bl_data): return
        
        for prop in self.res_class.properties:
            if not prop._can_draw: continue
            row = layout.row()
            row.prop(
                reg_info.get_active_data_props(self.res_class), 
                ResPanelsGenerator.get_res_prop_blender_name(self.res_class, prop))

class ResPanelsGenerator():
    class ResClassRegInfo():
        def __init__(self, bl_context=None, prop_group_data=None) -> None:
            self.bl_context = bl_context or "object"
            self.prop_group_data = prop_group_data or bpy.types.Object

        @property
        def active_bl_data(self):
            if self.bl_context == "material":
                return bpy.context.object.active_material
            return bpy.context.object
        
        @property
        def bl_data_collection(self):
            if self.bl_context == "material":
                return bpy.data.materials
            return bpy.data.objects
        
        def get_active_data_props(self, res_class):
            return getattr(
                self.active_bl_data, 
                ResPanelsGenerator.get_res_props_group_name(res_class))
    
    res_bl_reg_info = {
        "_default": ResClassRegInfo("object", bpy.types.Object),
        "material": ResClassRegInfo("material", bpy.types.Material),
    }
    
    def __init__(self, res_classes_parser) -> None:
        self.res_classes_parser:ResClassesParser = res_classes_parser
        self.properties_class = None

    def on_project_loaded(self):
        self.apply_all_bl_props_from_custom()
        self.check_props_draw_ability()

    def check_props_draw_ability(self):
        active_plugins = ResClassesParser.get_active_plugins(bpy.data.filepath)
        for res_class in self.res_classes_parser.res_classes_by_type.values():
            for prop in res_class.properties:
                prop._can_draw = True
                if prop.plugin:
                    if not prop.plugin in active_plugins:
                        prop._can_draw = False

    def apply_all_bl_props_from_custom(self):
        for res_class in self.res_classes_parser.res_classes_by_type.values():
            reg_info = self.get_res_bl_reg_info(res_class.type)
            for bl_data in reg_info.bl_data_collection:
                for prop in res_class.properties:
                    if prop.name in bl_data:
                        setattr(
                            getattr(bl_data, ResPanelsGenerator.get_res_props_group_name(res_class)),
                            ResPanelsGenerator.get_res_prop_blender_name(res_class, prop),
                            prop.type(bl_data[prop.name])
                        )

    @classmethod
    def get_res_bl_reg_info(self, res_type):
        if res_type in self.res_bl_reg_info:
            return self.res_bl_reg_info[res_type]
        return self.res_bl_reg_info["_default"]
    
    def register_res_props_group(self, res_class:ResClass):
        prop_group_name = self.get_res_props_group_name(res_class)
        properties_class_name = prop_group_name
        properties_attributes = {
            '__annotations__': {}
        }
        self.properties_class = type(properties_class_name, (bpy.types.PropertyGroup,), properties_attributes)
        CLSManager.reg_prop_group(
            self.get_res_bl_reg_info(res_class.type).prop_group_data, 
            prop_group_name
        )(self.properties_class)

    @staticmethod
    def get_res_prop_blender_name(res_class:ResClass, res_prop:ResClassProperty):
        return f"{res_class.type}_{res_prop.name}"
    @staticmethod
    def get_res_props_group_name(res_class:ResClass):
        return f"gre_{res_class.type}_props"

    def add_res_prop_to_blender(self, res_class:ResClass, res_prop:ResClassProperty):
        # prop = bpy.props.FloatProperty(
        #             name="My Float Property",
        #             default = res_prop.default_value)
        prop_key = self.get_res_prop_blender_name(res_class, res_prop)
        type_to_prop_map = {
            int: bpy.props.IntProperty,
            float: bpy.props.FloatProperty,
            str: bpy.props.StringProperty,
            bool: bpy.props.BoolProperty,
        }
        if res_prop.type in type_to_prop_map:
            def update_prop(self, context):
                reg_info = ResPanelsGenerator.get_res_bl_reg_info(res_class.type)
                active_data_props = reg_info.get_active_data_props(res_class)
                if active_data_props != self:
                    return
                bl_data = reg_info.active_bl_data
                value = getattr(
                    active_data_props, 
                    ResPanelsGenerator.get_res_prop_blender_name(res_class, res_prop),)
                bl_data[res_prop.name] = value
                    

            if res_prop.values:
                items = tuple([(v, v, "") for v in res_prop.values])
                prop_definition = bpy.props.EnumProperty(
                    name=res_prop.name, description=res_prop.description,
                    default=res_prop.default_value, update=update_prop,
                    items = items,
                )
            else:
                prop_definition = type_to_prop_map[res_prop.type](
                    name=res_prop.name, description=res_prop.description,
                    default=res_prop.default_value, update=update_prop,
                )

            self.properties_class.__annotations__[prop_key] = prop_definition

    def register_panel(self, res_class:ResClass):
        self.register_res_props_group(res_class)
        for prop in res_class.properties:
            self.add_res_prop_to_blender(res_class, prop)

        class_name = f"GRE_PT_{res_class.type}_Resource_Props_Panel"
        attributes = {
            "bl_label": f"GRE {res_class.type} Resource Properties",
            "bl_idname": f"GREHelper_PT_{res_class.type}_res_panel",
            "bl_description": res_class.description,
            "bl_space_type": "PROPERTIES",
            "bl_region_type": "WINDOW",
            "bl_context": self.get_res_bl_reg_info(res_class.type).bl_context,
            # new panel has ResClass reference
            "res_class": res_class,
        }

        dynamic_panel_class = type(class_name, (GRE_PT_Resource_Props_Panel,), attributes)
        CLSManager.reg_bpy_class(dynamic_panel_class)
        return dynamic_panel_class
        
    def generate_panels(self):
        for cls_type, res_cls in self.res_classes_parser.res_classes_by_type.items():
            panel = self.register_panel(res_cls)