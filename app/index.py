from flask import render_template, request
from flask_login import current_user
from flask import Blueprint,current_app as app
import random
from .models.product_2 import Product_2
from .models.purchase_2 import Purchase
from .models.orderfulfillment import OrderFulfillment

bp = Blueprint('index', __name__)

@bp.route('/')
def index():
    k = request.args.get('k', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 9
    sort = request.args.get('sort')
    query = request.args.get('query', '').strip()

    # Get all available products
    if k:
        all_products = Product_2.get_top_k_expensive(k, status=True)
    else:
        all_products = Product_2.get_all(status=True)

    #query search for products
    if query:
        query_lower = query.lower()
        all_products = [p for p in all_products if query_lower in p.name.lower() or query_lower in p.description.lower()]

    # find all the products current user has ever bought:
    # i dont think we
    if current_user.is_authenticated:
        purchases = Purchase.get_all_by_accountid(current_user.id)
        seller_id = OrderFulfillment.get_seller_id(current_user.id)
    else:
        purchases = None
        seller_id = None

    # Sort by price
    if sort == 'price_asc':
        all_products.sort(key=lambda p: p.price)
    elif sort == 'price_desc':
        all_products.sort(key=lambda p: p.price, reverse=True)
    elif sort == 'most_popular': # sort by most frequently purchased
        all_products = Product_2.get_all_sorted_by_popularity()

    # Filter products that are in stock
    in_stock_products = []
    for p in all_products:
        result = app.db.execute('''
            SELECT qtyavailable FROM Inventory
            WHERE productid = :pid AND sellerid = :sid
        ''', pid=p.id, sid=p.sellerid)
        if result and result[0][0] > 0:
            in_stock_products.append(p)

    # Randomly select up to 5 featured in-stock products
    featured_products = random.sample(in_stock_products, min(5, len(in_stock_products)))

    # Pagination logic
    total_products = len(in_stock_products)
    total_pages = (total_products + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    products = in_stock_products[start:end]


    return render_template('index.html',
                           avail_products=products,
                           featured_products=featured_products,
                           purchase_history=purchases,
                           k=k,
                           seller_id=seller_id,
                           sort=sort,
                           page=page,
                           total_pages=total_pages,
                           total_products=total_products,
                           start_index=start + 1,
                           end_index=min(end, total_products),
                           search_query=query)
