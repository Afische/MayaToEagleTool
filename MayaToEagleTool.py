import sys
import os
import re
import stat
import json
import shutil
import subprocess
import requests
from PySide2.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QLineEdit, QTextEdit, QFileDialog, QCheckBox, QMessageBox, QProgressBar, QComboBox
)
from PySide2.QtCore import Qt, QProcess
from PySide2.QtGui import QFont, QIcon
import GDocsHelperEagle as GDocsHelper

# Path to Maya’s mayapy executable
MAYA_BIN = r"C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe"
EAGLE_API_LIST = "http://localhost:41595/api/item/list"
EAGLE_API_MOVE_TO_TRASH = "http://localhost:41595/api/item/moveToTrash"

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
import sys
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
summary_json_path = r"{summary_json}"
try:
    if mel.eval('pluginInfo -q -loaded "renderSetup"'):
        cmds.unloadPlugin("renderSetup", force=True)
        print("renderSetup plugin was loaded and is now unloaded.")
except Exception as e:
    print("Warning unloading renderSetup:", e)

# ensure Arnold attrs exist so ASCII parses cleanly
try:
    if not cmds.pluginInfo("mtoa", q=True, loaded=True):
        cmds.loadPlugin("mtoa", quiet=True)
        print("[Init] Loaded mtoa for Arnold attributes.")
except Exception as e:
    print("[Init] mtoa not available (continuing):", e)

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

