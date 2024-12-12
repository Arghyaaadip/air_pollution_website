from flask import Flask, render_template

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(debug=True)
