from flask import Blueprint

routes = Blueprint('requests', __name__)

from src.static.api_routes import *