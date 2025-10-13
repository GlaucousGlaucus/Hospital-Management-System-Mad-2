from flask import Flask, render_template

app = Flask(__name__)

# Make sure Flask doesn’t cache templates or static files
# app.config['TEMPLATES_AUTO_RELOAD'] = True
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
def index():
    return render_template('index.html')

