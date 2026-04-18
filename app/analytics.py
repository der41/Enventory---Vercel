from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from .models import analytics

bp = Blueprint('analytics', __name__)

@bp.route('/analytics', methods=['GET'])
@login_required
def seller_insights():
    date_filter = request.args.get('date_filter', 'YTD')
    manual_start = request.args.get('start_date')
    manual_end = request.args.get('end_date')

    seller_id = current_user.sellerid

    sales_by_product = analytics.get_sales_by_product(seller_id, manual_start, manual_end, date_filter)
    monthly_qty = analytics.get_monthly_sales_qty(seller_id, manual_start, manual_end, date_filter)
    monthly_avg_times = analytics.get_monthly_avg_times(seller_id, manual_start, manual_end, date_filter)
    zero_qty_products = analytics.get_zero_qty_products(seller_id)
    unprocessed_orders = analytics.get_unprocessed_orders(seller_id)
    in_process_unfulfilled_orders = analytics.get_inprocess_unfulfilled_orders(seller_id)

    return render_template('analytics.html',
                           sales_by_product=sales_by_product,
                           monthly_qty=monthly_qty,
                           monthly_avg_times=monthly_avg_times,
                           zero_qty_products=zero_qty_products,
                           unprocessed_orders=unprocessed_orders,
                           in_process_unfulfilled_orders=in_process_unfulfilled_orders,
                           date_filter=date_filter,
                           manual_start=manual_start,
                           manual_end=manual_end)
