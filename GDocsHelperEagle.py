# GDocsHelperEagle.py  (leaned)

import os
import json
import datetime
import getpass
import logging

logger = logging.getLogger(__name__)

# If you don't need impersonation, replace with your service-account only,
# or share the sheet to the SA and remove "subject=" in _get_service().
_subjects = [
    'automation@tinyco.com',
    'automation1@tinyco.com',
    'automation2@tinyco.com',
    'automation3@tinyco.com',
    'automation4@tinyco.com',
    'automation5@tinyco.com'
]
_creds = [None] * len(_subjects)

HM_EAGLE_SPREADSHEET_ID = '1mlvbDt4yGq-GYX3YwDKlFQp5h8q2MW8GxmaKejKFhLg'

# sheetId (tab name) -> [spreadsheet_id, tab_name]
sheetNameToId = {
    'Characters': [HM_EAGLE_SPREADSHEET_ID, 'Characters'],
    'Creatures':  [HM_EAGLE_SPREADSHEET_ID, 'Creatures'],
    'Effects':    [HM_EAGLE_SPREADSHEET_ID, 'Effects'],
    'Hair':       [HM_EAGLE_SPREADSHEET_ID, 'Hair'],
    'Outfits':    [HM_EAGLE_SPREADSHEET_ID, 'Outfits'],
    'Props':      [HM_EAGLE_SPREADSHEET_ID, 'Props'],
}

def _normalize_sheet_id(s):
    m = {
        'props': 'Props', 'characters': 'Characters', 'creatures': 'Creatures',
        'outfits': 'Outfits', 'hair': 'Hair', 'effects': 'Effects'
    }
    return m.get(str(s).lower(), 'Props')

def _category_from_output_dir(output_dir):
    parts = [p for p in os.path.normpath(output_dir).split(os.sep) if p]
    if 'EagleFiles' in parts:
        i = parts.index('EagleFiles')
        if i + 1 < len(parts):
            return _normalize_sheet_id(parts[i+1])
    lower = output_dir.lower()
    for k in ['props','characters','creatures','outfits','hair','effects']:
        if os.sep + k + os.sep in lower or lower.endswith(os.sep + k):
            return _normalize_sheet_id(k)
    return 'Props'

def _asset_from_scene(scene_file):
    return os.path.splitext(os.path.basename(scene_file))[0]

def _to_p4_path(local_path):
    p = local_path.replace("\\", "/")
    i = p.find("/Perforce/")
    return f"//{p[i+len('/Perforce/'):]}" if i != -1 else p

