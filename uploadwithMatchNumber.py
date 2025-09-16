# # uploadwithMatchNumber.py
# import os
# import csv
# import time
# import re
# from datetime import datetime
# from dotenv import load_dotenv
# from notion_client import Client
# from dateutil import parser as date_parser  # pip install python-dateutil

# # -------------------------
# # Load variables
# # -------------------------
# load_dotenv("variable.env")   # your file name
# NOTION_TOKEN = os.getenv("NOTION_TOKEN")
# SPORTS_DB_ID = os.getenv("SPORTS_DB_ID")
# LEAGUES_DB_ID = os.getenv("LEAGUES_DB_ID")
# SEASONS_DB_ID = os.getenv("SEASONS_DB_ID")
# TEAMS_DB_ID = os.getenv("TEAMS_DB_ID")
# MATCHES_DB_ID = os.getenv("MATCHES_DB_ID")

# if not NOTION_TOKEN:
#     raise SystemExit("❌ NOTION_TOKEN missing in variable.env")

# if not all([SPORTS_DB_ID, LEAGUES_DB_ID, SEASONS_DB_ID, TEAMS_DB_ID, MATCHES_DB_ID]):
#     raise SystemExit("❌ One or more DB IDs missing in variable.env")

# notion = Client(auth=NOTION_TOKEN)

# # -------------------------
# # Caches
# # -------------------------
# db_schema_cache = {}    # db_id -> properties schema dict
# created_cache = {       # simple caches to reduce queries
#     "sport": {},
#     "league": {},
#     "season": {},
#     "team": {}
# }

# # -------------------------
# # Helpers: DB schema & property builder
# # -------------------------
# def get_db_schema(db_id):
#     """Retrieve and cache database schema (properties)."""
#     if db_id in db_schema_cache:
#         return db_schema_cache[db_id]
#     resp = notion.databases.retrieve(database_id=db_id)
#     props = resp.get("properties", {})
#     db_schema_cache[db_id] = props
#     return props

# def build_property_value(db_id, prop_name, value):
#     """
#     Given a DB id, property name and python value, build the Notion property payload
#     according to the property's type. Return None if property doesn't exist or value empty.
#     """
#     if not value and value != 0:  # empty (None or "")
#         return None
#     schema = get_db_schema(db_id)
#     prop = schema.get(prop_name)
#     if not prop:
#         return None
#     ptype = prop.get("type")

#     try:
#         if ptype == "title":
#             return {prop_name: {"title": [{"text": {"content": str(value)}}]}}
#         if ptype == "rich_text":
#             return {prop_name: {"rich_text": [{"text": {"content": str(value)}}]}}
#         if ptype == "number":
#             # attempt integer conversion, fallback to float
#             if isinstance(value, (int, float)):
#                 return {prop_name: {"number": value}}
#             v = str(value).strip()
#             if v == "":
#                 return None
#             if "." in v:
#                 return {prop_name: {"number": float(v)}}
#             return {prop_name: {"number": int(v)}}
#         if ptype == "select":
#             return {prop_name: {"select": {"name": str(value)}}}
#         if ptype == "multi_select":
#             # value can be comma-separated string or list
#             if isinstance(value, str):
#                 items = [s.strip() for s in value.split(",") if s.strip()]
#             elif isinstance(value, (list, tuple)):
#                 items = value
#             else:
#                 items = [str(value)]
#             return {prop_name: {"multi_select": [{"name": it} for it in items]}}
#         if ptype == "date":
#             # value should be an ISO datetime string or datetime
#             if isinstance(value, datetime):
#                 iso = value.isoformat()
#             else:
#                 iso = str(value)
#             return {prop_name: {"date": {"start": iso}}}
#         if ptype == "relation":
#             # value expected to be a single page id or list of ids
#             if isinstance(value, (list, tuple)):
#                 rels = [{"id": v} for v in value if v]
#             else:
#                 rels = [{"id": value}]
#             return {prop_name: {"relation": rels}}
#         if ptype == "people":
#             # skip: not used in our flows
#             return None
#         if ptype == "checkbox":
#             return {prop_name: {"checkbox": bool(value)}}
#         if ptype == "url":
#             return {prop_name: {"url": str(value)}}
#         if ptype == "files":
#             # skip files/uploads in this script
#             return None
#     except Exception as e:
#         print(f"❌ build_property_value error for {prop_name}: {e}")
#         return None

