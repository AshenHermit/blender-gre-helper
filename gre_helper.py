#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***** END GPL LICENSE BLOCK *****

import argparse
from functools import partial
import os
import sys
import traceback
import importlib
import bpy
import bmesh
import addon_utils
from bpy_extras.io_utils import ImportHelper
from .classes_manager import CLSManager

from .info import addon_id

# @CLSManager.reg_bpy_class
# class FACTORIOUTILS_PT_SidePanel(bpy.types.Panel):
#     bl_label = "Factorio Utils"
#     bl_space_type = "VIEW_3D"
#     bl_region_type = 'UI'
#     bl_category = 'Factorio Utils'

#     def draw(self, context):
#         scn = bpy.context.scene
#         layout = self.layout
#         col = layout.column(align=True)