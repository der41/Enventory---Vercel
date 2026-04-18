from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import current_user
from .models.purchase_2 import Purchase
from flask import current_app as app

bp = Blueprint('purchase', __name__)

@bp.route('/purchase/<int:purchase_id>')
def purchase_detail(purchase_id):
    # Ensure the purchase belongs to the current user
    purchase = Purchase.get(purchase_id)
    if not purchase or purchase.accountid != current_user.id:
        flash("Purchase not found or unauthorized access", "danger")
        return redirect(url_for('accounts.account'))  # Adjust this as needed

    # Get line items for this purchase
    line_items = app.db.execute('''
        SELECT li.linenumber, li.qty, p.name, p.price, p.image,
            li.productid, li.sellerid
        FROM LineItem li
        JOIN Products_2 p ON li.productid = p.id
        WHERE li.purchaseid = :purchase_id
        ORDER BY li.linenumber
    ''', purchase_id=purchase_id)

    # Pass the raw rows; your template can loop through them.
    return render_template('purchase_detail.html',
                           purchase=purchase,
                           line_items=line_items)
