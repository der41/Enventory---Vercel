from flask import jsonify, render_template
from flask import redirect, url_for
from flask_login import current_user
import datetime

from .models.product import Product
from .models.wishlist import WishlistItem
from humanize import naturaltime

from flask import Blueprint
bp = Blueprint('wishlist', __name__)

@bp.route('/wishlist')
def wishlist():
    # get all items on the wishlist
    if current_user.is_authenticated:
        items = WishlistItem.get_all_by_uid_since(
            current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))
    else:
        wishlist = None
        return jsonify({}), 404
    return render_template('wishlist.html',
                       items=items,
                       humanize_time=humanize_time)

        
@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
def wishlist_add(product_id):
    if current_user.is_authenticated:
        try:
            item = WishlistItem.insert_object(
                current_user.id, 
                product_id, 
                datetime.datetime(1980, 9, 14, 0, 0, 0)
            )
            if item is None:
                return jsonify({"error": "Failed to add item to wishlist"}), 400
            return redirect(url_for('wishlist.wishlist'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "User not authenticated"}), 401

def humanize_time(dt):
    return naturaltime(datetime.datetime.now() - dt)