#     return None

# # -------------------------
# # Helpers: find or create by Name (title)
# # -------------------------
# def find_by_name(database_id, name):
#     """Return page id if a page with Title == name exists, else None."""
#     if not name:
#         return None
#     try:
#         res = notion.databases.query(
#             database_id=database_id,
#             filter={"property": "Name", "title": {"equals": name}},
#             page_size=1
#         )
#         results = res.get("results", [])
#         if results:
#             return results[0]["id"]
#     except Exception as e:
#         print(f"❌ find_by_name error ({database_id}, {name}): {e}")
#     return None

# def create_item(database_id, name, extra_relations=None):
#     """
#     Create an item (page) in database with Name title and optional extra_relations dict
#     mapping property_name -> value (id or text) — only applied if property exists in DB.
#     """
#     props = {}
#     # Title
#     title_prop = build_property_value(database_id, "Name", name)
#     if title_prop:
#         props.update(title_prop)
#     # Extra relations/props
#     if extra_relations:
#         for prop_name, val in extra_relations.items():
#             built = build_property_value(database_id, prop_name, val)
#             if built:
#                 props.update(built)
#     if not props:
#         # nothing to create
#         try:
#             new_page = notion.pages.create(parent={"database_id": database_id}, properties={"Name": {"title":[{"text":{"content": name}}]}})
#             return new_page["id"]
#         except Exception as e:
#             print(f"❌ create_item fallback failed for {name}: {e}")
#             return None
#     try:
#         new_page = notion.pages.create(parent={"database_id": database_id}, properties=props)
#         return new_page["id"]
#     except Exception as e:
#         print(f"❌ create_item error for {name}: {e}")
#         return None

# def get_or_create(database_id, name, cache_key=None, extra_relations=None):
#     """Generic get_or_create with caching per type (cache_key in created_cache)."""
#     if not name:
#         return None
#     cache = created_cache.get(cache_key, {}) if cache_key else None
#     if cache is not None and name in cache:
#         return cache[name]
#     # find
#     pid = find_by_name(database_id, name)
#     if pid:
#         if cache is not None:
#             cache[name] = pid
#             created_cache[cache_key] = cache
#         return pid
#     # create (only include extra_relations which exist in db schema)
#     if extra_relations:
#         # filter only properties that exist in DB
#         schema = get_db_schema(database_id)
#         safe_extra = {}
#         for k, v in extra_relations.items():
#             if k in schema:
#                 safe_extra[k] = v
#         pid = create_item(database_id, name, safe_extra)
#     else:
#         pid = create_item(database_id, name, None)
#     if pid and cache is not None:
#         cache[name] = pid
#         created_cache[cache_key] = cache
#     return pid

