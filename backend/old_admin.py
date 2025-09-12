import os, re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
import gspread
from dotenv import load_dotenv
import json

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")

# one-time env load in this module (safe even if app.py loads it too)
load_dotenv()

# ---- helpers ----
def _open_sheet():
    """Return (gc, sh, ws) using env vars; raises if misconfigured."""
    sheet_url = os.getenv("SHEET_URL", "")
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not m:
        raise RuntimeError("Bad SHEET_URL format in .env")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS path is missing/invalid")
    gc = gspread.service_account(filename=cred_path)
    sh = gc.open_by_key(m.group(1))
    ws = sh.sheet1  # or pick a specific worksheet name if you prefer
    return gc, sh, ws

def _load_admin_users():
    """Load admin_users.json and return dict."""
    with open(os.path.join(os.path.dirname(__file__), "admin_users.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    return {u["username"]: u for u in data.get("users", [])}

def _require_admin():
    return session.get("admin") is True

# ---- routes ----
@admin_bp.get("/login")
def login_form():
    if _require_admin():
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html")

@admin_bp.post("/login")
def login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    users = _load_admin_users()
    user = users.get(username)
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password.", "danger")
        return redirect(url_for("admin.login_form"))
    session["admin"] = True
    flash("Welcome, admin!", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.get("/logout")
def logout():
    session.pop("admin", None)
    flash("Logged out.", "info")
    return redirect(url_for("admin.login_form"))

@admin_bp.get("/")
def dashboard():
    if not _require_admin():
        return redirect(url_for("admin.login_form"))
    # Optional: read the first few rows to show a preview
    try:
        _, _, ws = _open_sheet()
        headers = ws.row_values(1)
        preview = ws.get_all_records(head=1, expected_headers=headers)[:5]
    except Exception as e:
        headers, preview = [], []
        flash(f"Warning: couldn’t read sheet preview ({e})", "warning")
    return render_template("admin/dashboard.html", headers=headers, preview=preview)

@admin_bp.post("/add")
def add_row():
    if not _require_admin():
        return redirect(url_for("admin.login_form"))

    # Adjust these fields to match your sheet columns
    data = {
        "Title": request.form.get("title", "").strip(),
        "URL": request.form.get("url", "").strip(),
        "Audience": request.form.get("audience", "").strip(),
        "Status": request.form.get("status", "Published").strip(),
        "Notes": request.form.get("notes", "").strip(),
    }

    # Basic validation
    if not data["Title"] or not data["URL"]:
        flash("Title and URL are required.", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        _, _, ws = _open_sheet()

        # Map data to existing headers (best effort)
        headers = ws.row_values(1)
        row = [data.get(h, "") for h in headers] if headers else list(data.values())

        # If there are headers, match by name; if not, append values in fixed order
        if headers:
            row = [data.get(h, "") for h in headers]
        else:
            row = [data["Title"], data["URL"], data["Audience"], data["Status"], data["Notes"]]

        ws.append_row(row, value_input_option="USER_ENTERED")
        flash("Row added to the sheet ✅", "success")
    except Exception as e:
        flash(f"Failed to add row: {e}", "danger")

    return redirect(url_for("admin.dashboard"))
