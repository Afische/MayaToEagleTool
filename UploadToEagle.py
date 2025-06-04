import json
import os
import requests

# --- Eagle API Endpoints ---
EAGLE_API_LIST = "http://localhost:41595/api/item/list"
EAGLE_API_MOVE_TO_TRASH = "http://localhost:41595/api/item/moveToTrash"
EAGLE_API_ADD_FROM_PATH = "http://localhost:41595/api/item/addFromPath"
EAGLE_API_FOCUS = "http://localhost:41595/api/folder/open"

# --- Folder IDs within the shared Eagle library ---
FOLDER_IDS = {
    "creatures": "M9D7XXUNN2QHU",
    "hair": "M9D81F597PZ6N",
    "outfits": "M9D81SQAQOYBH",
    "characters": "M9D829A2UE0Y8",
    "props": "M9D82KZ6ELR64",
    "effects": "M9D82UNUFSGQA"
}

# --- Dynamically load JSON File Path from environment variable ---
JSON_FILE_PATH = os.environ.get("JSON_FILE_PATH")

if not JSON_FILE_PATH:
    print("Error: JSON_FILE_PATH environment variable not set.")
    exit(1)

# --- Global cache for preserved tags ---
preserved_tags_by_filename = {}

def delete_existing_images(render_data):
    global preserved_tags_by_filename

    target_filenames_no_ext = set()
    for info in render_data.values():
        img_path = info.get("imglink", "")
        if img_path:
            basename = os.path.basename(img_path)
            name_no_ext = os.path.splitext(basename)[0].lower()
            target_filenames_no_ext.add(name_no_ext)

    print("Checking Eagle for existing items to delete")

    try:
        list_resp = requests.get(EAGLE_API_LIST)
        list_resp.raise_for_status()
        all_items = list_resp.json().get("data", [])
    except requests.RequestException as e:
        print(f"Error retrieving items from Eagle: {e}")
        return

    item_ids_to_trash = []

    for item in all_items:
        eagle_name = item.get("name", "")
        item_id = item.get("id")
        tags = item.get("tags", [])

        if not item_id:
            continue

        eagle_name_no_ext = os.path.splitext(eagle_name)[0].lower()

        if eagle_name_no_ext in target_filenames_no_ext:
            item_ids_to_trash.append(item_id)
            preserved_tags_by_filename[eagle_name_no_ext] = tags

    if item_ids_to_trash:
        print("Trashing items with IDs:", item_ids_to_trash)
    else:
        print("No matching items found to trash.")
        return
    

    try:
        move_resp = requests.post(EAGLE_API_MOVE_TO_TRASH, json={"itemIds": item_ids_to_trash})
        move_resp.raise_for_status()
        print(f"Successfully moved {len(item_ids_to_trash)} items to Trash.")
    except requests.RequestException as e:
        print(f"Error moving items to trash: {e}")

def upload_new_images(render_data, folder_ids):
    expected_type = os.path.basename(os.path.dirname(JSON_FILE_PATH)).lower()
    folder_id = folder_ids.get(expected_type)

    if not folder_id:
        print(f"No folder ID found for '{expected_type}' — aborting upload.")
        return

    # Doesn't work: switch Eagle UI to correct folder
    #try:
    #    requests.post(EAGLE_API_FOCUS, json={"folderId": folder_id})
        #print(f"Focused Eagle UI on folder '{expected_type}'")
    #except requests.RequestException as e:
    #    print(f"Warning: Couldn't switch Eagle folder to {expected_type}: {e}")

    for image_name, data in render_data.items():
        file_type = data.get("file_type", "").lower()
        if file_type != expected_type:
            print(f"Skipping {image_name}: file_type '{file_type}' does not match expected type '{expected_type}'")
            continue

        img_path = data.get("imglink", "")
        if not img_path or not os.path.exists(img_path):
            print(f"Image not found: {img_path}, skipping...")
            continue

        malink = data.get("malink", "Unknown")
        poly_count = data.get("poly_count", "Unknown")
        bounding_box = data.get("bounding_box", [])
        rig_used = data.get("rig_used", [])

        dynamic_tags = [v for k, v in data.items() if k.lower().startswith("tag")]
        name_no_ext = os.path.splitext(os.path.basename(img_path))[0].lower()
        old_tags = preserved_tags_by_filename.get(name_no_ext, [])
        combined_tags = list(set(dynamic_tags + old_tags))

        note = f"malink: {malink}\n\npoly_count: {poly_count}\n\nbounding_box: {bounding_box}\n\nrig_used: {rig_used}"

        payload = {
            "path": img_path,
            "name": os.path.basename(img_path),
            "tags": combined_tags,
            "annotation": note,
            "folderId": folder_id
        }

        try:
            response = requests.post(EAGLE_API_ADD_FROM_PATH, json=payload)
            if response.status_code == 200:
                print(f"Uploaded: {img_path}")
            else:
                print(f"Failed to upload {img_path}: {response.text}")
        except requests.RequestException as e:
            print(f"Error uploading {img_path}: {e}")

def main():
    global preserved_tags_by_filename
    preserved_tags_by_filename = {}

    try:
        with open(JSON_FILE_PATH, "r") as f:
            render_data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return

    print("JSON loaded from:", JSON_FILE_PATH)
    for name, data in render_data.items():
        print("To Upload ->", name)

    delete_existing_images(render_data)
    upload_new_images(render_data, FOLDER_IDS)
    print("All done!")

if __name__ == "__main__":
    main()