# # -------------------------
# # Duplicate check
# # -------------------------
# def match_exists(date_iso, home_id=None, away_id=None, match_name=None):
#     """
#     Check match existence by combination:
#       - If home_id & away_id provided: match Date + Home relation contains id + Away relation contains id
#       - Else: check Date + Name title equals match_name
#     """
#     filters = []
#     filters.append({"property": "Date", "date": {"equals": date_iso}})
#     if home_id and away_id:
#         filters.append({"property": "Home team", "relation": {"contains": home_id}})
#         filters.append({"property": "Away team", "relation": {"contains": away_id}})
#         query_filter = {"and": filters}
#     else:
#         if match_name:
#             filters.append({"property": "Name", "title": {"equals": match_name}})
#             query_filter = {"and": filters}
#         else:
#             # only date -> treat as exists to avoid duplicates
#             query_filter = {"property": "Date", "date": {"equals": date_iso}}
#     try:
#         res = notion.databases.query(database_id=MATCHES_DB_ID, filter=query_filter, page_size=1)
#         return len(res.get("results", [])) > 0
#     except Exception as e:
#         # if the DB doesn't have Home/Away relation property names exactly, the query may fail.
#         # fallback: query by date only
#         print(f"⚠️ match_exists query error: {e} — falling back to date-only check")
#         try:
#             res = notion.databases.query(database_id=MATCHES_DB_ID, filter={"property": "Date", "date": {"equals": date_iso}}, page_size=1)
#             return len(res.get("results", [])) > 0
#         except Exception as e2:
#             print(f"❌ match_exists fallback error: {e2}")
#             return False

# # -------------------------
# # Date parsing helper
# # -------------------------
# def parse_date_str(date_str, default_year=None):
#     if not date_str or str(date_str).strip() == "":
#         return None
#     s = str(date_str).strip()
#     # If it looks like "14 December 01:45 PM" (no year), append default_year or current year
#     if re.match(r'^\d{1,2}\s+[A-Za-z]+\s+\d{1,2}:\d{2}\s*(AM|PM|am|pm)$', s):
#         year = default_year or datetime.now().year
#         s = f"{s} {year}"
#         try:
#             return datetime.strptime(s, "%d %B %I:%M %p %Y")
#         except Exception:
#             pass
#     # try ISO first
#     try:
#         return datetime.fromisoformat(s)
#     except Exception:
#         pass
#     # try common explicit format
#     try:
#         return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
#     except Exception:
#         pass
#     # try flexible dateutil
#     try:
#         return date_parser.parse(s, default=datetime(datetime.now().year, 1, 1))
#     except Exception:
#         return None

# # -------------------------
# # Main import
# # -------------------------
# def import_matches(csv_path):
#     print("Starting import:", csv_path)
#     # ensure schema caches are loaded for all DBs used
#     for db in [MATCHES_DB_ID, TEAMS_DB_ID, LEAGUES_DB_ID, SPORTS_DB_ID, SEASONS_DB_ID]:
#         try:
#             get_db_schema(db)
#         except Exception as e:
#             print(f"❌ Could not retrieve schema for DB {db}: {e}")
#             return

#     created = 0
#     skipped = 0
#     with open(csv_path, newline='', encoding='utf-8') as f:
#         reader = csv.DictReader(f)
#         for idx, raw_row in enumerate(reader, start=1):
#             try:
#                 # normalize CSV keys (strip)
#                 row = {k.strip(): (v if v is not None else "") for k, v in raw_row.items()}

#                 # Required fields from your CSV header
#                 date_in = (row.get("date") or "").strip()
#                 name_in = (row.get("name") or "").strip()
#                 sport_in = (row.get("sport") or "").strip()
#                 league_in = (row.get("league") or "").strip()
#                 season_in = (row.get("season") or "").strip()
#                 home_in = (row.get("home team") or "").strip()
#                 away_in = (row.get("away team") or "").strip()
#                 match_type_in = (row.get("match type") or "").strip()
#                 home_score_in = (row.get("home score") or "").strip()
#                 away_score_in = (row.get("away score") or "").strip()
#                 result_in = (row.get("result") or "").strip()
#                 prediction_in = (row.get("prediction") or "").strip()

#                 # Parse date -> datetime
#                 dt = parse_date_str(date_in) if date_in else None
#                 if dt:
#                     date_iso = dt.isoformat()
#                 else:
#                     date_iso = None

