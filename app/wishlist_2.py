#app/wishlist_2.py
from flask import jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user
import datetime
from .models.wishlist_2 import WishlistItem
from .models.category import Category

from flask import current_app as app
from humanize import naturaltime
from flask import Blueprint

bp = Blueprint('wishlist', __name__)

@bp.route('/wishlist')
def wishlist():
    if not current_user.is_authenticated:
        flash("Please log in to view your wishlist.", "warning")
        return redirect(url_for('accounts.login', next=request.path))

    # 1) load wishlist items
    items = WishlistItem.get_all_by_uid_since(
        current_user.id,
        datetime.datetime(1980, 9, 14, 0, 0, 0)
    )

    # 2) mark which are already in cart
    in_cart_ids = {
        row[0]
        for row in app.db.execute(
            "SELECT productid FROM Cart WHERE accountid = :uid",
            uid=current_user.id
        )
    }
    for item in items:
        item.in_cart = item.productid in in_cart_ids

    # 3) collect all categories of those wishlist items
    cats = {
        row[0]
        for row in app.db.execute(
            """
            SELECT DISTINCT pc.category
              FROM Products_2 p
              JOIN ProductCategories pc ON p.categoryid = pc.id
             WHERE p.id = ANY(:pids)
            """,
            pids=[i.productid for i in items]
        )
    }

    # 4) fetch up to 3 recommended products per category, up to a total of 9
    recommended: list = []
    seen = {i.productid for i in items}
    for cat in cats:
        count_for_cat = 0
        for p in Category.get_products_by_category(cat):
            if p.id in seen:
                continue
            # annotate whether it's already in cart
            p.in_cart = p.id in in_cart_ids
            recommended.append(p)
            seen.add(p.id)
            count_for_cat += 1
            # stop at 3 per category
            if count_for_cat >= 3:
                break
        # stop overall when we have 9
        if len(recommended) >= 9:
            break

    # 5) trim to exactly 9 if needed
    recommended = recommended[:9]

    # 6) render including the new 'recommended' list
    return render_template(
        'wishlist.html',
        items=items,
        recommended=recommended,
        humanize_time=humanize_time
    )
    
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
                flash("Failed to add item to wishlist", "danger")
                return redirect(url_for('wishlist.wishlist'))
            return redirect(url_for('wishlist.wishlist'))
        except Exception as e:
            flash(str(e), "danger")
            return redirect(url_for('wishlist.wishlist'))
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('accounts.login', next=request.referrer or url_for('wishlist.wishlist')))

@bp.route('/wishlist/remove/<int:wishlist_id>', methods=['POST'])
def wishlist_remove(wishlist_id):
    if current_user.is_authenticated:
        if WishlistItem.remove_object(wishlist_id):
            pass
        else:
            flash("Failed to remove item from wishlist", "danger")
        return redirect(url_for('wishlist.wishlist'))
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('accounts.login', next=request.referrer or url_for('wishlist.wishlist')))

def humanize_time(dt):
    return naturaltime(datetime.datetime.now() - dt)


