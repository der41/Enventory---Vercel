from flask import Blueprint, render_template
from flask_login import current_user
from .models.product_2 import Product_2
from .models.review import Review
from .models.event import Event

bp = Blueprint('product_2', __name__)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product_2.get_with_seller(product_id)
    # get reviews for this product
    reviews = Review.get_by_productid(product_id)
    # for the customer also bought section
    also_bought = Product_2.get_also_bought(product_id)
    # get the events this product is listed in
    related_events = Event.get_event_by_product_id(product_id)
    return render_template('product_detail.html', product=product, reviews=reviews,also_bought=also_bought, related_events=related_events)
