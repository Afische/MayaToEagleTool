import sys
import os
import re
import stat
import json
import shutil
import subprocess
from PySide2.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QFileDialog, QCheckBox, QMessageBox, QProgressBar
)
from PySide2.QtCore import Qt, QProcess
from PySide2.QtGui import QFont, QIcon

#"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" MayaToEagleTool.py
#pyinstaller --windowed --icon=eagleIcon.ico --add-data "UploadToEagle.py;." MayaToEagleTool.py

# Path to Maya’s mayapy executable
MAYA_BIN = r"C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe"

###############################################################################
# Maya code: Saves changes to a temp .ma file which is deleted after render
###############################################################################

MAYA_SCRIPT = """ 
# -*- coding: utf-8 -*-
import os
os.environ["MAYA_ENABLE_LEGACY_RENDER_LAYERS"] = "1"
os.environ["MAYA_NO_CONVERT_LEGACY_RENDER_LAYERS"] = "1"
os.environ['MAYA_DISABLE_PLUGIN_AUTOLOAD'] = '1'
import re
import subprocess
import tempfile
import traceback
import shutil
import json
import stat
import maya.standalone
maya.standalone.initialize(name="python")
import maya.utils
import maya.mel as mel
import maya.cmds as cmds
if mel.eval('pluginInfo -q -loaded "renderSetup"'):
    cmds.unloadPlugin("renderSetup", force=True)
    print("renderSetup plugin was loaded and is now unloaded.")

propsTags = [
    "wood", "metal", "glass", "stone", "marble", "rock", "boulder", "granite", "tile", "cloth",
    "concrete", "dirt", "door", "leather", "sand", "sky", "smoke", "snow", "solid", "wall",
    "water", "floor", "brick", "brass", "tree", "bush", "foliage", "iron", "gold", "paper",
    "canvas", "frame", "book", "pebble", "curtain", "chalk", "window", "painting", "plaster",
    "moss", "portrait", "stucco", "plank", "fabric", "rug", "furniture", "card", "bag", "food",
    "plant", "statue", "ceiling", "column", "trim", "cloud", "sun", "moon", "hill", "hay",
    "leaf", "leaves", "wand", "broom", "potion", "table", "chair", "christmans", "xmas",
    "halloween", "hw", "xm", "vd", "valentines", "summer", "spring", "fall", "winter",
    "owl", "pride", "perch", "bed", "mattress", "pillow", "cabinet", "ceramic", "drawer",
    "cork", "board", "cauldron", "roof", "boat", "car", "rubber", "train", "footprint",
    "pot", "ink", "couch", "paint", "bookshelf", "crate", "barrel", "box", "butter", "cake",
    "cupcake", "candy", "coat", "rack", "pumpkin", "candle", "jack", "chandelier", "stool",
    "fireplace", "wainscot", "yarn", "pet", "dust", "cardboard", "plastic", "light", "chest",
    "awning", "counter", "by7", "bh", "floating", "balloons", "deco"
]

effectsTags = [
    "water", "fire", "dust", "energy", "particle", "spark", "bubble", "dirt", "cloud",
    "patronus", "steam", "snow", "rain", "spell", "splash", "drip", "firework", "mist",
    "fog", "shadow", "darkness", "card", "invisibility", "ink", "ember", "blood",
    "explosion", "feather", "ray", "glow", "blast", "impact", "light", "wave", "shield",
    "puddle", "rainbow", "glitter", "slime"
]

allTags = [
    "beard", "glass", "earing", "necklace", "bracelet", "glove", "shoe", "cape", "coat",
    "jacket", "sock", "hat", "sandal", "belt", "shirt", "pauldron", "helmet", "ponytail",
    "hood", "tie", "bow", "boot", "male", "female", "skirt", "pants", "shorts",
    "tight", "scarf", "leather", "metal", "animate", "y8", "by7", "bh", "top", "bottom",
    "glove", "full", "hat", "wrist", "scarf", "glass", "earring", "ring", "fade", "fur"
]

shaderTags = [
    "AnimateUV", "AvatarFaceShader", "AvatarHairShader", "AvatarSkinShader", "BetterAnimateUvs_vfx", "BetterAnimateUvs2_vfx", "caustics_vfx", "ClothShader",
    "CustomSFX", "dancingSkeleton_vfx", "DirtDecal_vfx", "DualRim_vfx", "dustMotes_vfx", "enchant_vfx", "enchant_vfx_old", "EyesForMarketing01",
    "EyeShader", "Eyeballshader", "fallingParts_vfx", "fallingPartsColor_vfx", "fallingPartsRefined_vfx", "flare2D_vfx", "flowMap_vfx", "ghost_vfx", "ghostDiffuse_vfx",
    "ghostFade_vfx", "glow_vfx", "GodraysShader_vfx", "HairShader", "HouseClothShader", "houserobeshader", "HueShiftShader", "IconOutline",
    "Invisibility_vfx", "iridescence_vfx", "iridescenceAlpha_vfx", "KeyableAnimateUvs_vfx", "lightning_vfx", "LightRays_vfx", "LightRays2_vfx", "MetaBottleInk_vfx",
    "metallic_vfx", "MetaPaintingDust_vfx", "MODHairShader", "NavMeshShader", "newEyeShader", "Opal2_vfx", "Opal_vfx", "OutfitShader",
    "PanningB", "PanningFalloff", "PanningGlow_vfx", "PanningWithSparsity_vfx", "PatronusOutfit_vfx", "PatronusSimple_vfx", "PlantCare_vfx", "PumpkinSpiceOutfit_vfx",
    "rain_vfx", "reflective_vfx", "seasons_vfx", "SequinColors_vfx", "shadowPlane_vfx", "SkinShader", "snowflakes_vfx", "SnowOutfit_vfx",
    "SoapBubble_vfx", "Sparkle_vfx", "Sprite_vfx", "SpriteOutfit_vfx", "SpriteOutfitDiffuse_vfx", "StarsSparkle_vfx", "thunderbirdOutfit_vfx", "transition_vfx",
    "transitionDiffuse_vfx", "transitionFade_vfx", "transitionStaticFade_vfx", "TwoSpiritWithRim_vfx", "UberShader", "VertexAlpha_vfx", "VertexColor_vfx", "void_vfx",
    "warp_vfx", "worldPan_vfx", "worldPanAlpha_vfx"
]

outfitTags = ["BOTTOM", "TOP", "HAT", "LEFT_WRIST", "RIGHT_WRIST", "SCARF", "NECKLACE", "LEFT_RING", "RIGHT_RING", "GLASSES", "EARRINGS", "SHOES", "FULL"]

# === GET SCENE PATH AND TEMP DIRECTORY TO SAVE A MODIFIED VERSION===

original_scene = r"{scene_file}"

temp_scene_path = os.path.join(tempfile.gettempdir(), "temp_render_scene.ma")

# === DETERMINE WHAT KIND OF SCENE ===

output_dir = r"{output_dir}"
output_dir_lower = output_dir.lower()
is_prop_file = "props" in output_dir_lower
is_outfit_file = "outfits" in output_dir_lower
is_hair_file = "hair" in output_dir_lower
is_character_file = "characters" in output_dir_lower and not is_outfit_file
is_creature_file = "creatures" in output_dir_lower
is_effects_file = "effects" in output_dir_lower

file_type = ""
if is_prop_file:
    file_type = "props"
elif is_outfit_file:
    file_type = "outfits"
elif is_hair_file:
    file_type = "hair"
elif is_character_file:
    file_type = "characters"
elif is_creature_file:
    file_type = "creatures"
elif is_effects_file:
    file_type = "effects"

# === INITIALIZE MAYA STANDALONE FUNCTIONALITY ===

maya.standalone.initialize(name="python")

try:
    # === LOAD SCENE ===

    cmds.file(original_scene, open=True, force=True)
    if not cmds.file(query=True, sceneName=True):
        print("!!! ERROR: Maya failed to open the scene file !!!")
    scene_loaded = cmds.file(query=True, sceneName=True)
    print("Scene loaded path:", scene_loaded)
    if not scene_loaded:
        print("!!! ERROR: Maya failed to open the scene file (empty sceneName) !!!")
    print(f"Opened original scene: {{original_scene}}")
    project_dir = cmds.workspace(q=True, rootDirectory=True)

    #scene_path = r"{scene_file}"
    #if not cmds.file(query=True, sceneName=True):
    #    cmds.file(scene_path, open=True, force=True)
    #    print("Scene loaded:", scene_path)
    #all_refs = cmds.file(query=True, reference=True)
    #if all_refs:
    #    for ref in all_refs:
    #        cmds.file(ref, loadReference=True)

    # === ENSURE CHARACTER LIGHTING IS IMPORTED ===

    light_template_path = os.path.join(project_dir, "Lights", "ForTexturing", "characterLights_template.ma")
    if cmds.objExists("characterLights_template:KeyLight"):
        try:
            if cmds.referenceQuery("characterLights_templateRN", isNodeReferenced=True):
                cmds.file(removeReference=True, referenceNode="characterLights_templateRN")
        except RuntimeError as e:
            print(f"Warning: Failed to remove characterLights_templateRN reference: {{e}}")
    try:
        cmds.file(light_template_path, reference=True, type="mayaAscii", ignoreVersion=True, namespace="characterLights_template", options="v=0;")
        print("Referenced characterLights_template.ma successfully.")
    except Exception as e:
        print(f"Failed to reference characterLights_template.ma: {{e}}")

    # === HIDE ALL MESHES UNDER ANY NonExportGeo GROUP IN THE SCENE ===

    all_render_layers = cmds.ls(type="renderLayer")
    ml_render_layers = [layer for layer in all_render_layers if layer.startswith("ML_")]
    render_layers_to_process = ["defaultRenderLayer"] + ml_render_layers
    for render_layer in render_layers_to_process:
        cmds.editRenderLayerGlobals(currentRenderLayer=render_layer)
        non_export_groups = [x for x in cmds.ls("NonExportGeo", type="transform", long=True)]
        for group in non_export_groups:
            non_export_descendants = cmds.listRelatives(group, allDescendents=True, fullPath=True) or []
            for node in non_export_descendants:
                if cmds.nodeType(node) == 'mesh':
                    transform = cmds.listRelatives(node, parent=True, fullPath=True)
                    if transform:
                        cmds.setAttr(f"{{transform[0]}}.visibility", 0)
                        print(f"Hid non-export mesh: {{transform[0]}}")

    # === FIND GRP_GEO MESH(S)===

    geo_candidates = [x for x in cmds.ls(type="transform", long=True) if x.endswith("|grp_geo")]
    if not geo_candidates:
        geo_candidates = cmds.ls("Char_Rig|grp_other|grp_geo", long=True)
    if geo_candidates:
        grp_geo_name = geo_candidates[0]
        print(f"Found `grp_geo`: {{grp_geo_name}}")
    else:
        print("Error: The group 'grp_geo' does not exist even after loading references!")
        print("Scene hierarchy:", cmds.ls(dag=True, long=True))
        cmds.error("The group 'grp_geo' does not exist.")

    # === COMPUTE INITIAL BOUNDING BOX AND POLY COUNT FOR GRP_GEO AND INITIALIZE JSON DICTIONARY ===
    
    bbox = cmds.exactWorldBoundingBox(grp_geo_name)
    x_min, y_min, z_min, x_max, y_max, z_max = bbox
    bbox_width = x_max - x_min
    bbox_height = y_max - y_min
    bbox_depth = z_max - z_min

    meshes = cmds.listRelatives(grp_geo_name, allDescendents=True, type="mesh") or []
    poly_count = 0
    for mesh in meshes:
        if not cmds.getAttr(f"{{mesh}}.intermediateObject"):
            #poly_count += cmds.polyEvaluate(mesh, face=True)
            poly_count += cmds.polyEvaluate(mesh, triangle=True)
    print(f"grp_geo bounding box: width={{bbox_width}}, height={{bbox_height}}, depth={{bbox_depth}}")
    print(f"Polygon count for grp_geo: {{poly_count}}")

    render_data = {{}}

    # === CREATE 2 DUPLICATES OF GRP_GEO IN DIFFERENT PERSPECTIVES ===

    offset1 = x_max + z_max + 0.5
    dup_grp1 = cmds.duplicate(grp_geo_name, name="grp_geo_dup1")[0]
    cmds.rotate(0, -90, 0, dup_grp1, relative=True, objectSpace=True)
    cmds.xform(dup_grp1, ws=True, t=(offset1, 0, 0))
    amount1 = x_max + z_max + 0.5
    amount2 = x_max + abs(z_min) + 0.5
    offset2 = amount1 + amount2
    dup_grp2 = cmds.duplicate(grp_geo_name, name="grp_geo_dup2")[0]
    cmds.rotate(0, 180, 0, dup_grp2, relative=True, objectSpace=True)
    cmds.xform(dup_grp2, ws=True, t=(offset2, 0, 0))

    # === CREATE NEW ORTHOGRAPHIC CAMERA ===

    if cmds.objExists("EagleCamera1"):
        cmds.delete("EagleCamera1")
    camera = cmds.camera(name="EagleCamera1")[0]
    camera_shapes = cmds.listRelatives(camera, shapes=True)
    if camera_shapes:
        cameraShape = camera_shapes[0]
        cmds.rename(cameraShape, "EagleCamera1Shape")
        cameraShape = "EagleCamera1Shape"
    else:
        print("Error: Camera shape not found!")
        cmds.error("Camera shape missing after creation.")
    cmds.setAttr(f"{{cameraShape}}.renderable", True)
    cmds.setAttr(f"{{cameraShape}}.orthographic", True)
    cmds.setAttr(f"{{cameraShape}}.orthographicWidth", 10.0)
    print("Created camera:", camera, "with shape:", cameraShape)

    # === DETECT IF THIS IS A FLAT PLANE FOR EFFECTS FILES AND ADJUST CAMERA ===

    flat_axis = None
    if is_effects_file:
        x = bbox_width
        y = bbox_height
        z = bbox_depth

        flat_candidates = []
        if x < 0.05 * y or x < 0.05 * z:
            flat_candidates.append(('X', x))
        if y < 0.05 * x or y < 0.05 * z:
            flat_candidates.append(('Y', y))
        if z < 0.05 * x or z < 0.05 * y:
            flat_candidates.append(('Z', z))

        if flat_candidates:
            flat_axis = min(flat_candidates, key=lambda t: t[1])[0]
            print("Flat axis detected by ratio:", flat_axis)

    # === COMPUTE OVERALL BOUNDING BOX OF ALL 3 MESHES ===

    overall_bbox = cmds.exactWorldBoundingBox(grp_geo_name, dup_grp1, dup_grp2)
    ov_x_min, ov_y_min, ov_z_min, ov_x_max, ov_y_max, ov_z_max = overall_bbox
    margin = 1.05
    overall_bb_width  = (ov_x_max - ov_x_min) * margin
    overall_bb_height = (ov_y_max - ov_y_min) * margin
    overall_bb_depth  = (ov_z_max - ov_z_min) * margin

    # === COMPUTE ASPECT RATIO BASED ON BOUNDING BOX SHAPE, COMPUTE PIXEL HEIGHT ===

    dynamic_aspect = overall_bb_width / overall_bb_height
    pixel_height = max(2, int(1920 / dynamic_aspect))
    print("Overall bounding box Width:", overall_bb_width)
    print("Corrected bounding box Height:", overall_bb_height)
    print("Dynamic aspect ratio:", dynamic_aspect)
    print("Clamped pixel height:", pixel_height)

    # === SET CAMERA RESOLUTION, ORTHOGRAPHIC WIDTH AND ASPECT RATIO ===

    cmds.setAttr("defaultResolution.width", 1920)
    cmds.setAttr("defaultResolution.height", pixel_height)
    cmds.setAttr(f"{{cameraShape}}.orthographicWidth", overall_bb_width)
    cmds.setAttr("defaultResolution.deviceAspectRatio", dynamic_aspect)
    print("Render resolution set to 1920 x", pixel_height)
    print("Orthographic width set to:", overall_bb_width)
    # Set the near clip plane to 0.001
    #cmds.setAttr(f"{{cameraShape}}.nearClipPlane", 0.001)

    # === AUTO-CENTER CAMERA BASED ON FLATNESS OR DEFAULT ===

    if is_effects_file and flat_axis:
        print("[Camera] Auto-orienting camera for flat effects plane...")
        center_x = (ov_x_min + ov_x_max) / 2.0
        center_y = (ov_y_min + ov_y_max) / 2.0
        center_z = (ov_z_min + ov_z_max) / 2.0

        if flat_axis == 'Z':
            # Camera looking at front face from +Z
            cam_pos = [center_x, center_y, ov_z_max + 100]
            cam_rot = [0, 0, 0]
            ortho_width = max(overall_bb_width, overall_bb_height) * 1.05
            dynamic_aspect = overall_bb_width / overall_bb_height

        elif flat_axis == 'X':
            # Camera looking at side face from +X
            cam_pos = [ov_x_max + 100, center_y, center_z]
            cam_rot = [0, 90, 0]
            ortho_width = max(overall_bb_depth, overall_bb_height) * 1.05
            dynamic_aspect = overall_bb_depth / overall_bb_height

        elif flat_axis == 'Y':
            # Camera looking from above (top-down)
            cam_pos = [center_x, ov_y_max + 100, center_z]
            cam_rot = [-90, 0, 0]
            ortho_width = max(overall_bb_width, overall_bb_depth) * 1.05
            dynamic_aspect = overall_bb_width / overall_bb_depth

        pixel_height = int(1920 / dynamic_aspect)
        cmds.xform(camera, ws=True, t=cam_pos)
        cmds.setAttr(f"{{camera}}.rotateX", cam_rot[0])
        cmds.setAttr(f"{{camera}}.rotateY", cam_rot[1])
        cmds.setAttr(f"{{camera}}.rotateZ", cam_rot[2])
        cmds.setAttr(f"{{cameraShape}}.orthographicWidth", ortho_width)
        print(f"[Camera] Camera positioned at {{cam_pos}} with rotation {{cam_rot}}")
        print(f"[Camera] Ortho width: {{ortho_width}}, aspect: {{dynamic_aspect}}, height: {{pixel_height}}")

    else:
        # Default camera placement for non-flat objects
        center_x = (ov_x_min + ov_x_max) / 2.0
        center_y = (ov_y_min + ov_y_max) / 2.0
        global_z_max = ov_z_max
        cam_pos = (center_x, center_y, global_z_max + 100)
        cmds.xform(camera, ws=True, t=cam_pos)
        dynamic_aspect = overall_bb_width / overall_bb_height
        pixel_height = int(1920 / dynamic_aspect)
        cmds.setAttr(f"{{cameraShape}}.orthographicWidth", overall_bb_width)
        print("[Camera] Default camera positioning:", cam_pos)
        print(f"[Camera] Default ortho width: {{overall_bb_width}}, aspect: {{dynamic_aspect}}, height: {{pixel_height}}")

    # === SET ORTHO AS THE RENDERABLE CAMERA ===

    all_cameras = cmds.ls(type="camera")
    if "EagleCamera1" or "EagleCamera1Shape" in all_cameras:
        render_camera = "EagleCamera1"
    else:
        print("Warning: EagleCamera1 not found! Using first available camera.")
        render_camera = all_cameras[0]
    for camera in all_cameras:
        cmds.setAttr(f"{{camera}}.renderable", 0)
    cmds.setAttr(f"{{render_camera}}.renderable", 1)
    print(f"{{render_camera}} is now the only renderable camera.")

    # === SET OTHER CAMERA SETTINGS ===

    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)  # Enable anti-aliasing
    cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", 16)  # Higher = better smoothing (16 is a good balance)
    cmds.setAttr("defaultRenderGlobals.imageFormat", 32)  # Set high-quality PNG output (lossless)
    cmds.setAttr("hardwareRenderingGlobals.enableTextureMaxRes", 1)  # Enable high-quality textures
    cmds.setAttr("hardwareRenderingGlobals.transparencyAlgorithm", 2)  # Best transparency handling
    cmds.setAttr("defaultRenderGlobals.animation", 0)  # Ensure animation is off (single frame)
    cmds.setAttr("defaultRenderGlobals.startFrame", 1) # Ensure the renderable frame
    cmds.setAttr("defaultRenderGlobals.endFrame", 1) # Ensure the renderable frame
    cmds.setAttr("defaultRenderGlobals.extensionPadding", 0)  # Prevents ".0001" type suffix
    cmds.setAttr("defaultRenderGlobals.periodInExt", 1) # Prevents ".1" suffix
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "mayaHardware2", type="string") # Use Maya Hardware 2.0

    # === EXTRACT MESH-SHADER-TEXTURE DATA FROM ALL MESHES UNDER GRP_GEO ===
    
    # Get all ShaderfxShader nodes
    SHADERFX_SHADERS = cmds.ls(type='ShaderfxShader')
    SHADERFX_TEXTURE_ATTRS = (
        '.DiffuseMap', '.LightmapMap', '.SpecularMap',
        '.DirtMap', '.SecondDiffuseMap', '.Diffuse',
        '.SecondaryMaps', '.ColorMap', '.Mask'
    )

    shader_texture_data = {{}}

    # Get all meshes under grp_geo
    meshes_under_grp_geo = []
    tagged_outfit_parts = set()
    if cmds.objExists(grp_geo_name):
        all_descendants = cmds.listRelatives(grp_geo_name, allDescendents=True, fullPath=True) or []
        for m in all_descendants:
            if cmds.nodeType(m) == 'mesh':
                meshes_under_grp_geo.append(m)

                # If this is an outfit or hair file perform outfit tag check 
                if is_outfit_file or is_hair_file:
                    parent_chain = cmds.listRelatives(m, allParents=True, fullPath=True) or []
                    while parent_chain:
                        parent = parent_chain[0]
                        short_name = parent.split('|')[-1].upper()
                        if short_name in outfitTags:
                            tagged_outfit_parts.add(short_name)
                            break
                        parent_chain = cmds.listRelatives(parent, parent=True, fullPath=True) or []

    # Get shaders connected to those meshes
    connected_shaders = set()
    shader_to_meshes = {{}}
    for mesh in meshes_under_grp_geo:
        shading_engines = cmds.listConnections(mesh, type='shadingEngine') or []
        for se in shading_engines:
            surface_shaders = cmds.listConnections(se + '.surfaceShader', source=True, destination=False) or []
            for shader in surface_shaders:
                if cmds.nodeType(shader) == 'ShaderfxShader':
                    connected_shaders.add(shader)
                    shader_to_meshes.setdefault(shader, []).append(mesh)

    # Gather texture data for the relevant shaders
    for shader in connected_shaders:
        shader_texture_data[shader] = []
        for attr in SHADERFX_TEXTURE_ATTRS:
            try:
                filePath = cmds.getAttr('{{}}{{}}'.format(shader, attr))
                if filePath:
                    shader_texture_data[shader].append({{
                        'attribute': attr,
                        'filePath': re.sub(r'//+', '/', filePath)
                    }})
            except Exception as e:
                print(f"Skipping {{shader}}{{attr}} due to error: {{e}}")
                continue
                
    # === CREATE TAGS FROM SHADER TEXTURE MESH DATA ===

    keywords = []
    rigUsed = ""
    if not shader_texture_data:
        tagslist = []
    else:
        for shader, textures in shader_texture_data.items():
            texture_names = [os.path.basename(tex['filePath']).replace('.png', '').lower() for tex in textures]
            meshes = shader_to_meshes.get(shader, [])
            cleaned_meshes = [cmds.listRelatives(m, parent=True, fullPath=False)[0].lower() for m in meshes]
            keywords.extend(texture_names + cleaned_meshes + [shader.lower()])
        keywords_string = ''.join(keywords)

        print(\n"keywords_string:")
        print(keywords_string)

        all_known_tags = set(propsTags + effectsTags + allTags + shaderTags)
        tagslist = [tag for tag in all_known_tags if tag.lower() in keywords_string]
        # Remove 'male' if 'female' is present
        if 'female' in [t.lower() for t in tagslist]:
            tagslist = [tag for tag in tagslist if tag.lower() != 'male']
        # Remove mask from the tagslist
            tagslist = [tag for tag in tagslist if tag.lower() != "mask"]
        # Add outfit and hair specific tags
        tagslist.extend([tag.lower() for tag in tagged_outfit_parts])
        
        # Save character and creature rig name for notes to be added later
        if is_character_file or is_creature_file:
            if grp_geo_name:
                ref_node = cmds.referenceQuery(grp_geo_name, referenceNode=True)
                rigUsed = str(ref_node)
                rig_tag = re.sub(r'_?rn$', '', rigUsed, flags=re.IGNORECASE)
            else:
                print('grp_geo not found')

        print("")
        print("Tags:")
        print (tagslist)

    # === SAVE A TEMPORARY SCENE TO RENDER ===

    filename = os.path.splitext(os.path.basename(original_scene))[0]
    render_exe = r"C:/Program Files/Autodesk/Maya2024/bin/Render.exe"
    scene_file = r"{scene_file}"
    output_dir = r"{output_dir}"
    log_file = os.path.join(r"{log_dir}", "MayaToEagle_log.txt")
    try:
        if os.path.exists(log_file):
            os.chmod(log_file, stat.S_IWRITE)
    except Exception as e:
        print(f"Warning: Could not make log file writable: {{e}}")
    expected_output = os.path.join(output_dir, filename + ".png")
    cmds.file(rename=temp_scene_path)
    cmds.file(save=True, type="mayaAscii")
    print(f"Temporary scene saved: {{temp_scene_path}}")

    # === GET ALL ML_ RENDER LAYERS IN THE SCENE IF THEY EXIST ===

    all_render_layers = cmds.ls(type="renderLayer")
    ml_render_layers = [layer for layer in all_render_layers if layer.startswith("ML_")]
    render_layers_to_process = ["defaultRenderLayer"] + ml_render_layers
    print(f"Render layers to process: {{render_layers_to_process}}")

    # === LOOP THROUGH EACH RENDER LAYER AND RENDER SEPARATELY ===

    for render_layer in render_layers_to_process:
        print(f"Setting render layer: {{render_layer}}")
        cmds.editRenderLayerGlobals(currentRenderLayer=render_layer)
        if render_layer == "defaultRenderLayer":
            filename_with_layer = filename
        else:
            layer_suffix = render_layer.replace("ML_", "")
            filename_with_layer = f"{{os.path.splitext(filename)[0]}}_{{layer_suffix}}"

        # === NAME FILE AND DELETE IMAGE IF THE NAME ALREADY EXISTS ===

        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", filename_with_layer, type="string") # Name files with a prefix
        expected_output = os.path.join(output_dir, f"{{filename_with_layer}}.png").replace(os.sep, "/")
        if os.path.exists(expected_output):
            try:
                os.remove(expected_output)
                print(f"Deleted existing image: {{expected_output}}")
            except Exception as e:
                print(f"Error deleting {{expected_output}}: {{e}}")
        print(f"Render will be saved to: {{expected_output}}")

        # === MODIFY THE RENDERING COMMAND WITH RENDER LAYER INFO ===

        render_cmd = [
            render_exe,
            "-r", "hw2",
            "-s", "1", "-e", "1",
            "-x", "1920", "-y", str(int(pixel_height)),
            "-cam", render_camera,
            "-rd", output_dir,
            "-of", "png",
            "-im", filename_with_layer,
            "-fnc", "3",
            "-rl", render_layer,
            "-log", log_file,
            temp_scene_path
        ]

        print(\n""\n)
        print("Executing Render.exe with command:")
        print(\n""\n)
        print(" ".join(render_cmd))

        # === RUN THE RENDERING PROCESS ===

        process = subprocess.run(render_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # bail out if Render.exe failed, Exit MAYA_SCRIPT entirely
        if process.returncode != 0:
            print(f"Render.exe failed with exit code {{process.returncode}}")
            print(process.stderr)
            sys.exit(process.returncode)

        print("Render.exe Errors:")
        print(process.stderr)

        # === RENAME OUTPUT FILES TO REMOVE FRAME NUMBER SUFFIX, PREFIX AND _RIG ===

        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if (".0001" in file or ".1" in file) and file.lower().endswith(".png"):
                    old_path = os.path.join(root, file)
                    new_name = re.sub(r'\.\d+(?=\.png$)', '', file) # Remove frame number suffix
                    new_name = re.sub(r'^(c_|o_|p_|fx_|.+?_)', '', new_name)  # Remove prefix
                    new_name = re.sub(r'_rig(?=\.png$)', '', new_name)  # Remove '_rig' if it exists before .png
                    new_path = os.path.join(root, new_name)
                    if os.path.exists(new_path):
                        try:
                            os.remove(new_path)
                            print(f"Deleted existing image: {{new_path}}")
                        except Exception as e:
                            print(f"Error deleting {{new_path}}: {{e}}")
                    try:
                        os.rename(old_path, new_path)
                        print(f"Renamed {{old_path}} to {{new_path}}")
                    except Exception as e:
                        print(f"Error renaming {{old_path}}: {{e}}")

        # === REMOVE EXTRA FOLDER STRUCTURE AFTER EACH RENDER COMMAND ===

        for root, dirs, files in os.walk(output_dir):
            if os.path.abspath(root) == os.path.abspath(output_dir):
                continue
            for file in files:
                if file.lower().endswith(".png"):
                    source_path = os.path.join(root, file)
                    dest_path = os.path.join(output_dir, file)
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    shutil.move(source_path, dest_path)
                    print(f"Moved {{source_path}} to {{dest_path}}")
        for root, dirs, files in os.walk(output_dir, topdown=False):
            if os.path.abspath(root) == os.path.abspath(output_dir):
                continue
            if not os.listdir(root):
                os.rmdir(root)
                print(f"Removed empty directory: {{root}}")

        # === RECORD JSON DATA FOR THIS IMAGE ===

        imglink = os.path.join(output_dir, filename_with_layer + ".png").replace(os.sep, "/")
        if "/Potter" in imglink:
            p4_link = "//Potter" + imglink.split("/Potter", 1)[1]
        else:
            p4_link = imglink
        filename = os.path.basename(imglink)
        dirname = os.path.dirname(imglink)
        clean_filename  = re.sub(r'^(c_|o_|p_|fx_|.+?_)', '', filename)
        clean_filename  = re.sub(r'_rig(?=\.png$)', '', os.path.basename(clean_filename ))
        image_key = os.path.splitext(clean_filename )[0]
        imglink = os.path.join(dirname, clean_filename ).replace(os.sep, "/")
        scene_relative_path = scene_file.replace("\\\\", "/").split("/Perforce/Potter/Art/3D/", 1)[-1]
        malink = f"//Potter/Art/3D/{{scene_relative_path}}"

        render_data[image_key] = {{
            "imglink": imglink,
            "malink": malink,
            "poly_count": poly_count,
            "bounding_box": [bbox_width, bbox_height, bbox_depth],
            "file_type": file_type
        }}

        # Add rig used found in file
        if rigUsed:
            render_data[image_key]["rig_used"] = rig_tag.lower()
        else:
            render_data[image_key]["rig_used"] = ""
        # Add tags found in file
        for i, tag in enumerate(tagslist):
            render_data[image_key][f"tag{{i + 1}}"] = tag

        print(f"Recorded JSON data for image: {{image_key}}")

    # === WRITE JSON FILE ===

    #library_root = os.path.dirname(output_dir)
    base_library = os.path.join(os.path.splitdrive(output_dir)[0] + os.sep, "Perforce", "Potter", "Art", "EagleFiles")
    library_root = os.path.join(base_library, file_type.capitalize())
    json_filename = f"render_data_{{file_type.lower()}}.json"
    json_file = os.path.join(library_root, json_filename)

    # Load existing JSON data if the file exists
    if os.path.exists(json_file):
        try:
            with open(json_file, "r") as jf:
                existing_data = json.load(jf)
            print("Loaded existing JSON data.")
        except Exception as e:
            print(f"Error reading existing JSON file: {{e}}")
            existing_data = {{}}
    else:
        existing_data = {{}}

    # Merge new render data into existing data
    existing_data.update(render_data)

    # Fix JSON indentation for bounding box arrays
    json_str = json.dumps(existing_data, indent=4)
    json_str = re.sub(
        r'("bounding_box": )\[\s*([\d\.,\s]+?)\s*\]',
        lambda m: m.group(1) + '[' + ', '.join(item.strip() for item in m.group(2).split(',')) + ']',
        json_str
    )

    # Write merged data back to file
    try:
        with open(json_file, "w") as jf:
            jf.write(json_str)
        print("Render JSON data written to:", json_file)
    except Exception as e:
        print(f"Failed to write JSON file: {{e}}")

    # === CLEANUP: REMOVE TEMP SCENE FILE AFTER ALL RENDERS COMPLETE ===

    if os.path.exists(temp_scene_path):
        os.remove(temp_scene_path)
        print(f"Temporary scene deleted: {{temp_scene_path}}")

    print(f"Render complete! Check directory: {output_dir}")

except Exception as e:
    traceback.print_exc()
    print(f"Error occurred: {{e}}")
    sys.exit(1)

finally:
    maya.standalone.uninitialize()
"""

