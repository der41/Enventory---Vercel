from flask import render_template, request
from flask_login import current_user
from flask import Blueprint,current_app as app
import re
from .models.product_2 import Product_2
from .models.purchase_2 import Purchase
from .models.orderfulfillment import OrderFulfillment

bp = Blueprint('product_search', __name__)

@bp.route('/search', endpoint='search_results')
def search_results():
    query = request.args.get('query', '').strip()
    results = []
    if query:
        products = Product_2.get_all(status=True)
        pattern = re.compile(r'\b{}\b'.format(re.escape(query)), re.IGNORECASE)
        results = [p for p in products if pattern.search(p.name) or pattern.search(p.description)]
    
    return render_template('search_results.html', query=query, results=results)