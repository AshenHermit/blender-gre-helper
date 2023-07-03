# from .utils import *
from pathlib import Path
import re
import enum
import json

from .utils import find_collection_by_object

from .addon_prefs import get_gr_exporter_path

class PropertyRegionParser():
    class LineData():
        def __init__(self, info_type, key, value) -> None:
            self.info_type:PropertyRegionParser.InfoType = info_type
            self.key:str = key
            self.value:str = value
        def __repr__(self) -> str:
            return f"LineData: {self.info_type}, {self.key}: {self.value}"
    class InfoType(enum.Enum):
        REGION_SETTING = enum.auto()
        REGION_DESCRIPTION_LINE = enum.auto()
        PROPERTY = enum.auto()
        PROPERTY_DESCRIPTION_LINE = enum.auto()
        PROPERTY_SETTING = enum.auto()

    @classmethod
    def iterate_lines(self, text):
        lines = text.split("\n")
        lines = [l.strip() for l in lines]
        settings = []

        def check_line(line):
            # reg info
            if line.startswith("###"):
                line = line[3:].strip()
                # reg setting
                for match in re.findall(r"(\w+)\s*:\s*(.+)", line):
                    key, value = match
                    return self.LineData(self.InfoType.REGION_SETTING, key, value)
                if line:
                    return self.LineData(self.InfoType.REGION_DESCRIPTION_LINE, "", line)
            
            elif line.startswith("#"):
                line = line[1:].strip()
                # reg setting
                for match in re.findall(r"(\w+)\s*:\s*(.+)", line):
                    key, value = match
                    return self.LineData(self.InfoType.PROPERTY_SETTING, key, value)
                if line:
                    return self.LineData(self.InfoType.PROPERTY_DESCRIPTION_LINE, "", line)
            else:
                for match in re.findall(r"self.(\w+)\s*=\s*(.+)", line):
                    key, value = match
                    value = value
                    return self.LineData(self.InfoType.PROPERTY, key, value)
            
            return None

        for line in lines:
            data = check_line(line)
            if data: yield data

class ResClassProperty():
    def __init__(self) -> None:
        self.name = "prop"
        self.type = str
        self.default_value = "value"
        self.description = ""
        self.values = None
        self.plugin = ""
        self._can_draw = True

class ResClass():
    def __init__(self) -> None:
        self.type = ""
        self.properties = []
        self.description = ""

    @staticmethod
    def object_fits(obj):
        return True

class ResMaterialClass(ResClass):
    pass

class ResModelClass(ResClass):
    @staticmethod
    def is_phy_model(obj):
        return find_collection_by_object(obj).name.endswith("_phy")

class ResViewModelClass(ResModelClass):
    @staticmethod
    def object_fits(obj):
        return not ResModelClass.is_phy_model(obj)

class ResPhyModelClass(ResModelClass):
    @staticmethod
    def object_fits(obj):
        return ResModelClass.is_phy_model(obj)

class ResClassesParser():
    def __init__(self) -> None:
        self.res_classes = []
        self.res_classes_by_type = {}

    def sort_classes_by_type(self):
        self.res_classes_by_type = {}
        for cls in self.res_classes:
            cls_type = cls.type
            if not cls_type in self.res_classes_by_type:
                self.res_classes_by_type[cls_type] = []
            self.res_classes_by_type[cls_type].append(cls)

    def get_all_properties_regions(self, text):
        properties_regions = []
        regex = r"(?s)(?<=### PROPERTIES START).*?(?=### PROPERTIES END)"
        matches = re.finditer(regex, text, re.MULTILINE)

        for match in matches:
            properties_regions.append(match.group())
        return properties_regions
    
    def request_class_by_type(self, cls_type):
        if cls_type in self.res_classes_by_type:
            return self.res_classes_by_type[cls_type]
        types_classes = {
            "material": ResMaterialClass,
            "model": ResModelClass,
            "view_model": ResViewModelClass,
            "phy_model": ResPhyModelClass,
        }
        cls = None
        if cls_type in types_classes:
            cls = types_classes[cls_type]()
        else: cls = ResClass()
        if cls: cls.type = cls_type
        self.res_classes.append(cls)
        self.res_classes_by_type[cls_type] = cls
        return cls
    
    @staticmethod
    def get_active_plugins(projpath):
        projpath = Path(projpath)
        for parent in projpath.parents:
            search = list(parent.glob("exporter_config.json"))
            if len(search)>0:
                config = search[0]
                config = json.loads(config.read_text())
                plugins = config["plugins"]
                return plugins
        return []
    
    @staticmethod
    def get_script_plugin_related(filepath):
        filepath = Path(filepath)
        for parent in filepath.parents:
            if parent.parent.name == "plugins":
                return parent.name
        return None

    def parse_classes(self):
        gre_path = Path(get_gr_exporter_path())
        gre_path = gre_path / "resources_exporter"

        search_folders = ["resource_types", "plugins"]
        
        blender_export_folders = [(gre_path / sf).rglob("blender_export/") for sf in search_folders]
        blender_export_folders = [d for gen in blender_export_folders for d in gen]
        files_to_scan = [d.rglob("**/*.py") for d in blender_export_folders]
        files_to_scan = [f for gen in files_to_scan for f in gen]

        for filepath in files_to_scan:
            text = filepath.read_text()
            properties_regions = self.get_all_properties_regions(text)

            for region in properties_regions:
                cls_description = ""
                cls = None
                prop_description = ""
                prop_values = None

                itype = PropertyRegionParser.InfoType
                for info in PropertyRegionParser.iterate_lines(region):
                    if info.info_type == itype.REGION_DESCRIPTION_LINE:
                        cls_description += f"{info.value}\n"

                    elif info.info_type == itype.REGION_SETTING:
                        if info.key == "class":
                            cls = self.request_class_by_type(info.value)
                    
                    elif info.info_type == itype.PROPERTY_DESCRIPTION_LINE:
                        prop_description += f"{info.value}\n"

                    elif info.info_type == itype.PROPERTY_SETTING:
                        if info.key == "values":
                            prop_values = [eval(v) for v  in info.value.split(",")]

                    elif info.info_type == itype.PROPERTY:
                        if cls:
                            prop = ResClassProperty()
                            prop.description = prop_description
                            prop.default_value = eval(info.value)
                            prop.name = info.key
                            prop.type = type(prop.default_value)
                            prop.plugin = self.get_script_plugin_related(filepath)
                            if prop_values: prop.values = prop_values
                            cls.properties.append(prop)
                            prop_description = ""
                            prop_values = None
                            self.get_script_plugin_related(filepath)

                if cls:
                    if cls.description:
                        cls.description += "\n"+cls_description
                    else:
                        cls.description = cls_description

res_classes_parser = ResClassesParser()