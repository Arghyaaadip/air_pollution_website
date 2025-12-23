# backend/admin/__init__.py
import os, os.path, functools, re
import gspread
from google.auth import default
from gspread import utils as gutils
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash


admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")

MANAGE_LIMIT = 50  # max rows to show in manage table

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = (os.getenv("ADMIN_PASSWORD_HASH") or "").strip()


def check_admin_password(password: str) -> bool:
    # If the secret isn't attached / env var missing, deny login
    if not ADMIN_PASSWORD_HASH:
        return False
    try:
        return check_password_hash(ADMIN_PASSWORD_HASH, password or "")
    except Exception:
        return False


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            flash("Please log in as admin.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


# ---------------- Auth routes ---------------
@admin_bp.get("/login")
def login():
    return render_template("admin/login.html")


@admin_bp.post("/login")
def login_submit():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if username == ADMIN_USERNAME and check_admin_password(password):
        session["admin"] = True  # boolean flag
        flash("Welcome, Margaret!", "success")
        return redirect(url_for("admin.dashboard"))

    flash("Invalid username or password.", "danger")
    return redirect(url_for("admin.login"))


@admin_bp.get("/logout")
def logout():
    session.pop("admin", None)
    flash("Logged out.", "info")
    return redirect(url_for("home"))


# ---------------- Google Sheets helpers ---------------
def _open_ws_and_headers():
    """
    Return (worksheet, header_list) or (None, None) if sheets not configured.
    Uses Cloud Run runtime service account via google.auth.default().
    """
    sheet_url = os.getenv("SHEET_URL", "")
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not m:
        return None, None

    try:
        creds, _ = default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(m.group(1))
        ws = sh.sheet1
        headers = ws.row_values(1)
        return ws, headers
    except Exception as e:
        print(f"[ERROR] Sheets auth/open failed: {e}")
        return None, None



def _read_rows_for_manage(ws, headers, limit=MANAGE_LIMIT):
    """
    Return a list of dicts for the first N data rows:
      { 'sheet_row': int,  header1: val1, header2: val2, ... }
    """
    if not ws or not headers:
        return []

    records = ws.get_all_records()  # list[dict] for all data rows (starting row 2)
    out = []
    for idx, rec in enumerate(records[:limit]):
        rec_copy = dict(rec)
        rec_copy["sheet_row"] = 2 + idx  # actual row number in the sheet
        out.append(rec_copy)
    return out


# ---------------- Dashboard ----------------
@admin_bp.get("/")
@login_required
def dashboard():
    ws, headers = _open_ws_and_headers()
    preview = []
    manage_rows = []

    if ws and headers:
        all_rows = ws.get_all_records()
        preview = all_rows[:5]
        manage_rows = _read_rows_for_manage(ws, headers, MANAGE_LIMIT)

    return render_template(
        "admin/dashboard.html",
        headers=headers or [],
        preview=preview,
        manage_rows=manage_rows,
    )


# ---------------- Add row (all fields optional) ----------------
@admin_bp.post("/add")
@login_required
def add_row():
    title            = (request.form.get("title") or "").strip()
    url              = (request.form.get("url") or "").strip()
    target_audience  = (request.form.get("target_audience") or "").strip()
    authors          = (request.form.get("authors") or "").strip()
    publisher        = (request.form.get("publisher") or "").strip()
    date_published   = (request.form.get("date_published") or "").strip()
    resource_theme   = (request.form.get("resource_theme") or "").strip()
    resource_type    = (request.form.get("resource_type") or "").strip()
    keywords         = (request.form.get("keywords") or "").strip()
    language         = (request.form.get("language") or "").strip()
    status           = (request.form.get("status") or "").strip()
    notes            = (request.form.get("notes") or "").strip()

    ws, headers = _open_ws_and_headers()
    if not (ws and headers):
        flash("Google Sheets not configured (check SHEET_URL and GOOGLE_APPLICATION_CREDENTIALS).", "danger")
        return redirect(url_for("admin.dashboard"))

    values_map = {
        "Title":                         title,
        "URL":                           url,
        "Target Audience":               target_audience,
        "Author(s)":                     authors,
        "Publisher":                     publisher,
        "Date Pub":                      date_published,
        "Date Published":                date_published,
        "Resource Theme":                resource_theme,
        "Date Pub Resource Theme":       resource_theme,
        "Resource Type":                 resource_type,
        "Keywords":                      keywords,
        "Language":                      language,
        "Status":                        status,
        "Notes":                         notes,
    }

    row = [values_map.get(h, "") for h in headers]

    try:
        ws.append_row(row, value_input_option="USER_ENTERED")
        flash("Row added to the sheet ✅", "success")
    except Exception as e:
        flash(f"Failed to add row: {e}", "danger")

    return redirect(url_for("admin.dashboard"))


# ---------------- Update row ----------------
@admin_bp.post("/update")
@login_required
def update_row():
    sheet_row = request.form.get("sheet_row", type=int)
    ws, headers = _open_ws_and_headers()
    if not (ws and headers and sheet_row and sheet_row >= 2):
        flash("Update failed (bad row or sheet).", "danger")
        return redirect(url_for("admin.dashboard"))

    updates = {}
    i = 0
    while True:
        h = request.form.get(f"header_{i}")
        if h is None:
            break
        v = request.form.get(f"field_{i}", "")
        updates[h] = v
        i += 1

    row_values = [updates.get(h, "") for h in headers]

    try:
        start_a1 = gutils.rowcol_to_a1(sheet_row, 1)
        end_a1   = gutils.rowcol_to_a1(sheet_row, len(headers))
        ws.update(f"{start_a1}:{end_a1}", [row_values])
        flash(f"Updated row {sheet_row}.", "success")
    except Exception as e:
        flash(f"Update failed: {e}", "danger")

    return redirect(url_for("admin.dashboard"))


# ---------------- Delete row ----------------
@admin_bp.route("/delete", methods=["GET", "POST"])
@login_required
def delete_row():
    sheet_row = request.values.get("sheet_row", type=int)
    ws, headers = _open_ws_and_headers()
    if not (ws and headers and sheet_row and sheet_row >= 2):
        flash("Delete failed (bad row or sheet).", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        ws.delete_rows(sheet_row)
        flash(f"Deleted row {sheet_row}.", "success")
    except Exception as e:
        flash(f"Delete failed: {e}", "danger")

    return redirect(url_for("admin.dashboard"))