#                 # Create / get related items (sport -> league -> season -> teams)
#                 sport_id = get_or_create(SPORTS_DB_ID, sport_in, cache_key="sport") if sport_in else None
#                 league_id = get_or_create(LEAGUES_DB_ID, league_in, cache_key="league", extra_relations={"Sport": sport_id} if sport_id else None) if league_in else None
#                 season_id = get_or_create(SEASONS_DB_ID, season_in, cache_key="season", extra_relations={"League": league_id} if league_id else None) if season_in else None

#                 home_id = get_or_create(TEAMS_DB_ID, home_in, cache_key="team", extra_relations={"League": league_id, "Sport": sport_id} if (league_id or sport_id) else None) if home_in else None
#                 away_id = get_or_create(TEAMS_DB_ID, away_in, cache_key="team", extra_relations={"League": league_id, "Sport": sport_id} if (league_id or sport_id) else None) if away_in else None

#                 # Duplicate detection (prefer date+home+away). If teams not present, fallback to date+name
#                 is_dup = False
#                 if date_iso and home_id and away_id:
#                     is_dup = match_exists(date_iso, home_id=home_id, away_id=away_id)
#                 elif date_iso and name_in:
#                     is_dup = match_exists(date_iso, home_id=None, away_id=None, match_name=name_in)

#                 if is_dup:
#                     print(f"⚠️ Skipped duplicate: row {idx} -> {name_in} [{date_iso}]")
#                     skipped += 1
#                     continue

#                 # Build properties for Matches DB using schema-aware builder
#                 props = {}
#                 # Title / Name
#                 p = build_property_value(MATCHES_DB_ID, "Name", name_in)
#                 if p: props.update(p)
#                 # Date
#                 if date_iso:
#                     p = build_property_value(MATCHES_DB_ID, "Date", date_iso)
#                     if p: props.update(p)
#                 # Relations (Sport, League, Season, Home team, Away team)
#                 if sport_id:
#                     p = build_property_value(MATCHES_DB_ID, "Sport", sport_id)
#                     if p: props.update(p)
#                 if league_id:
#                     p = build_property_value(MATCHES_DB_ID, "League", league_id)
#                     if p: props.update(p)
#                 if season_id:
#                     p = build_property_value(MATCHES_DB_ID, "Season", season_id)
#                     if p: props.update(p)
#                 if home_id:
#                     p = build_property_value(MATCHES_DB_ID, "Home team", home_id)
#                     if p: props.update(p)
#                 if away_id:
#                     p = build_property_value(MATCHES_DB_ID, "Away team", away_id)
#                     if p: props.update(p)
#                 # Match Type (select)
#                 if match_type_in:
#                     p = build_property_value(MATCHES_DB_ID, "Match Type", match_type_in)
#                     if p: props.update(p)
#                 # Scores
#                 if home_score_in and home_score_in.strip().isdigit():
#                     p = build_property_value(MATCHES_DB_ID, "Home score", int(home_score_in.strip()))
#                     if p: props.update(p)
#                 if away_score_in and away_score_in.strip().isdigit():
#                     p = build_property_value(MATCHES_DB_ID, "Away score", int(away_score_in.strip()))
#                     if p: props.update(p)
#                 # Result and Prediction
#                 if result_in:
#                     p = build_property_value(MATCHES_DB_ID, "Result", result_in)
#                     if p: props.update(p)
#                 if prediction_in:
#                     p = build_property_value(MATCHES_DB_ID, "Prediction", prediction_in)
#                     if p: props.update(p)
#                 # Optionally set match number (row index)
#                 if "Match Number" in get_db_schema(MATCHES_DB_ID):
#                     # decide type: if number -> set number, else set as text
#                     mprop = get_db_schema(MATCHES_DB_ID)["Match Number"]["type"]
#                     if mprop == "number":
#                         props.update(build_property_value(MATCHES_DB_ID, "Match Number", idx))
#                     else:
#                         props.update(build_property_value(MATCHES_DB_ID, "Match Number", f"Match {idx}"))

#                 # Final create: ensure props is not empty
#                 if not props:
#                     print(f"⚠️ Nothing to set for row {idx}, skipping.")
#                     skipped += 1
#                     continue

