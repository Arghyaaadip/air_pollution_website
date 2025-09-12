import os, re, gspread
from dotenv import load_dotenv

# Load env from backend/.env (and project root .env if present)
load_dotenv("backend/.env")
load_dotenv(".env")

sheet_url = os.getenv("SHEET_URL", "")
m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", sheet_url)
assert m, f"Bad SHEET_URL: {sheet_url}"
sheet_id = m.group(1)

gc = gspread.service_account(filename=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
sh = gc.open_by_key(sheet_id)

# If your admin code expects the first tab to have headers like Title, URL, Audience, Status, Notes,
# make sure we're writing to that exact tab. If it's named “Roster”, use that by name:
ws = sh.worksheet("Roster")  # or: ws = sh.sheet1

# Append a test row
ws.append_row(
    ["TEST via API", "https://example.com", "Developers", "Draft", "Temp row"],
    value_input_option="USER_ENTERED"
)
print("Appended OK to:", ws.title)
