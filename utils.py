import bpy, os

def find_collection_by_object(obj):
    for collection in bpy.data.collections:
        if obj.name in collection.objects:
            return collection
    return None