###############################################################################
# GUI code: Process every .ma file found in a selected folder (recursively) sequentially
###############################################################################

class MayaRenderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.process = None
        self.scene_files = []
        self.current_index = 0
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #dcdcdc;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
            }
            QLineEdit, QTextEdit {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 4px;
                color: #f0f0f0;
            }
            QPushButton {
                background-color: #4a90e2;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
            }
            QPushButton:hover {
                background-color: #5aa0f2;
            }
            QCheckBox {
                spacing: 6px;
            }
            QProgressBar {
                background-color: #444;
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 5px;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 12pt;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        main_layout = QVBoxLayout()

        title = QLabel("Maya To Eagle Renderer")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        icon_path = os.path.join(self.get_base_path(), "eagleIcon.png")
        self.app_icon = QIcon(icon_path)
        self.setWindowIcon(QIcon(icon_path))

        scene_layout = QHBoxLayout()
        self.scene_folder_label = QLabel("Scene Folder:")
        self.scene_folder_edit = QLineEdit()
        self.scene_folder_edit.setPlaceholderText("Select folder containing .ma files (recursively)")
        self.scene_folder_browse = QPushButton("Browse")
        self.scene_folder_browse.clicked.connect(self.browse_scene_folder)
        scene_layout.addWidget(self.scene_folder_label)
        scene_layout.addWidget(self.scene_folder_edit)
        scene_layout.addWidget(self.scene_folder_browse)
        main_layout.addLayout(scene_layout)

        self.overwrite_checkbox = QCheckBox("Do Not Overwrite Existing Images")
        self.overwrite_checkbox.setChecked(True)
        main_layout.addWidget(self.overwrite_checkbox)

        self.render_button = QPushButton("🚀 Render Scenes")
        self.render_button.clicked.connect(self.run_maya_render)
        main_layout.addWidget(self.render_button)

        checkbox_layout = QHBoxLayout()
        self.checkboxes = {
            "Props": QCheckBox("Props"),
            "Outfits": QCheckBox("Outfits"),
            "Hair": QCheckBox("Hair"),
            "Characters": QCheckBox("Character"),
            "Creatures": QCheckBox("Creature"),
            "Effects": QCheckBox("Effects")
        }
        for category, checkbox in self.checkboxes.items():
            checkbox.clicked.connect(self.make_exclusive)
            checkbox_layout.addWidget(checkbox)
        main_layout.addLayout(checkbox_layout)

        self.upload_button = QPushButton("📤 Upload Images To Eagle")
        self.upload_button.clicked.connect(self.upload_images_to_eagle)
        main_layout.addWidget(self.upload_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 10))
        main_layout.addWidget(self.log_output)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)
        self.setWindowTitle(" Maya To Eagle Renderer")
        self.setMinimumWidth(600)
        self.setGeometry(300, 300, 640, 800)

    def make_exclusive(self):
        sender = self.sender()
        for checkbox in self.checkboxes.values():
            if checkbox != sender:
                checkbox.setChecked(False)

    def browse_scene_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Scene Folder")
        if folder:
            self.scene_folder_edit.setText(folder)

    def get_output_dir_for_file(self, file_path):
        """
        Determines the proper output directory for a given .ma file.
        """
        norm_path = os.path.normpath(file_path)
        file_dir = os.path.dirname(norm_path)
        drive, path_after_drive = os.path.splitdrive(file_dir)
        path_after_drive_lower = path_after_drive.lower()
        file_lower = os.path.basename(file_path).lower()

        # Define the relative base paths
        base_props_relative = os.path.join(os.sep, "perforce", "potter", "art", "3d", "props")
        base_characters_relative = os.path.join(os.sep, "perforce", "potter", "art", "3d", "characters")
        base_creatures_relative = os.path.join(os.sep, "perforce", "potter", "art", "3d", "characters", "_creatures")
        base_outfits_relative = os.path.join(os.sep, "perforce", "potter", "art", "3d", "characters", "_outfits")
        base_effects_relative = os.path.join(os.sep, "perforce", "potter", "art", "3d", "effects")

        # Build the base library folder
        base_library = os.path.join(drive + os.sep, "Perforce", "Potter", "Art", "EagleFiles")
        output_dir = None

        def subpath_after(base_path):
            return os.path.relpath(file_dir, os.path.join(drive + os.sep, base_path.lstrip(os.sep)))

        if path_after_drive_lower.startswith(base_props_relative) and file_lower.startswith("p_"):
            output_dir = os.path.join(base_library, "Props", subpath_after(base_props_relative))
        elif path_after_drive_lower.startswith(base_creatures_relative) and file_lower.startswith("c_"):
            output_dir = os.path.join(base_library, "Creatures", subpath_after(base_creatures_relative))
        elif path_after_drive_lower.startswith(base_outfits_relative):
            if file_lower.startswith("o_"):
                output_dir = os.path.join(base_library, "Outfits", subpath_after(base_outfits_relative))
            elif file_lower.startswith("c_"):
                output_dir = os.path.join(base_library, "Hair", subpath_after(base_outfits_relative))
        elif path_after_drive_lower.startswith(base_effects_relative) and file_lower.startswith("fx_"):
            output_dir = os.path.join(base_library, "Effects", subpath_after(base_effects_relative))
        elif (path_after_drive_lower.startswith(base_characters_relative)
            and not path_after_drive_lower.startswith(base_creatures_relative)
            and not path_after_drive_lower.startswith(base_outfits_relative)
            and file_lower.startswith("c_")):
            output_dir = os.path.join(base_library, "Characters", subpath_after(base_characters_relative))
        
        return output_dir
    
    def clean_ma_file(self, filepath):
        """
        Remove plugins from the .ma text file to prevent crashes.
        """
        try:
            # Unset read-only flag
            file_attrs = os.stat(filepath).st_mode
            if not file_attrs & stat.S_IWRITE:
                os.chmod(filepath, file_attrs | stat.S_IWRITE)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            # Remove lines that contain the string
            cleaned_lines = [line for line in lines if '"Unfold3DUnfold"' not in line]
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to clean {filepath}: {e}")
            return False
        
    def record_failure(self, scene_file, note=""):
        """
        Append the scene path to MayaToEagleFailures_log.txt.
        Called from every crash / timeout / non-zero exit path.
        """
        failures_log = os.path.join(self.get_base_path(), "MayaToEagleFailures_log.txt")
        try:
            if os.path.exists(failures_log):
                os.chmod(failures_log, stat.S_IWRITE)
            with open(failures_log, "a") as f:
                f.write(scene_file + " --- " + note + "\n")
            self.log_output.append(f"❌ Logged failure for: {scene_file}")
        except Exception as e:
            self.log_output.append(f"Error writing to failures log: {e}")

    def run_maya_render(self):
        self.log_output.clear()
        failures_log = os.path.join(self.get_base_path(), "MayaToEagleFailures_log.txt")
        with open(failures_log, "w") as f:
            pass

        scene_folder = self.scene_folder_edit.text().strip()
        if not scene_folder:
            self.log_output.append("Error: Please select a scene folder.")
            return

        # Scan for .ma files meeting the criteria.
        self.scene_files = []
        for root, dirs, files in os.walk(scene_folder):
            for file in files:
                if file.lower().endswith("_rig.ma"):
                    full_path = os.path.join(root, file)
                    out_dir = self.get_output_dir_for_file(full_path)
                    if out_dir:
                        self.scene_files.append((full_path, out_dir))

        if not self.scene_files:
            self.log_output.append("Error: The .ma files must be in one of the renderable folders (Props, Outfits, Hair, Characters, Creatures, Effects)")
            return

        self.current_index = 0
        self.log_output.append(f"Found {len(self.scene_files)} matching .ma file(s) in folder: {scene_folder}")
        self.progress_bar.setMaximum(len(self.scene_files))
        self.progress_bar.setValue(0)
        self.run_next_render()

    def run_next_render(self):
        if self.current_index < len(self.scene_files):
            scene_file, output_dir = self.scene_files[self.current_index]

            # Clean the .ma file before rendering
            self.log_output.append(f"Cleaning file: {scene_file}")
            success = self.clean_ma_file(scene_file)
            if success:
                self.log_output.append("Cleaning complete.")
            else:
                self.log_output.append("Cleaning failed. Proceeding anyway.")

            # Skip any file containing 'incrementalSave' in the path
            if "incrementalSave" in scene_file:
                self.log_output.append(f"\n=== Skipping file with 'incrementalSave' in path: {scene_file} ===\n")
                self.current_index += 1
                self.progress_bar.setValue(self.current_index)
                self.run_next_render()
                return
        
            self.log_output.append(f"\n--- Rendering file {self.current_index+1} of {len(self.scene_files)}: {scene_file} ---\n")
            self.log_output.append(f"Output directory: {output_dir}")

            # Ensure the output directory exists
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    self.log_output.append(f"Created output directory: {output_dir}")
                except Exception as e:
                    self.log_output.append("Error creating output directory: " + str(e))
                    return
            
            # Check if we should skip this file if it already exists
            base_filename = os.path.splitext(os.path.basename(scene_file))[0]
            clean_base = re.sub(r'\.\d+$', '', base_filename)
            clean_base = re.sub(r'^(c_|o_|p_|fx_|.+?_)', '', clean_base)
            clean_base = re.sub(r'_rig$', '', clean_base)
            existing_images = [
                f for f in os.listdir(output_dir)
                if f.lower().endswith(".png") and os.path.splitext(f)[0].lower() == clean_base.lower()
            ]
            if self.overwrite_checkbox.isChecked() and existing_images:
                self.log_output.append(f"\n=== Skipping render. Existing render image found for: {base_filename} ===\n")
                self.current_index += 1
                self.progress_bar.setValue(self.current_index)
                self.run_next_render()
                return
            
            log_dir = self.get_base_path()

            # Format the Maya script with the current scene file and its specific output directory
            formatted_script = MAYA_SCRIPT.format(
                scene_file=scene_file,
                output_dir=output_dir,
                log_dir=log_dir
            )

            # Write the temporary Maya script
            script_path = os.path.join(self.get_base_path(), "maya_render_script.py")
            try:
                with open(script_path, "w") as f:
                    f.write(formatted_script)
            except Exception as e:
                self.log_output.append("Error writing temporary script: " + str(e))
                return

            arguments = [script_path]
            self.log_output.append("Executing command:")
            self.log_output.append(MAYA_BIN + " " + " ".join(arguments))
            self.log_output.append("-----\n")

            self.process = QProcess(self)
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            # catch hard crashes and pipe/IO errors
            self.process.errorOccurred.connect(self.handle_process_error)
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(
                lambda exitCode, exitStatus: self.on_process_finished(exitCode, exitStatus, script_path, scene_file)
            )
            self.process.start(MAYA_BIN, arguments)
        else:
            self.log_output.append("\n==========================")
            self.log_output.append("=== All files have been processed ===")
            self.log_output.append("==========================")

    def handle_process_error(self, error):
        from PySide2.QtCore import QProcess
        if error in (QProcess.Crashed,
                    QProcess.ReadError,
                    QProcess.WriteError):
            scene_file = self.scene_files[self.current_index][0]
            self.record_failure(scene_file, "Maya crashed or pipe broke (errorOccurred).")

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.log_output.append(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.log_output.append(data)

    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def upload_images_to_eagle(self):
        self.log_output.append("\n--- Uploading Images to Eagle ---\n")

        selected_types = []
        selected_types = [name for name, checkbox in self.checkboxes.items() if checkbox.isChecked()]

        if not selected_types:
            self.log_output.append("No categories selected for upload.")
            return
        
        scene_folder = self.scene_folder_edit.text().strip()
        if not scene_folder:
            possible_drives = [f"{chr(letter)}:\\" for letter in range(67, 91)]  # Scan C to Z drives
            for drive in possible_drives:
                perforce_path = os.path.join(drive, "Perforce")
                if os.path.exists(perforce_path) and os.path.isdir(perforce_path):
                    scene_folder = perforce_path 
            if not scene_folder:
                self.log_output.append("Error: Please select any scene folder first so we know where your Perforce files exist on your machine")
                return
        drive = os.path.splitdrive(scene_folder)[0]
        if not drive:
            self.log_output.append("Error: Could not determine drive letter from scene folder.")
            return

        base_library = os.path.join(drive + os.sep, "Perforce", "Potter", "Art", "EagleFiles")
        upload_script = os.path.join(self.get_base_path(), "UploadToEagle.py")

        for category in selected_types:
            json_filename = f"render_data_{category.lower()}.json"
            json_path = os.path.join(base_library, category, json_filename)

            if not os.path.exists(json_path):
                self.log_output.append(f"JSON not found for {category}: {json_path}")
                continue

            try:
                with open(json_path, "r") as f:
                    json_data = json.load(f)
            except Exception as e:
                self.log_output.append(f"Error loading JSON for {category}: {e}")
                continue

            confirm_text = (
                f"You are about to upload all rendered {category} assets to the {category} Eagle library.\n\n"
                f"Please confirm Eagle UI is focused on the {category} library before uploading.\n\n"
                f"→ JSON Data: {json_filename}\n"
                f"→ Target Eagle Folder: '{category}'\n\n"
                "Continue?"
            )

            reply = QMessageBox.question(self, "Confirm Upload", confirm_text, QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.log_output.append(f"Upload canceled for {category}.\n")
                continue

            self.log_output.append(f"\nUploading for {category} from {json_path}\n")

            env = os.environ.copy()
            env["JSON_FILE_PATH"] = json_path
            python_exe = shutil.which("python") or shutil.which("python3")
            if not python_exe:
                self.log_output.append("Python executable not found.")
                return

            try:
                result = subprocess.run(
                    [python_exe, upload_script],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.log_output.append(result.stdout)
                self.log_output.append(f"Finished upload for: {category}\n")
            except subprocess.CalledProcessError as e:
                self.log_output.append(f"Upload failed for {category}: {e}\n")
                self.log_output.append(e.stdout)
                self.log_output.append(e.stderr)

    def on_process_finished(self, exitCode, exitStatus, script_path, scene_file):
        # log to UI
        self.log_output.append(f"\nProcess finished for {scene_file} with exit code: {exitCode}")

        if exitStatus == QProcess.CrashExit:
            self.record_failure(scene_file, "QProcess reported CrashExit.")
        
        # if it failed, write to failures log
        CRASH_CODES = {3221225477, 3221225785} 
        if exitCode == 0:
            self.log_output.append(f"✔️ Process succeeded: {scene_file}")
        elif exitCode in CRASH_CODES or exitCode < 0:
            self.record_failure(scene_file, "LARGE TEXTURE CRASH")
        else:
            self.record_failure(scene_file, "PLUGIN OR OTHER ERROR")

        # clean up the temp script
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
                self.log_output.append("\nCleanup complete.")
            except Exception as e:
                self.log_output.append("Error removing temporary script file: " + str(e))
        
        # advance to next file
        self.current_index += 1
        self.progress_bar.setValue(self.current_index)
        self.run_next_render()

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MayaRenderGUI()
    window.show()
    sys.exit(app.exec_())