try:

    # === CLEAN SCENE OF POTENTIAL BAD DEFAULT REFERENCE LAYERS ==

    did_rehost = False
    cleanScene = False
    cmds.file(original_scene, open=True, force=True)
    scene_loaded = cmds.file(query=True, sceneName=True)
    print("Scene loaded path:", scene_loaded)
    if cmds.objExists("defaultRenderLayer"):
        try:
            if not cmds.referenceQuery("defaultRenderLayer", isNodeReferenced=True):
                # local defaultRenderLayer exists
                current = None
                try:
                    current = cmds.editRenderLayerGlobals(q=True, currentRenderLayer=True)
                except:
                    pass
                if current == "defaultRenderLayer":
                    cleanScene = True
        except:
            pass
    if not cleanScene:
        # Open original, export assemblies, import into fresh scene, rebuild defaultRenderLayer
        assemblies = [n for n in cmds.ls(assemblies=True) if n not in ("front", "persp", "side", "top")]
        cmds.select(assemblies, r=True)
        tmpPath = cmds.internalVar(userTmpDir=True).replace("\\\\", "/") + "temp_scene_export.ma"
        cmds.file(tmpPath, es=True, force=True, type="mayaAscii", options="v=0")
        cmds.file(new=True, force=True)
        cmds.file(tmpPath, i=True, mergeNamespacesOnClash=True, namespace=":")
        try:
            rehost_path = os.path.join(tempfile.gettempdir(), "rehost_working_scene.ma").replace("\\\\", "/")
            cmds.file(rename=rehost_path)
            cmds.file(save=True, type="mayaAscii")
            scene_loaded = rehost_path  # keep logs/logic happy
            print(f"[Rehost] Saved working scene to: {{rehost_path}}")
        except Exception as e:
            print(f"[Rehost] Could not save rehosted scene: {{e}}")
        # Ensure a manager exists
        if not cmds.objExists("renderLayerManager"):
            try:
                cmds.createNode("renderLayerManager", name="renderLayerManager")
            except:
                pass
        # Make sure defaultRenderLayer exists and is current+renderable
        if not cmds.objExists("defaultRenderLayer"):
            try:
                cmds.createNode("renderLayer", name="defaultRenderLayer", shared=True)
                print("[Layers] Created defaultRenderLayer")
            except Exception as e:
                print(f"[Layers] Could not create defaultRenderLayer: {{e}}")
        layerName = "defaultRenderLayer"
        try:
            cmds.editRenderLayerGlobals(currentRenderLayer=layerName)
            if cmds.objExists(f"{{layerName}}.renderable"):
                cmds.setAttr(f"{{layerName}}.renderable", 1)
        except:
            pass
        try:
            os.remove(tmpPath)
        except:
            pass
        did_rehost = True
        print("[Cleaned scene of bad render layers]")
    else:
        print("Scene render layers are good")

    # === LOAD SCENE ===

    if not did_rehost:
        cmds.file(original_scene, open=True, force=True)
        scene_loaded = cmds.file(query=True, sceneName=True)
        if not scene_loaded:
            print("!!! ERROR: Maya failed to open the scene file !!!")
    print("Scene loaded path:", scene_loaded)
    if (not did_rehost) and (not scene_loaded):
        print("!!! ERROR: Maya failed to open the scene file (empty sceneName) !!!")
    print(f"Opened original scene: {{original_scene}}")
    project_dir = cmds.workspace(q=True, rootDirectory=True)

    # === CLEANUP ORPHAN REFERENCE NODES ===

    for rn in cmds.ls(type='reference'):
        try:
            _ = cmds.referenceQuery(rn, filename=True)
        except RuntimeError:
            try:
                cmds.lockNode(rn, l=False)
                cmds.delete(rn)
                print("Deleted orphan reference node:", rn)
            except Exception as e:
                print("Could not delete orphan reference node:", rn, e)

    # === ENSURE CHARACTER LIGHTING IS IMPORTED ===

    light_template_path = os.path.join(project_dir, "Lights", "ForTexturing", "characterLights_template.ma")
    if cmds.objExists("characterLights_template:KeyLight"):
        try:
            if cmds.referenceQuery("characterLights_templateRN", isNodeReferenced=True):
                cmds.file(removeReference=True, referenceNode="characterLights_templateRN")
        except RuntimeError as e:
            print(f"Warning: Failed to remove characterLights_templateRN reference: {{e}}")
    try:
        lightNodes = []
        lightNodes = cmds.file(light_template_path, reference=True, type="mayaAscii", ignoreVersion=True, namespace="characterLights_template", options="v=0;", returnNewNodes=True)
        print("Referenced characterLights_template.ma successfully.")
    except Exception as e:
        print(f"Failed to reference characterLights_template.ma: {{e}}")

    # === HIDE ALL MESHES UNDER ANY NonExportGeo GROUP IN THE SCENE ===

    all_render_layers = cmds.ls(type="renderLayer") or []
    ml_render_layers = [layer for layer in all_render_layers if layer.startswith("ML_")]
    render_layers_to_process = []
    current_layer = cmds.editRenderLayerGlobals(q=True, currentRenderLayer=True)
    render_layers_to_process = [current_layer] + ml_render_layers

    for render_layer in render_layers_to_process:
        try:
            _is_ref = False
            try:
                _is_ref = cmds.referenceQuery(render_layer, isNodeReferenced=True)
            except Exception:
                _is_ref = False
            if not (render_layer == "defaultRenderLayer" and _is_ref):
                cmds.editRenderLayerGlobals(currentRenderLayer=render_layer)
            else:
                print(f"[Layer] '{{render_layer}}' is referenced; not making it current.")
        except Exception as _e:
            print(f"[Layer] Could not set currentRenderLayer='{{render_layer}}': {{_e}}")

        print(f"Processing (or safely skipping) render layer: {{render_layer}}")
        for group in (cmds.ls("NonExportGeo", type="transform", long=True) or []):
            for node in (cmds.listRelatives(group, allDescendents=True, fullPath=True) or []):
                if cmds.nodeType(node) == 'mesh':
                    transform = cmds.listRelatives(node, parent=True, fullPath=True)
                    if transform:
                        cmds.setAttr(f"{{transform[0]}}.visibility", 0)
                        print(f"Hid non-export mesh: {{transform[0]}}")

    # === FIND GRP_GEO MESH(S)===

    geo_candidates = [x for x in cmds.ls(type="transform", long=True) if x.endswith("|grp_geo")]
    if not geo_candidates:
        geo_candidates = cmds.ls("Char_Rig|grp_other|grp_geo", long=True)
    if not geo_candidates:
        geo_candidates = cmds.ls("|*|grp_mesh", long=True)
    if geo_candidates:
        grp_geo_name = geo_candidates[0]
        print(f"Found `grp_geo`: {{grp_geo_name}}")
    else:
        print("Error: The group 'grp_geo' does not exist even after loading references!")
        print("Scene hierarchy:", cmds.ls(dag=True, long=True))
        sys.exit(1)

    # === COMPUTE INITIAL BOUNDING BOX FOR GRP_GEO AND REMOVE ANY DEFORMER HISTORY ===
    
    bbox = cmds.exactWorldBoundingBox(grp_geo_name)
    x_min, y_min, z_min, x_max, y_max, z_max = bbox
    bbox_width = x_max - x_min
    bbox_height = y_max - y_min
    bbox_depth = z_max - z_min
    meshes = cmds.listRelatives(grp_geo_name, allDescendents=True, type="mesh") or []
    mesh_shapes = cmds.ls(meshes, ni=True, l=True) or []
    print(f"grp_geo bounding box: width={{bbox_width}}, height={{bbox_height}}, depth={{bbox_depth}}")
            
    # === CALCULATE POLY COUNT AND INITIALIZE JSON DICTIONARY===

    poly_count = 0
    for mesh in mesh_shapes:
        try:
            tri = cmds.polyEvaluate(mesh, triangle=True)
            if isinstance(tri, dict):
                tri = sum(tri.values())
            poly_count += (tri or 0)
        except:
            pass

    print(f"Polygon count for grp_geo: {{poly_count}}")
    render_data = {{}}

    # === CREATE DUPLICATES OF GRP_GEO IN DIFFERENT PERSPECTIVES ===

    views_to_render = json.loads(r'''{views_json}''') or []
    views_lower = {{str(v).strip().lower() for v in views_to_render}}
    print("Views passed in:", views_to_render)

    # Default views when no views specified
    dup_left = dup_top = dup_back = None
    if not views_lower:
        offset1 = x_max + z_max + 0.5
        dup_grp1 = cmds.duplicate(grp_geo_name, name="grp_geo_dup1")[0]
        cmds.rotate(0, -90, 0, dup_grp1, relative=True, objectSpace=True)
        cmds.xform(dup_grp1, ws=True, t=(offset1, 0, 0))
        amount1 = x_max + z_max + 0.5

        dup_grp2 = cmds.duplicate(grp_geo_name, name="grp_geo_dup2")[0]
        if is_prop_file:
            cmds.rotate(90, 0, -90, dup_grp2, relative=True, objectSpace=True)  # TOP
            amount2 = x_max + max(y_max, abs(z_min)) + 0.5
        else:
            cmds.rotate(0, 180, 0, dup_grp2, relative=True, objectSpace=True)  # BACK
            amount2 = x_max + abs(z_min) + 0.5

        offset2 = amount1 + amount2
        cmds.xform(dup_grp2, ws=True, t=(offset2, 0, 0))
        dup_left = dup_top = dup_back = None
        dup_left = dup_grp1
        dup_top  = dup_grp2 if is_prop_file else None
        dup_back = dup_grp2 if not is_prop_file else None

    else:
        # Selected views to render
        want_front = ('front' in views_lower)
        want_left  = ('left'  in views_lower)
        want_back  = ('back'  in views_lower)
        want_top   = ('top'   in views_lower)
        dup_left = dup_top = dup_back = None
        
        # Use a gap that scales with the original grp_geo width
        orig_bb = cmds.exactWorldBoundingBox(grp_geo_name)
        orig_width = max(orig_bb[3] - orig_bb[0], 0.001)
        offset = 0.05
        gap = orig_width * offset

        # Get right edge of bounding box
        current_right = orig_bb[3]

        if want_left:
            dup_left = cmds.duplicate(grp_geo_name, name="grp_geo_left")[0]
            cmds.rotate(0, -90, 0, dup_left, relative=True, objectSpace=True)
            bb = cmds.exactWorldBoundingBox(dup_left)
            minX, minY, maxX, maxY = bb[0], bb[1], bb[3], bb[4]
            dx = (current_right + gap) - minX
            cmds.move(dx, 0, 0, dup_left, r=True, ws=True)
            current_right = cmds.exactWorldBoundingBox(dup_left)[3]

        if want_back:
            dup_back = cmds.duplicate(grp_geo_name, name="grp_geo_back")[0]
            cmds.rotate(0, 180, 0, dup_back, relative=True, objectSpace=True)
            bb = cmds.exactWorldBoundingBox(dup_back)
            minX, minY, maxX, maxY = bb[0], bb[1], bb[3], bb[4]
            dx = (current_right + gap) - minX
            cmds.move(dx, 0, 0, dup_back, r=True, ws=True)
            current_right = cmds.exactWorldBoundingBox(dup_back)[3]

        if want_top:
            dup_top = cmds.duplicate(grp_geo_name, name="grp_geo_top")[0]
            cmds.rotate(90, 0, -90, dup_top, relative=True, objectSpace=True)
            bb = cmds.exactWorldBoundingBox(dup_top)
            minX, minY, maxX, maxY = bb[0], bb[1], bb[3], bb[4]
            dx = (current_right + gap) - minX
            orig_cy = (y_min + y_max) / 2.0
            dup_cy  = (minY  + maxY) / 2.0
            dy = (orig_cy - dup_cy)
            cmds.move(dx, dy, 0, dup_top, r=True, ws=True)
            current_right = cmds.exactWorldBoundingBox(dup_top)[3]

        # Remove FRONT (original) if not requested
        if not want_front:
            try:
                cmds.delete(grp_geo_name)
                print("Removed original grp_geo because 'Front' not requested.")
            except Exception as e:
                print("Warning: failed to delete grp_geo:", e)

    # === CREATE NEW ORTHOGRAPHIC CAMERA ===

    if cmds.objExists("EagleCamera1"):
        cmds.delete("EagleCamera1")

    camera_transform = cmds.camera(name="EagleCamera1")[0]  # transform node
    camera_shapes = cmds.listRelatives(camera_transform, shapes=True) or []
    if camera_shapes:
        # Rename to a stable, known shape name
        camera_shape = cmds.rename(camera_shapes[0], "EagleCamera1Shape")
    else:
        print("Error: Camera shape not found!")
        cmds.error("Camera shape missing after creation.")

    # Toggle attributes on the SHAPE
    cmds.setAttr(camera_shape + ".renderable", True)
    cmds.setAttr(camera_shape + ".orthographic", True)
    cmds.setAttr(camera_shape + ".orthographicWidth", 10.0)
    print("Created camera:", camera_transform, "with shape:", camera_shape)

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

    # === COMPUTE OVERALL BOUNDING BOX OF EXISTING MESHES ===

    bbox_targets = []
    if cmds.objExists(grp_geo_name):
        bbox_targets.append(grp_geo_name)
    for n in (dup_left, dup_top, dup_back):
        if n and cmds.objExists(n):
            bbox_targets.append(n)
    if not bbox_targets:
        bbox_targets = [grp_geo_name]

    overall_bbox = cmds.exactWorldBoundingBox(*bbox_targets)
    ov_x_min, ov_y_min, ov_z_min, ov_x_max, ov_y_max, ov_z_max = overall_bbox
    margin = 1.05
    overall_bb_width  = max((ov_x_max - ov_x_min) * margin, 0.01)
    overall_bb_height = max((ov_y_max - ov_y_min) * margin, 0.01)
    overall_bb_depth  = max((ov_z_max - ov_z_min) * margin, 0.01)

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
    cmds.setAttr(f"{{camera_shape}}.orthographicWidth", overall_bb_width)
    cmds.setAttr("defaultResolution.deviceAspectRatio", dynamic_aspect)
    print("Render resolution set to 1920 x", pixel_height)
    print("Orthographic width set to:", overall_bb_width)
    # Set the near clip plane to 0.001
    #cmds.setAttr(f"{{camera_shape}}.nearClipPlane", 0.001)

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
            # Camera looking from above
            cam_pos = [center_x, ov_y_max + 100, center_z]
            cam_rot = [-90, 0, 0]
            ortho_width = max(overall_bb_width, overall_bb_depth) * 1.05
            dynamic_aspect = overall_bb_width / overall_bb_depth

        if ortho_width < 0.0001:
            ortho_width = 0.01
        pixel_height = int(1920 / dynamic_aspect)
        cmds.xform(camera_transform, ws=True, t=cam_pos)
        cmds.setAttr(f"{{camera_transform}}.rotateX", cam_rot[0])
        cmds.setAttr(f"{{camera_transform}}.rotateY", cam_rot[1])
        cmds.setAttr(f"{{camera_transform}}.rotateZ", cam_rot[2])
        cmds.setAttr(camera_shape + ".orthographicWidth", overall_bb_width)
        print(f"[Camera] Camera positioned at {{cam_pos}} with rotation {{cam_rot}}")
        print(f"[Camera] Ortho width: {{ortho_width}}, aspect: {{dynamic_aspect}}, height: {{pixel_height}}")

    else:
        # Default camera placement for non-flat objects
        center_x = (ov_x_min + ov_x_max) / 2.0
        center_y = (ov_y_min + ov_y_max) / 2.0
        global_z_max = ov_z_max
        cam_pos = (center_x, center_y, global_z_max + 100)
        cmds.xform(camera_transform, ws=True, t=cam_pos)
        dynamic_aspect = overall_bb_width / overall_bb_height
        pixel_height = int(1920 / dynamic_aspect)
        cmds.setAttr(f"{{camera_shape}}.orthographicWidth", overall_bb_width)
        print("[Camera] Default camera positioning:", cam_pos)
        print(f"[Camera] Default ortho width: {{overall_bb_width}}, aspect: {{dynamic_aspect}}, height: {{pixel_height}}")

    # === SET ORTHO AS THE RENDERABLE CAMERA ===

    # Disable renderable on all camera shapes
    for cam_shape in (cmds.ls(type="camera") or []):
        try:
            cmds.setAttr(cam_shape + ".renderable", 0)
        except Exception:
            pass
    # Enable only our camera's SHAPE
    try:
        cmds.setAttr(camera_shape + ".renderable", 1)
    except Exception:
        pass
    # We'll pass the TRANSFORM to Render.exe
    render_cam_transform = camera_transform
    print("[Camera] Using transform for Render.exe:", render_cam_transform)

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
    
    SHADERFX_SHADERS = cmds.ls(type='ShaderfxShader')
    SHADERFX_TEXTURE_ATTRS = ('.DiffuseMap', '.LightmapMap', '.SpecularMap','.DirtMap', '.SecondDiffuseMap', '.Diffuse','.SecondaryMaps', '.ColorMap', '.Mask')
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
                #filePath = cmds.getAttr(shader + attr)
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
    rig_tag = ""
    if not shader_texture_data:
        tagslist = []
    else:
        for shader, textures in shader_texture_data.items():
            texture_names = [os.path.basename(tex['filePath']).replace('.png', '').lower() for tex in textures]
            meshes = shader_to_meshes.get(shader, [])
            cleaned_meshes = [cmds.listRelatives(m, parent=True, fullPath=False)[0].lower() for m in meshes]
            keywords.extend(texture_names + cleaned_meshes + [shader.lower()])
        keywords_string = ''.join(keywords)

        print("keywords_string:")
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
                if cmds.referenceQuery(grp_geo_name, isNodeReferenced=True):
                    ref_node = cmds.referenceQuery(grp_geo_name, referenceNode=True)
                    rigUsed = str(ref_node)
                    rig_tag = re.sub(r'_?rn$', '', rigUsed, flags=re.IGNORECASE)
                else:
                    print('grp_geo is a local node, not a reference')
            else:
                print('grp_geo not found')
        print("")
        print("Tags:")
        print (tagslist)

    # === ADD LIGHTS TO ML_ RENDER LAYERS ===

    light_root = "characterLights_template:Lights" if cmds.objExists("characterLights_template:Lights") else None
    for render_layer in ml_render_layers:
        try:
            cmds.editRenderLayerGlobals(currentRenderLayer=render_layer)
            if light_root:
                cmds.editRenderLayerMembers(render_layer, light_root, noRecurse=False)
                shapes = cmds.listRelatives(light_root, ad=True, type="shape", f=True) or []
                if shapes:
                    cmds.editRenderLayerMembers(render_layer, shapes, noRecurse=True)
                print(f"Added lights to {{render_layer}}: {{light_root}}")
            else:
                print("No valid light group found to add.")
        except RuntimeError as e:
            print(f"Failed to add lights to {{render_layer}}: {{e}}")

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

    # === LOOP THROUGH EACH RENDER LAYER AND RENDER SEPARATELY ===

    for render_layer in render_layers_to_process:
        print(f"Setting render layer: {{render_layer}}")
        try:
            _is_ref = False
            try:
                _is_ref = cmds.referenceQuery(render_layer, isNodeReferenced=True)
            except Exception:
                _is_ref = False
            if not (render_layer == "defaultRenderLayer" and _is_ref):
                cmds.editRenderLayerGlobals(currentRenderLayer=render_layer)
            else:
                print(f"[Layer] '{{render_layer}}' is referenced; skipping set-current; relying on -rl.")
        except Exception as _e:
            print(f"[Layer] Could not set currentRenderLayer='{{render_layer}}': {{_e}}")
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
            "-cam", render_cam_transform,
            "-rd", output_dir,
            "-of", "png",
            "-im", filename_with_layer,
            "-fnc", "3",
            "-rl", render_layer,
            "-log", log_file,
            temp_scene_path
        ]

        print("Executing Render.exe with command:")
        print(" ".join(render_cmd))

        # === RUN THE RENDERING PROCESS ===

        process = subprocess.run(render_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

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

    # === WRITE EAGLE JSON FILE ===

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
    if os.path.exists(json_file):
        try:
            os.chmod(json_file, stat.S_IWRITE)
        except Exception as e:
            print(f"Warning: Could not make JSON file writable: {{e}}")
    try:
        with open(json_file, "w") as jf:
            jf.write(json_str)
        print("Render JSON data written to:", json_file)
    except Exception as e:
        print(f"Failed to write JSON file: {{e}}")

    # === WRITE SUMMARY JSON DATA ===
    try:
        asset_name = os.path.splitext(os.path.basename(original_scene))[0]
        num_shaders = len(connected_shaders)
        num_textures = sum(len(v) for v in shader_texture_data.values())
        missing_textures = any(
            (t.get('filePath') and not os.path.exists(t['filePath']))
            for texlist in shader_texture_data.values() for t in texlist
        )
        scene_rel = original_scene.replace(os.sep, "/").split("/Perforce/", 1)[-1]
        p4_path = f"//{{scene_rel}}"

        summary = {{
            "type": file_type,                 # e.g. "props", "effects"
            "asset": asset_name,               # scene name minus .ma
            "path": p4_path,                   # Perforce-style path
            "polycount": poly_count,
            "num_textures": num_textures,
            "num_shaders": num_shaders,
            "missing_textures": missing_textures
        }}
        with open(summary_json_path, "w") as sf:
            json.dump(summary, sf)
        print("[EAGLE_SUMMARY]", json.dumps(summary))  # optional breadcrumb
    except Exception as e:
        print("Failed to write summary JSON:", e)

    # === CLEANUP: REMOVE TEMP SCENE FILE AFTER ALL RENDERS COMPLETE ===

    if os.path.exists(temp_scene_path):
        os.remove(temp_scene_path)
        print(f"Temporary scene deleted: {{temp_scene_path}}")

    try:
        if 'rehost_path' in locals() and os.path.exists(rehost_path):
            os.remove(rehost_path)
            print(f"[Rehost] Deleted temp rehost file: {{rehost_path}}")
    except Exception as e:
        print(f"[Rehost] Could not delete rehost file: {{e}}")

    norm_outdir = output_dir.replace(os.sep, "/")
    print("Render complete! Check directory: " + norm_outdir)

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
        self.gdocs = GDocsHelper.GDocs()
        self.deleted_status = {}
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
            QPlainTextEdit {
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

        mode_row = QHBoxLayout()
        mode_label = QLabel("Render Options:")
        self.rerender_mode = QComboBox()
        self.rerender_mode.addItems(["Render New Entries Only","Re-Render If New View","Re-Render Crashed Renders Only","Force Re-Render All"])
        self.rerender_mode.setCurrentText("Render New Entries Only")
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.rerender_mode, 1)
        main_layout.addLayout(mode_row)

        self.rerender_deleted = QCheckBox("Re-Render Deleted Assets")
        self.rerender_deleted.setChecked(False)
        main_layout.addWidget(self.rerender_deleted)

        self.render_button = QPushButton("🚀 Render Scenes")
        self.render_button.clicked.connect(self.run_maya_render)
        main_layout.addWidget(self.render_button)

        checkbox_layout = QHBoxLayout()
        self.checkboxes = {
            "Characters": QCheckBox("Character"),
            "Creatures": QCheckBox("Creature"),
            "Effects": QCheckBox("Effects"),
            "Hair": QCheckBox("Hair"),
            "Outfits": QCheckBox("Outfits"),
            "Props": QCheckBox("Props")
        }
        for category, checkbox in self.checkboxes.items():
            checkbox.clicked.connect(self.make_exclusive)
            checkbox_layout.addWidget(checkbox)
        main_layout.addLayout(checkbox_layout)

        self.upload_button = QPushButton("📤 Upload Images To Eagle")
        self.upload_button.clicked.connect(self.upload_images_to_eagle)
        main_layout.addWidget(self.upload_button)

        delete_row = QHBoxLayout()
        self.delete_label = QLabel("Delete by Asset or Link:")
        self.delete_input = QPlainTextEdit()
        self.delete_input.setPlaceholderText("Enter asset name (e.g. p_MyProp_rig) or a .ma/.png link")
        default_h = self.scene_folder_edit.sizeHint().height()
        self.delete_input.setFixedHeight(default_h)
        self.delete_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.delete_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.delete_input.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.delete_button = QPushButton("🗑️ Delete from Eagle + Sheets")
        self.delete_button.clicked.connect(self.delete_assets)
        delete_row.addWidget(self.delete_label)
        delete_row.addWidget(self.delete_input, 1)
        delete_row.addWidget(self.delete_button)
        main_layout.addLayout(delete_row)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 10))
        self.log_output.append = self.log_output.appendPlainText
        main_layout.addWidget(self.log_output)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)
        self.setWindowTitle(" Maya To Eagle Renderer")
        self.setMinimumWidth(600)
        self.setGeometry(300, 300, 800, 800)

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
        
    def get_checked_views(self, scene_file, summary=None):
        """
        Return a list of views (Front/Left/Back/Top) to use for this scene
        If new entry: defaults - FLB, props - FLT)
        If existing entry: read from sheet checkboxes
        """
        output_dir = self.get_output_dir_for_file(scene_file) or ""
        sheet  = GDocsHelper._category_from_output_dir(output_dir)
        asset  = os.path.splitext(os.path.basename(scene_file))[0]

        try:
            row, row_num = self.gdocs.getRow(sheet, asset)
            if row is None:
                # New entry defaults
                type_value = None
                if summary and summary.get('type'):
                    type_value = str(summary.get('type')).lower()
                else:
                    type_value = GDocsHelper._normalize_sheet_id(sheet).lower()

                if type_value.startswith("prop"):
                    return ["Front", "Left", "Top"]
                else:
                    return ["Front", "Left", "Back"]
            else:
                # Existing entry - checkboxes from sheet
                row_dict = self.gdocs.to_dict(sheet, row)
                checked = []
                for key, label in (('front', 'Front'), ('left', 'Left'), ('back', 'Back'), ('top', 'Top')):
                    v = row_dict.get(key)
                    if v and str(v).strip().lower() in ("true", "yes", "y", "1", "checked", "on", "☑", "☒"):
                        checked.append(label)
                return checked
        except Exception as e:
            self.log_output.append(f"[ERROR] get_checked_views failed for {asset}: {e}")
            return []
        
    def views_to_checkbox_payload(self, views):
        views_lower = {v.strip().lower() for v in (views or [])}
        return {
            'front': 'front' in views_lower,
            'left':  'left'  in views_lower,
            'back':  'back'  in views_lower,
            'top':   'top'   in views_lower,
        }

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
        
        # Force fresh read from Google Sheets on each run
        try:
            self.gdocs = GDocsHelper.GDocs()
        except Exception as e:
            self.log_output.append(f"[WARN] Could not reset Google Sheets helper: {e}")

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

            # Skip based on sheet state and overwrite checkbox
            base_filename = os.path.splitext(os.path.basename(scene_file))[0]
            try:
                sheet = GDocsHelper._category_from_output_dir(output_dir)
                asset = os.path.splitext(os.path.basename(scene_file))[0]
                row, _ = self.gdocs.getRow(sheet, asset)
                key = os.path.splitext(os.path.basename(scene_file))[0].lower()
                skip = False
                skip_msg = None
                mode = self.rerender_mode.currentText()

                if row is None:
                    self.deleted_status[key] = None
                    if mode == "Re-Render Crashed Renders Only":
                        skip = True
                        skip_msg = f"No existing row (nothing crashed) for: {key}"

                if row is not None and not skip:
                    row_dict = self.gdocs.to_dict(sheet, row)
                    TRUE_VALUES = {'true','yes','y','1','checked','on','☑','☒'}
                    deleted_raw = str(row_dict.get('deleted', '') or '').strip().lower()
                    is_deleted = deleted_raw in TRUE_VALUES
                    self.deleted_status[key] = is_deleted
                    if is_deleted:
                        if not self.rerender_deleted.isChecked():
                            skip = True
                            skip_msg = (f"Marked deleted in Sheets; enable 'Re-render deleted assets' "
                                        f"to process: {base_filename}")
                        else:
                            self.log_output.append(f"[Override] 'Deleted' is true and override is ON; "
                                                   f"forcing render for {base_filename}.")
                            pass
                    if not skip and not (is_deleted and self.rerender_deleted.isChecked()):
                        if mode == "Render New Entries Only":
                            skip = True
                            skip_msg = (f"Entry already exists: {base_filename}")
                        elif mode == "Re-Render Crashed Renders Only":
                            crashed_raw = str(row_dict.get('crashed', '') or '').strip()
                            crashed_norm = crashed_raw.lower()
                            if crashed_norm and not crashed_norm.startswith('no'):
                                skip = False
                                self.log_output.append(f"Re-rendering existing entry due to crashed='{crashed_raw}'.")
                            else:
                                skip = True
                                skip_msg = (f"Skipping non-crashed entry: {base_filename} "
                                            f"(crashed='{crashed_raw or 'No'}')")
                        elif mode == "Re-Render If New View":
                            allowed = {"Front", "Left", "Back", "Top"}
                            prev_raw = str(row_dict.get('previouslyrendered', '') or '')
                            prev_set = {t.title() for t in re.split(r'[,\s/;]+', prev_raw) if t.strip()} & allowed
                            selected_set = {
                                label for key, label in (('front','Front'), ('left','Left'), ('back','Back'), ('top','Top'))
                                if str(row_dict.get(key)).strip().lower() in TRUE_VALUES
                            } & allowed
                            if prev_set == selected_set and prev_set:
                                skip = True
                                skip_msg = ("'Previously Rendered' matches selected views "
                                            f"({', '.join(sorted(selected_set))}) for: {base_filename}")
                        elif mode == "Force Re-Render All":
                            pass

                if skip:
                    self.log_output.append(f"\n=== Skipping render. {skip_msg} ===\n")
                    self.current_index += 1
                    self.progress_bar.setValue(self.current_index)
                    self.run_next_render()
                    return
            except Exception as e:
                self.log_output.append(f"[WARN] Could not evaluate skip rule: {e}")

            log_dir = self.get_base_path()
            asset_name   = os.path.splitext(os.path.basename(scene_file))[0]
            summary_path = os.path.join(self.get_base_path(), f"summary_{asset_name}.json")
            try:
                if os.path.exists(summary_path):
                    os.remove(summary_path)
            except Exception:
                pass

            # Get checked camera angles
            views = self.get_checked_views(scene_file)
            self.log_output.append(f"[EAGLE] Views for {os.path.basename(scene_file)}: {', '.join(views) if views else 'None'}")
            # Format the Maya script with the current scene file and its specific output directory
            formatted_script = MAYA_SCRIPT.format(
                scene_file=scene_file,
                output_dir=output_dir,
                log_dir=log_dir,
                summary_json=summary_path,
                views_json=json.dumps(views)
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

            if self.process:
                try:
                    self.process.kill()
                except Exception:
                    pass
                self.process.deleteLater()
                self.process = None
            self.process = QProcess(self)
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            # catch hard crashes and pipe/IO errors
            self.process.errorOccurred.connect(self.handle_process_error)
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            #self.process.readyReadStandardError.connect(self.handle_stderr)
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
        data = self.process.readAllStandardOutput().data().decode('utf-8', 'ignore')
        self.log_output.append(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.log_output.append(data)

    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def _basename_no_ext(self, path_or_name: str) -> str:
        b = os.path.basename(path_or_name.strip())
        return os.path.splitext(b)[0].strip().lower()

    def _fetch_eagle_items(self):
        try:
            resp = requests.get(EAGLE_API_LIST, timeout=10)
            resp.raise_for_status()
            return resp.json().get("data", []) or []
        except Exception as e:
            self.log_output.append(f"[EAGLE] List error: {e}")
            return []

    def _trash_eagle_items(self, item_ids):
        if not item_ids:
            return False
        try:
            r = requests.post(EAGLE_API_MOVE_TO_TRASH, json={"itemIds": item_ids}, timeout=10)
            if r.status_code == 200:
                return True
            self.log_output.append(f"[EAGLE] moveToTrash failed: {r.text}")
        except Exception as e:
            self.log_output.append(f"[EAGLE] moveToTrash error: {e}")
        return False

    def _extract_asset_from_annotation_malink(self, annotation_text: str):
        """
        From an Eagle annotation we created (contains 'malink: //Potter/.../Something.ma'),
        return the scene asset name (basename without extension).
        """
        if not annotation_text:
            return None
        for line in str(annotation_text).splitlines():
            if line.strip().lower().startswith("malink:"):
                p = line.split(":", 1)[1].strip()
                if p:
                    try:
                        base = os.path.basename(p)
                        if base:
                            return os.path.splitext(base)[0]
                    except Exception:
                        pass
        return None
    
    def _parse_terms(self, raw_text: str):
        parts = re.split(r'[,\n;]+', raw_text or '')
        terms = [p.strip() for p in parts if p.strip()]
        seen, out = set(), []
        for t in terms:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                out.append(t)
        return out

    def _match_eagle_for_term(self, eagle_items, term: str):
        candidates = {self._basename_no_ext(term)}
        matched_ids = []
        inferred_assets = set()

        # infer asset directly from input if possible
        if term.lower().endswith(".ma"):
            inferred_assets.add(os.path.splitext(os.path.basename(term))[0])
        elif ("/" not in term and "\\" not in term and not term.lower().endswith(".png")):
            inferred_assets.add(term.strip())

        tl = term.lower()
        for it in eagle_items:
            eid  = it.get("id")
            name = it.get("name", "")
            note = it.get("annotation", "") or ""
            n_noext = os.path.splitext(name)[0].lower()

            name_hit = (n_noext in candidates)
            anno_hit = (tl in name.lower()) or (tl in str(note).lower())
            if name_hit or anno_hit:
                if eid:
                    matched_ids.append(eid)
                asset_from_anno = self._extract_asset_from_annotation_malink(note)
                if asset_from_anno:
                    inferred_assets.add(asset_from_anno)

        return matched_ids, inferred_assets
    
    def delete_assets(self):
        """
        Accept multiple assets/links (one per line or comma/semicolon-separated),
        trash matching Eagle items, and delete matching rows in Google Sheets.
        """
        raw = (self.delete_input.toPlainText() or "").strip()
        if not raw:
            self.log_output.append("Enter assets or links first.")
            return
        
        confirm_text = (
            "You are about to delete assets from both Eagle and Google Sheets.\n\n"
            "Please confirm Eagle UI is focused on the correct library before deleting.\n\n"
            "This action will:\n"
            "- Move matching Eagle items to the Trash\n"
            "- Mark rows as deleted in Google Sheets\n\n"
            "Are you sure you want to continue?"
        )
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            confirm_text,
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            self.log_output.append("Delete canceled by user.\n")
            return

        terms = self._parse_terms(raw)
        self.log_output.append(f"🧹 Deleting {len(terms)} item(s) from Eagle & Sheets...")

        eagle_items = self._fetch_eagle_items()
        if not eagle_items:
            self.log_output.append("[EAGLE] No items returned from Eagle.")
            return

        all_ids = []
        all_sheet_assets = set()

        for t in terms:
            ids, assets = self._match_eagle_for_term(eagle_items, t)
            if ids:
                self.log_output.append(f" • Eagle match for '{t}': {len(ids)} item(s)")
            else:
                self.log_output.append(f" • No Eagle match for '{t}'")
            all_ids.extend(ids)
            all_sheet_assets |= assets

        unique_ids = list({i for i in all_ids if i})
        if unique_ids:
            ok = self._trash_eagle_items(unique_ids)
            if ok:
                self.log_output.append(f"🗑️ Moved {len(unique_ids)} Eagle item(s) to Trash.")
            else:
                self.log_output.append("Eagle trash request failed.")
        else:
            self.log_output.append("No Eagle items to trash.")

        if not all_sheet_assets:
            self.log_output.append("No Sheets rows inferred. Tip: include .ma paths or asset names (e.g., p_MyProp_rig).")
            return

        deleted_any = False
        for asset in sorted(all_sheet_assets):
            try:
                sheetName, rowNum = self.gdocs.mark_asset_deleted(asset)
                if sheetName and rowNum:
                    self.log_output.append(f"✅ Deleted '{asset}' from Google Sheets tab '{sheetName}' (row {rowNum}).")
                    deleted_any = True
                else:
                    self.log_output.append(f"[Sheets] Row not found for asset '{asset}'.")
            except Exception as e:
                self.log_output.append(f"[Sheets] Delete failed for '{asset}': {e}")

        if not deleted_any:
            self.log_output.append("No rows were marked for delete.")

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
                f"- JSON Data: {json_filename}\n"
                f"- Target Eagle Folder: '{category}'\n\n"
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

        self.log_output.append(f"\nProcess finished for {scene_file} with exit code: {exitCode}")

        if exitStatus == QProcess.CrashExit:
            self.record_failure(scene_file, "QProcess reported CrashExit.")
        
        # if it failed, write to failures log
        CRASH_CODES = {3221225477, 3221225785}
        LAYER_EXIT_CODES = {211}
        UNKNOWN_DATA_CODES = {1}
        crashed = 'No'
        if exitCode == 0:
            self.log_output.append(f"✔️ Process succeeded: {scene_file}")
            crashed = 'No'
        elif exitCode in LAYER_EXIT_CODES:
            self.record_failure(scene_file, "EXIT 211 BAD DEFAULT LAYER")
            crashed = 'Yes, Exit 211 bad default layer'
        elif exitCode in UNKNOWN_DATA_CODES:
            self.record_failure(scene_file, "EXIT 1 FILE CONTAINS UNKNOWN DATA")
            crashed = 'Yes, Exit 1 Bad Data'
        elif exitCode in CRASH_CODES or exitCode < 0:
            self.record_failure(scene_file, "LARGE TEXTURE CRASH")
            crashed = 'Yes, Large Texture Crash'
        else:
            self.record_failure(scene_file, f"PLUGIN OR OTHER ERROR (exit {exitCode})")
            crashed = 'Yes, plugin or other error'

        if self.process:
            try:
                self.process.deleteLater()
            except Exception:
                pass
            self.process = None

        # clean up the temp script
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
                self.log_output.append("\nCleanup complete.")
            except Exception as e:
                self.log_output.append("Error removing temporary script file: " + str(e))

        # write from Eagle json to google sheets
        try:
            asset_name   = os.path.splitext(os.path.basename(scene_file))[0]
            summary_path = os.path.join(self.get_base_path(), f"summary_{asset_name}.json")
            summary = None
            if os.path.exists(summary_path):
                with open(summary_path, "r") as f:
                    summary = json.load(f)
                os.remove(summary_path)

            output_dir = self.get_output_dir_for_file(scene_file) or ""
            sheet  = GDocsHelper._category_from_output_dir(output_dir)
            asset  = os.path.splitext(os.path.basename(scene_file))[0]
            p4     = GDocsHelper._to_p4_path(scene_file)

            views_for_sheet = self.get_checked_views(scene_file)
            checkbox_payload = self.views_to_checkbox_payload(views_for_sheet)
            payload = {'asset': asset, 'path': p4}
            payload.update(checkbox_payload)
            if summary:
                payload.update({
                    'type':        summary.get('type'),
                    'polycount':        summary.get('polycount'),
                    'numberoftextures': summary.get('num_textures'),
                    'numberofshaders':  summary.get('num_shaders'),
                    'missingtextures':  'Yes' if summary.get('missing_textures') else 'No',
                })
            payload['crashed'] = crashed
            order = [('front', 'Front'), ('left', 'Left'), ('back', 'Back'), ('top', 'Top')]
            previously_rendered = ", ".join(label for key, label in order if bool(payload.get(key)))
            payload['Previously Rendered'] = previously_rendered

            asset_key = os.path.splitext(os.path.basename(scene_file))[0].lower()
            status = self.deleted_status.pop(asset_key, None)
            if status is None or (status is True and self.rerender_deleted.isChecked()):
                payload['deleted'] = False
                payload['Deleted'] = False

            self.gdocs.doUpdateConfig(sheet, payload)

        except Exception as e:
            self.log_output.append(f"Sheets update failed: {e}")

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
