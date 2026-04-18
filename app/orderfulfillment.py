from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from app.models.orderfulfillment import OrderFulfillment

bp = Blueprint('orderfulfillment_bp', __name__)

@bp.route('/orders')
@login_required
def view_orders():
    seller_id = OrderFulfillment.get_seller_id(current_user.id)
    if not seller_id:
        return "You are not a seller.", 403

    lineitems = OrderFulfillment.get_lineitems_for_seller(seller_id)
    return render_template('orderfulfillment.html', lineitems=lineitems)

@bp.route('/orders/edit/<int:lineitem_id>', methods=['GET', 'POST'])
@login_required
def edit_fulfillment(lineitem_id):
    seller_id = OrderFulfillment.get_seller_id(current_user.id)
    if not seller_id:
        return "You are not a seller.", 403

    item = OrderFulfillment.get_lineitem_details(lineitem_id, seller_id)
    if not item:
        return "Unauthorized or invalid item.", 403

    if request.method == 'POST':
        status = request.form.get('status')
        now = datetime.utcnow()

        if status == 'inprocess' and not item['inprocesstimestamp']:
            OrderFulfillment.set_inprocess(lineitem_id, now)

        elif status == 'fulfilled':
            if not item['inprocesstimestamp']:
                OrderFulfillment.set_inprocess(lineitem_id, now)
            OrderFulfillment.set_fulfilled(lineitem_id, now)

        flash('Fulfillment status updated.', 'success')
        return redirect(url_for('orderfulfillment_bp.view_orders'))

    return render_template('edit_orderfulfillment.html', item=item)
