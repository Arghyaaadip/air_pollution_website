import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import bcrypt
import gspread
from google.oauth2.service_account import Credentials
from flask import request, flash



# ---- Google Sheets setup ----

# 1) Scopes for reading & writing Sheets:
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 2) Load your service-account key
creds = Credentials.from_service_account_file(
    os.path.join(os.path.dirname(__file__), 'scicomwebsite.json'),
    scopes=SCOPES
)

# 3) Create a gspread client via the helper
gc = gspread.authorize(creds)

# 4) Point at your target Sheet (paste your actual URL or ID)
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1sbBxgNuTO596fSs8TiFIpIQonL1cXYzcKjqqpwtZalE/edit'
sh = gc.open_by_url(SHEET_URL)
worksheet = sh.sheet1  # or .worksheet('Sheet Name')

# 5) Helper functions
def load_spreadsheet_rows():
    """Fetch all rows as a list of lists."""
    return worksheet.get_all_values()

def append_to_spreadsheet(row_values):
    """Append a single new row to the sheet."""
    worksheet.append_row(row_values, value_input_option='USER_ENTERED')



# compute absolute path to your “templatess” folder
template_dir = os.path.join(os.path.dirname(__file__), 'templatess')


app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'your_secret_key_here'  # replace with a secure secret

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'


# Load admin credentials from JSON file
def load_admin_data():
    with open('admin_users.json') as f:
        return json.load(f)

class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    data = load_admin_data()
    if user_id in data:
        return AdminUser(user_id)
    return None

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        data = load_admin_data()
        user = data.get(username)
        if user and bcrypt.checkpw(password, user['password_hash'].encode('utf-8')):
            login_user(AdminUser(username))
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html', user=current_user)

from flask import request, flash

@app.route('/admin/materials', methods=['GET'])
@login_required
def admin_materials():
    # Fetch all rows from the Sheet
    rows = load_spreadsheet_rows()
    return render_template('admin/materials.html', rows=rows)

@app.route('/admin/materials', methods=['POST'])
@login_required
def add_material():
    # These names match the <input name="…"> in your form
    title = request.form['title']
    url   = request.form['url']
    append_to_spreadsheet([title, url])
    flash('Added new material!', 'success')
    return redirect(url_for('admin_materials'))




# Route for the homepage
@app.route('/')
def home():
    print("Home route accessed")  # Debugging statement
    return render_template('index.html')

# Other routes
@app.route('/impacts')
def impacts():
    print("Impacts route accessed")  # Debugging statement
    return render_template('impacts.html')

@app.route('/community')
def community():
    print("Community route accessed")  # Debugging statement
    return render_template('community.html')

@app.route('/sustainability')
def sustainability():
    print("Sustainability route accessed")  # Debugging statement
    return render_template('sustainability.html')

@app.route('/other')
def other():
    print("Other route accessed")  # Debugging statement
    return render_template('other.html')

@app.route('/collections')
def collections():
    # Public users get a link to the live Sheet
    return render_template('collections.html', sheet_url='https://docs.google.com/spreadsheets/d/1sbBxgNuTO596fSs8TiFIpIQonL1cXYzcKjqqpwtZalE/edit?gid=634347005#gid=634347005')

if __name__ == "__main__":
    app.run(debug=True)
