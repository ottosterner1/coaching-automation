from flask import Flask, send_from_directory
from app import create_app
import os

app = create_app()

# Add this to serve the React static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path.startswith('api'):
        return app.view_functions[path]()
    try:
        return send_from_directory('app/static/dist', path)
    except:
        return send_from_directory('app/static/dist', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)