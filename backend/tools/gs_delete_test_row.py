# backend/tools/gs_delete_test_row.py
import os, re, gspread
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")

m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", os.getenv("SHEET_URL",""))
gc = gspread.service_account(filename=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
sh = gc.open_by_key(m.group(1))
ws = sh.worksheet("Roster")  # or your tab name

# find & delete the first row whose first cell == "TEST via API"
cells = ws.findall("TEST via API", in_column=1)  # column A
if cells:
    ws.delete_rows(cells[0].row)
    print(f"Deleted row {cells[0].row}")
else:
    print("Nothing to delete")
