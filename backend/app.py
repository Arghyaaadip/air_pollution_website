import os
import sys
import atexit
import shutil
import smtplib
import ssl
import subprocess
import json
from email.mime.text import MIMEText
from pathlib import Path
from .admin import admin_bp

# env (python-dotenv)
from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    session,  # <-- sessions for admin login
)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent              # backend/
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create ONE Flask app (don’t create another later)
app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/",  # lets /images/* work
)

# secret for sessions/flash
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "dev-change-me")

# Also allow a top-level .env if you keep it there
env_top = BASE_DIR.parent / ".env"
if env_top.exists():
    load_dotenv(env_top)

# Also support "/static/..." paths (because some templates use that form)
@app.route("/static/<path:filename>")
def static_alias(filename):
    return send_from_directory(app.static_folder, filename)

# ---- Optional: Start Node/Express server.js as a child process (disabled by default) ----
_node_proc = None

def _start_node_if_requested():
    """Starts server.js with Node if START_NODE=1 and server.js is found."""
    global _node_proc
    if os.getenv("START_NODE", "0") != "1":
        return

    node = shutil.which("node")
    if not node:
        print("[WARN] START_NODE=1 but 'node' not found in PATH. Skipping Node start.")
        return

    candidates = [BASE_DIR / "server.js", BASE_DIR.parent / "server.js"]
    server_js = next((p for p in candidates if p.exists()), None)
    if not server_js:
        print("[WARN] START_NODE=1 but could not find server.js. Looked in:", candidates)
        return

    workdir = server_js.parent
    env = os.environ.copy()
    env.setdefault("PORT", "5000")
    try:
        _node_proc = subprocess.Popen(
            [node, str(server_js)],
            cwd=str(workdir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(f"[INFO] Started Node server: {server_js} (pid={_node_proc.pid}) on PORT={env['PORT']}")
    except Exception as e:
        print(f"[WARN] Failed to start Node server.js: {e}")

def _stop_node_if_running():
    global _node_proc
    if _node_proc and _node_proc.poll() is None:
        try:
            _node_proc.terminate()
        except Exception:
            pass

atexit.register(_stop_node_if_running)
_start_node_if_requested()

# ---- Helpers ----
def _home_template_fallback():
    """Choose a homepage that actually exists in your templates."""
    for name in ("index.html", "impacts.html", "test.html"):
        if (TEMPLATES_DIR / name).exists():
            return name
    return None

def _send_email_via_gmail(sender_name: str, sender_email: str, body: str):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_PASS")
    if not gmail_user or not gmail_pass:
        raise RuntimeError("GMAIL_USER or GMAIL_PASS is not set in environment/.env")

    msg = MIMEText(f"You have received a new message from {sender_name} ({sender_email}):\n\n{body}")
    msg["Subject"] = f"Message from {sender_name}"
    msg["From"] = gmail_user
    msg["To"] = gmail_user

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=context)
        server.login(gmail_user, gmail_pass)
        server.send_message(msg)

# ---- Public routes ----

@app.route("/")
def home():
    chosen = _home_template_fallback()
    if chosen:
        return render_template(chosen)
    return "<h1>Home</h1><p>Create templates/index.html or impacts.html for a proper homepage.</p>"

@app.route("/collections")
def collections():
    sheet_url = os.getenv("SHEET_URL", "#")
    return render_template("collections.html", sheet_url=sheet_url)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("contact.html")

    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not name or not email or not message:
        flash("All fields are required. Please fill out the form completely.", "error")
        return redirect(url_for("contact"))

    try:
        _send_email_via_gmail(name, email, message)
        flash("Your message was sent successfully!", "success")
        return redirect(url_for("thank_you"))
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")
        return (f"<h1>Something went wrong. Please try again later.</h1><p>{str(e)}</p>", 500)

@app.route("/thank-you")
def thank_you():
    return render_template("thank-you.html")

@app.route("/impacts")
def impacts():
    return render_template("impacts.html")

@app.route("/sustainability")
def sustainability():
    return render_template("sustainability.html")

@app.route("/community")
def community():
    return render_template("community.html")

@app.route("/other")
def other():
    return render_template("other.html")

# ---- Admin blueprint registration ----
# (Routes live in backend/admin/__init__.py)
from admin import admin_bp
app.register_blueprint(admin_bp, url_prefix="/admin")

# ---- Entry point ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))  # Cloud Run sets PORT
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"[INFO] Flask running on http://0.0.0.0:{port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