#                 # Create the page
#                 notion.pages.create(parent={"database_id": MATCHES_DB_ID}, properties=props)
#                 created += 1
#                 print(f"✅ Imported row {idx}: {name_in} [{date_iso}]")

#                 # be polite to the API
#                 time.sleep(0.3)

#             except Exception as e:
#                 print(f"❌ Error importing row {idx}: {e}")

#     print(f"\nDone. Created: {created}, Skipped: {skipped}")

# # -------------------------
# # Run
# # -------------------------
# if __name__ == "__main__":
#     import_matches("matches.csv")

import os
import csv
import time
import re
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from dateutil import parser as date_parser  # pip install python-dateutil

# -------------------------
# Load variables
# -------------------------
load_dotenv("variable.env")   # your file name
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
SPORTS_DB_ID = os.getenv("SPORTS_DB_ID")
LEAGUES_DB_ID = os.getenv("LEAGUES_DB_ID")
SEASONS_DB_ID = os.getenv("SEASONS_DB_ID")
TEAMS_DB_ID = os.getenv("TEAMS_DB_ID")
MATCHES_DB_ID = os.getenv("MATCHES_DB_ID")

if not NOTION_TOKEN:
    raise SystemExit("❌ NOTION_TOKEN missing in variable.env")

if not all([SPORTS_DB_ID, LEAGUES_DB_ID, SEASONS_DB_ID, TEAMS_DB_ID, MATCHES_DB_ID]):
    raise SystemExit("❌ One or more DB IDs missing in variable.env")

notion = Client(auth=NOTION_TOKEN)

# -------------------------
# Caches
# -------------------------
db_schema_cache = {}    # db_id -> properties schema dict
created_cache = {       # simple caches to reduce queries
    "sport": {},
    "league": {},
    "season": {},
    "team": {}
}

# -------------------------
# Helpers: DB schema & property builder
# -------------------------
def get_db_schema(db_id):
    """Retrieve and cache database schema (properties)."""
    if db_id in db_schema_cache:
        return db_schema_cache[db_id]
    resp = notion.databases.retrieve(database_id=db_id)
    props = resp.get("properties", {})
    db_schema_cache[db_id] = props
    return props

def build_property_value(db_id, prop_name, value):
    """
    Given a DB id, property name and python value, build the Notion property payload
    according to the property's type. Return None if property doesn't exist or value empty.
    """
    if not value and value != 0:  # empty (None or "")
        return None
    schema = get_db_schema(db_id)
    prop = schema.get(prop_name)
    if not prop:
        return None
    ptype = prop.get("type")

    try:
        if ptype == "title":
            return {prop_name: {"title": [{"text": {"content": str(value)}}]}}
        if ptype == "rich_text":
            return {prop_name: {"rich_text": [{"text": {"content": str(value)}}]}}
        if ptype == "number":
            # attempt integer conversion, fallback to float
            if isinstance(value, (int, float)):
                return {prop_name: {"number": value}}
            v = str(value).strip()
            if v == "":
                return None
            if "." in v:
                return {prop_name: {"number": float(v)}}
            return {prop_name: {"number": int(v)}}
        if ptype == "select":
            return {prop_name: {"select": {"name": str(value)}}}
        if ptype == "multi_select":
            # value can be comma-separated string or list
            if isinstance(value, str):
                items = [s.strip() for s in value.split(",") if s.strip()]
            elif isinstance(value, (list, tuple)):
                items = value
            else:
                items = [str(value)]
            return {prop_name: {"multi_select": [{"name": it} for it in items]}}
        if ptype == "date":
            # value should be an ISO datetime string or datetime
            if isinstance(value, datetime):
                iso = value.isoformat()
            else:
                iso = str(value)
            return {prop_name: {"date": {"start": iso}}}
        if ptype == "relation":
            # value expected to be a single page id or list of ids
            if isinstance(value, (list, tuple)):
                rels = [{"id": v} for v in value if v]
            else:
                rels = [{"id": value}]
            return {prop_name: {"relation": rels}}
        if ptype == "people":
            # skip: not used in our flows
            return None
        if ptype == "checkbox":
            return {prop_name: {"checkbox": bool(value)}}
        if ptype == "url":
            return {prop_name: {"url": str(value)}}
        if ptype == "files":
            # skip files/uploads in this script
            return None
    except Exception as e:
        print(f"❌ build_property_value error for {prop_name}: {e}")
        return None

    return None

