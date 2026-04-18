from flask import Blueprint, render_template, request
from flask_login import current_user
from .models.event import Event
from .models.product_2 import Product_2

bp = Blueprint('events', __name__)

@bp.route('/events')
def list_events():
    events = Event.get_all()
    unique_events = {event.name: event for event in events}.values()  # deduplicate by name
    return render_template('events.html', events=unique_events)

@bp.route('/events/<event_name>')
def view_products_by_event(event_name):
    products = Event.get_products_by_event(event_name)
    return render_template('event_products.html', event_name=event_name, products=products)
