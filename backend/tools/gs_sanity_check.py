# backend/tools/gs_sanity_check.py
import os, re, json, gspread
from dotenv import load_dotenv

# Load env (works if .env is in backend/.env)
load_dotenv("backend/.env")
load_dotenv(".env")  # also allow a top-level .env if you keep one there

cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print("Cred path:", cred_path)
assert cred_path and os.path.exists(cred_path), "Cred path missing or file not found."

with open(cred_path, "r", encoding="utf-8") as f:
    info = json.load(f)
svc_email = info["client_email"]
print("Service account email:", svc_email)

sheet_url = os.getenv("SHEET_URL", "")
m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
assert m, f"Bad SHEET_URL: {sheet_url}"
sheet_id = m.group(1)
print("Parsed sheet ID:", sheet_id)

# Read-only open test
gc = gspread.service_account(filename=cred_path)
sh = gc.open_by_key(sheet_id)
print("Opened spreadsheet:", sh.title)
print("First worksheet:", sh.sheet1.title)
