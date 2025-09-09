# backend/tools/gs_sanity_check.py
import os, re, gspread
from dotenv import load_dotenv

# Load env from backend/.env
load_dotenv(dotenv_path="backend/.env")

sheet_url = os.getenv("SHEET_URL", "")
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

assert sheet_url, "SHEET_URL missing in backend/.env"
m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
assert m, f"Bad SHEET_URL format: {sheet_url}"

assert cred_path and os.path.exists(cred_path), f"Missing/bad GOOGLE_APPLICATION_CREDENTIALS: {cred_path}"

gc = gspread.service_account(filename=cred_path)
sh = gc.open_by_key(m.group(1))
print("OK -> Worksheet:", sh.sheet1.title)