# -------------------------
# Helpers: find or create by Name (title)
# -------------------------
def find_by_name(database_id, name):
    """Return page id if a page with Title == name exists, else None."""
    if not name:
        return None
    try:
        res = notion.databases.query(
            database_id=database_id,
            filter={"property": "Name", "title": {"equals": name}},
            page_size=1
        )
        results = res.get("results", [])
        if results:
            return results[0]["id"]
    except Exception as e:
        print(f"❌ find_by_name error ({database_id}, {name}): {e}")
    return None

def create_item(database_id, name, extra_relations=None):
    """
    Create an item (page) in database with Name title and optional extra_relations dict
    mapping property_name -> value (id or text) — only applied if property exists in DB.
    """
    props = {}
    # Title
    title_prop = build_property_value(database_id, "Name", name)
    if title_prop:
        props.update(title_prop)
    # Extra relations/props
    if extra_relations:
        for prop_name, val in extra_relations.items():
            built = build_property_value(database_id, prop_name, val)
            if built:
                props.update(built)
    if not props:
        # nothing to create
        try:
            new_page = notion.pages.create(parent={"database_id": database_id}, properties={"Name": {"title":[{"text":{"content": name}}]}})
            return new_page["id"]
        except Exception as e:
            print(f"❌ create_item fallback failed for {name}: {e}")
            return None
    try:
        new_page = notion.pages.create(parent={"database_id": database_id}, properties=props)
        return new_page["id"]
    except Exception as e:
        print(f"❌ create_item error for {name}: {e}")
        return None

def get_or_create(database_id, name, cache_key=None, extra_relations=None):
    """Generic get_or_create with caching per type (cache_key in created_cache)."""
    if not name:
        return None
    cache = created_cache.get(cache_key, {}) if cache_key else None
    if cache is not None and name in cache:
        return cache[name]
    # find
    pid = find_by_name(database_id, name)
    if pid:
        if cache is not None:
            cache[name] = pid
            created_cache[cache_key] = cache
        return pid
    # create (only include extra_relations which exist in db schema)
    if extra_relations:
        # filter only properties that exist in DB
        schema = get_db_schema(database_id)
        safe_extra = {}
        for k, v in extra_relations.items():
            if k in schema:
                safe_extra[k] = v
        pid = create_item(database_id, name, safe_extra)
    else:
        pid = create_item(database_id, name, None)
    if pid and cache is not None:
        cache[name] = pid
        created_cache[cache_key] = cache
    return pid

# -------------------------
# Duplicate check
# -------------------------
def match_exists(date_iso, home_id=None, away_id=None, match_name=None):
    """
    Check match existence by combination:
      - If home_id & away_id provided: match Date + Home relation contains id + Away relation contains id
      - Else: check Date + Name title equals match_name
    """
    filters = []
    filters.append({"property": "Date", "date": {"equals": date_iso}})
    if home_id and away_id:
        filters.append({"property": "Home team", "relation": {"contains": home_id}})
        filters.append({"property": "Away team", "relation": {"contains": away_id}})
        query_filter = {"and": filters}
    else:
        if match_name:
            filters.append({"property": "Name", "title": {"equals": match_name}})
            query_filter = {"and": filters}
        else:
            # only date -> treat as exists to avoid duplicates
            query_filter = {"property": "Date", "date": {"equals": date_iso}}
    try:
        res = notion.databases.query(database_id=MATCHES_DB_ID, filter=query_filter, page_size=1)
        return len(res.get("results", [])) > 0
    except Exception as e:
        # if the DB doesn't have Home/Away relation property names exactly, the query may fail.
        # fallback: query by date only
        print(f"⚠️ match_exists query error: {e} — falling back to date-only check")
        try:
            res = notion.databases.query(database_id=MATCHES_DB_ID, filter={"property": "Date", "date": {"equals": date_iso}}, page_size=1)
            return len(res.get("results", [])) > 0
        except Exception as e2:
            print(f"❌ match_exists fallback error: {e2}")
            return False

