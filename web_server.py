
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Server is active!</h1><p>The web server is running successfully!</p>"

@app.route('/health')
def health():
    return {"status": "Server is active!", "message": "Web server is running"}

if __name__ == '__main__':
    # Use port 5001 as configured in .replit
    port = 5001
    print(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