# GDocsHelperEagle.py  (_get_service)
def _get_service():
    from googleapiclient import discovery, errors as gerrors
    from google.oauth2 import service_account
    import json, os, sys

    dirpath = os.path.dirname(__file__)
    json_path = os.path.join(dirpath, "config-interface-5f3b76500711_v2.json")

    #try:
        #with open(json_path, "r") as jf:
            #svc_email = json.load(jf).get("client_email")
        #print(f"[Sheets] Using service account: {svc_email}")
    #except Exception:
    #    pass

    creds = service_account.Credentials.from_service_account_file(
        json_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    service = discovery.build("sheets", "v4", credentials=creds)
    _creds[0] = (creds, service)
    return service, None, gerrors

class GDocs(object):
    """Minimal helper to upsert rows in Google Sheets tabs by Asset/Name and merge summary stats."""

    def __init__(self):
        self.service, self.__subject, self.gerrors = _get_service()
        self.feeds = {}
        self._header_cache = {}

    # --- Sheet/meta helpers ---

    @staticmethod
    def cleaned_heading(value):
        # keep only alnum, lowercased
        return ''.join(ch for ch in str(value) if ch.isalnum()).lower()

    def getSheetInfo(self, sheetId):
        sheetId = _normalize_sheet_id(sheetId)
        return sheetNameToId.get(sheetId, sheetNameToId['Props'])

    def getFeed(self, sheetId):
        sheetId = _normalize_sheet_id(sheetId)
        if sheetId in self.feeds:
            return self.feeds[sheetId]
        s_id, tab = self.getSheetInfo(sheetId)
        result = self.service.spreadsheets().values().get(
            spreadsheetId=s_id, range=tab
        ).execute()
        feed = result.get('values', [])
        self.feeds[sheetId] = feed
        return feed

    def get_headings(self, sheet_id):
        heads, _ = self.headings_and_row_index(sheet_id)
        return heads

    def _sheet_type_value(self, sheet_id):
        """Return the singular, lowercase Type value used in the sheet."""
        t = _normalize_sheet_id(sheet_id).lower()
        return {
            'props': 'prop',
            'characters': 'character',
            'creatures': 'creature',
            'outfits': 'outfit',
            'hair': 'hair',
            'effects': 'effect',
        }.get(t, 'prop')

    def _key_index(self, sheetId):
        heads, _ = self.headings_and_row_index(sheetId)
        if "asset" in heads:
            return heads.index("asset"), "asset"
        if "name" in heads:
            return heads.index("name"), "name"
        raise RuntimeError(f"Sheet '{sheetId}' must have an 'Asset' or 'Name' column.")

    def getRow(self, sheetId, rowId):
        heads, header_idx = self.headings_and_row_index(sheetId)
        # Use 'asset' if present, else 'name'
        if "asset" in heads:
            key_idx = heads.index("asset")
        elif "name" in heads:
            key_idx = heads.index("name")
        else:
            raise RuntimeError(f"Sheet '{sheetId}' must have an 'Asset' or 'Name' column.")

        feed = self.getFeed(sheetId)
        # Search only data rows (after header)
        search_rows = feed[header_idx + 1:]

        found = None
        found_abs_idx = -1
        for i, row in enumerate(search_rows):
            if key_idx < len(row) and row[key_idx] == rowId:
                found = row
                found_abs_idx = header_idx + 1 + i
                break

        # row_number is 1-based for Sheets API
        return [found, (found_abs_idx + 1) if found is not None else -1]
    
    def headings_and_row_index(self, sheet_id):
        """
        Return (headings_list, header_row_index). Scans the first ~10 rows
        to find the row that contains 'asset' or 'name' (case/spacing-insensitive).
        """
        if sheet_id in self._header_cache:
            return self._header_cache[sheet_id]

        feed = self.getFeed(sheet_id)
        # Look at the first few rows to find the header
        for idx, row in enumerate(feed[:10]):
            heads = [self.cleaned_heading(c) for c in row]
            if "asset" in heads or "name" in heads:
                self._header_cache[sheet_id] = (heads, idx)
                return heads, idx

        # Fallback: first non-empty row (or empty)
        if feed:
            heads = [self.cleaned_heading(c) for c in feed[0]]
        else:
            heads = []
        self._header_cache[sheet_id] = (heads, 0)
        return heads, 0

    # --- Row shaping & updates ---

    def flatten_for_values(self, sheet_id, data):
        heads, _ = self.headings_and_row_index(sheet_id)
        type_cell = data.get('type', self._sheet_type_value(sheet_id))
        return [type_cell] + [data.get(h, '') for h in heads[1:]]

    def to_dict(self, sheet_id, row):
        heads = self.get_headings(sheet_id)
        return {k: v for k, v in zip(heads, row)}

    @staticmethod
    def _is_value_valid(v):
        return v not in (None, '', {}, '[]', '{}')

    def _needs_update(self, sheetId, row, data):
        if row is None:
            return True
        # fields that we always ignore when comparing
        volatile = {'date', 'dateandtime', 'blame'}
        row_dict = self.to_dict(sheetId, row)
        # Remove volatile keys from the row snapshot
        for k in volatile:
            row_dict.pop(k, None)
        # Remove volatile keys from the new payload too
        cmp_data = {k: v for k, v in data.items() if k not in volatile}
        # Keep only meaningful values
        row_set  = {k: v for k, v in row_dict.items() if self._is_value_valid(v)}
        data_set = {k: v for k, v in cmp_data.items() if self._is_value_valid(v)}
        # Update only if any meaningful key actually changed
        return any(row_set.get(k) != v for k, v in data_set.items())

    def addEntry(self, data, sheetId):
        s_id, tab = self.getSheetInfo(sheetId)
        entry = self.flatten_for_values(sheetId, data)
        self.service.spreadsheets().values().append(
            spreadsheetId=s_id,
            range=f'{tab}!A:A',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [entry]}
        ).execute()
        self.feeds.pop(_normalize_sheet_id(sheetId), None)

    def updateRow(self, row, row_number, sheetId):
        s_id, tab = self.getSheetInfo(sheetId)
        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=s_id,
            body={'valueInputOption': 'USER_ENTERED',
                  'data': [{'range': f'{tab}!A{row_number}', 'values': [row]}]}
        ).execute()
        self.feeds.pop(_normalize_sheet_id(sheetId), None)

    def doUpdateConfig(self, sheetId, data):
        # Normalize keys to cleaned headings style
        data = {self.cleaned_heading(k): v for k, v in data.items()}
        key_idx, key_name = self._key_index(sheetId)
        key_val = data.get(key_name)
        if not key_val:
            raise ValueError(f"Missing key '{key_name}' in payload.")

        try:
            row, row_num = self.getRow(sheetId, key_val)
            # Always stamp date/blame
            data['dateandtime'] = datetime.datetime.now().strftime("%I:%M%p on %m/%d/%Y")
            data['blame'] = getpass.getuser()

            if row is None:
                self.addEntry(data, sheetId)
            else:
                if not self._needs_update(sheetId, row, data):
                    return
                merged = self.to_dict(sheetId, row)
                merged.update(data)
                out_row = self.flatten_for_values(sheetId, merged)
                self.updateRow(out_row, row_num, sheetId)
        except Exception as e:
            # If googleapiclient is present, surface the HTTP status cleanly, else just log
            if hasattr(self, 'gerrors') and isinstance(e, self.gerrors.HttpError):
                logger.error(f"Sheets HttpError {e.resp.status}: {e}")
            else:
                logger.error(f"Sheets update error: {e}")
            raise

    # --- Public entry points you call from the GUI ---

    def upsert_basic(self, scene_file, output_dir):
        sheet = _category_from_output_dir(output_dir)
        asset = _asset_from_scene(scene_file)
        p4    = _to_p4_path(scene_file)
        self.doUpdateConfig(sheet, {'type': self._sheet_type_value(sheet),'asset': asset, 'path': p4})

    def apply_summary(self, output_dir, asset_name, summary_dict, crashed=None):
        sheet = _category_from_output_dir(output_dir)
        payload = {
            'asset': asset_name,
            'polycount':        summary_dict.get('polycount'),
            'numberoftextures': summary_dict.get('num_textures'),
            'numberofshaders':  summary_dict.get('num_shaders'),
            'missingtextures':  'Yes' if summary_dict.get('missing_textures') else 'No',
        }
        if crashed is not None:
            payload['crashed'] = 'Yes' if crashed else 'No'
        self.doUpdateConfig(sheet, payload)