# -------------------------
# Date parsing helper
# -------------------------
def parse_date_str(date_str, default_year=None):
    if not date_str or str(date_str).strip() == "":
        return None
    s = str(date_str).strip()
    # If it looks like "14 December 01:45 PM" (no year), append default_year or current year
    if re.match(r'^\d{1,2}\s+[A-Za-z]+\s+\d{1,2}:\d{2}\s*(AM|PM|am|pm)$', s):
        year = default_year or datetime.now().year
        s = f"{s} {year}"
        try:
            return datetime.strptime(s, "%d %B %I:%M %p %Y")
        except Exception:
            pass
    # try ISO first
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    # try common explicit format
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    # try flexible dateutil
    try:
        return date_parser.parse(s, default=datetime(datetime.now().year, 1, 1))
    except Exception:
        return None

# -------------------------
# Main import
# -------------------------
def import_matches(csv_path):
    print("Starting import:", csv_path)
    # ensure schema caches are loaded for all DBs used
    for db in [MATCHES_DB_ID, TEAMS_DB_ID, LEAGUES_DB_ID, SPORTS_DB_ID, SEASONS_DB_ID]:
        try:
            get_db_schema(db)
        except Exception as e:
            print(f"❌ Could not retrieve schema for DB {db}: {e}")
            return

    created = 0
    skipped = 0
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, raw_row in enumerate(reader, start=1):
            try:
                # normalize CSV keys (strip)
                row = {k.strip(): (v if v is not None else "") for k, v in raw_row.items()}

                # Required fields from your CSV header
                date_in = (row.get("date") or "").strip()
                name_in = (row.get("name") or "").strip()
                sport_in = (row.get("sport") or "").strip()
                league_in = (row.get("league") or "").strip()
                season_in = (row.get("season") or "").strip()
                home_in = (row.get("home team") or "").strip()
                away_in = (row.get("away team") or "").strip()
                match_type_in = (row.get("match type") or "").strip()
                home_score_in = (row.get("home score") or "").strip()
                away_score_in = (row.get("away score") or "").strip()
                result_in = (row.get("result") or "").strip()
                prediction_in = (row.get("prediction") or "").strip()
                conductor_numeral_in = (row.get("conductor numeral") or "").strip()

                # Parse date -> datetime
                dt = parse_date_str(date_in) if date_in else None
                if dt:
                    date_iso = dt.isoformat()
                else:
                    date_iso = None

                # Create / get related items (sport -> league -> season -> teams)
                sport_id = get_or_create(SPORTS_DB_ID, sport_in, cache_key="sport") if sport_in else None
                league_id = get_or_create(LEAGUES_DB_ID, league_in, cache_key="league", extra_relations={"Sport": sport_id} if sport_id else None) if league_in else None
                season_id = get_or_create(SEASONS_DB_ID, season_in, cache_key="season", extra_relations={"League": league_id} if league_id else None) if season_in else None

                home_id = get_or_create(TEAMS_DB_ID, home_in, cache_key="team", extra_relations={"League": league_id, "Sport": sport_id} if (league_id or sport_id) else None) if home_in else None
                away_id = get_or_create(TEAMS_DB_ID, away_in, cache_key="team", extra_relations={"League": league_id, "Sport": sport_id} if (league_id or sport_id) else None) if away_in else None

                # Duplicate detection (prefer date+home+away). If teams not present, fallback to date+name
                is_dup = False
                if date_iso and home_id and away_id:
                    is_dup = match_exists(date_iso, home_id=home_id, away_id=away_id)
                elif date_iso and name_in:
                    is_dup = match_exists(date_iso, home_id=None, away_id=None, match_name=name_in)

                if is_dup:
                    print(f"⚠️ Skipped duplicate: row {idx} -> {name_in} [{date_iso}]")
                    skipped += 1
                    continue

                # Build properties for Matches DB using schema-aware builder
                props = {}
                # Title / Name
                p = build_property_value(MATCHES_DB_ID, "Name", name_in)
                if p: props.update(p)
                # Date
                if date_iso:
                    p = build_property_value(MATCHES_DB_ID, "Date", date_iso)
                    if p: props.update(p)
                # Relations (Sport, League, Season, Home team, Away team)
                if sport_id:
                    p = build_property_value(MATCHES_DB_ID, "Sport", sport_id)
                    if p: props.update(p)
                if league_id:
                    p = build_property_value(MATCHES_DB_ID, "League", league_id)
                    if p: props.update(p)
                if season_id:
                    p = build_property_value(MATCHES_DB_ID, "Season", season_id)
                    if p: props.update(p)
                if home_id:
                    p = build_property_value(MATCHES_DB_ID, "Home team", home_id)
                    if p: props.update(p)
                if away_id:
                    p = build_property_value(MATCHES_DB_ID, "Away team", away_id)
                    if p: props.update(p)
                # Match Type (select)
                if match_type_in:
                    p = build_property_value(MATCHES_DB_ID, "Match Type", match_type_in)
                    if p: props.update(p)
                # Scores
                if home_score_in and home_score_in.strip().isdigit():
                    p = build_property_value(MATCHES_DB_ID, "Home score", int(home_score_in.strip()))
                    if p: props.update(p)
                if away_score_in and away_score_in.strip().isdigit():
                    p = build_property_value(MATCHES_DB_ID, "Away score", int(away_score_in.strip()))
                    if p: props.update(p)
                # Result and Prediction
                if result_in:
                    p = build_property_value(MATCHES_DB_ID, "Result", result_in)
                    if p: props.update(p)
                if prediction_in:
                    p = build_property_value(MATCHES_DB_ID, "Prediction", prediction_in)
                    if p: props.update(p)
                # Optionally set match number (row index)
                if "Match Number" in get_db_schema(MATCHES_DB_ID):
                    # decide type: if number -> set number, else set as text
                    mprop = get_db_schema(MATCHES_DB_ID)["Match Number"]["type"]
                    if mprop == "number":
                        props.update(build_property_value(MATCHES_DB_ID, "Match Number", idx))
                    else:
                        props.update(build_property_value(MATCHES_DB_ID, "Match Number", f"Match {idx}"))
                # Optionally set conductor numeral
                if "Conductor Numeral" in get_db_schema(MATCHES_DB_ID) and conductor_numeral_in and conductor_numeral_in.strip().isdigit():
                    p = build_property_value(MATCHES_DB_ID, "Conductor Numeral", int(conductor_numeral_in.strip()))
                    if p: props.update(p)

                # Final create: ensure props is not empty
                if not props:
                    print(f"⚠️ Nothing to set for row {idx}, skipping.")
                    skipped += 1
                    continue

                # Create the page
                notion.pages.create(parent={"database_id": MATCHES_DB_ID}, properties=props)
                created += 1
                print(f"✅ Imported row {idx}: {name_in} [{date_iso}]")

                # be polite to the API
                time.sleep(0.3)

            except Exception as e:
                print(f"❌ Error importing row {idx}: {e}")

    print(f"\nDone. Created: {created}, Skipped: {skipped}")

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    import_matches("matches.csv")