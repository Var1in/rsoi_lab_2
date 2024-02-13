from flask import jsonify

from src.config.flask_config import ServerConfiguration
from src.config.program_config import ProgramConfiguration
from src.static import routes

orig_app = ServerConfiguration('gunicorn').app
orig_app.register_blueprint(routes)

app = orig_app

app_config = ProgramConfiguration()

@app.route("/")
def start_page():
    return jsonify(hello="world", first_message="test")
