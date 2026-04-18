from flask import Blueprint, render_template
from app.models.category import Category

bp = Blueprint('categories', __name__, url_prefix='/categories')

@bp.route('/')
def list_categories():
    categories = Category.get_all_categories()
    return render_template('categories.html', categories=categories)

@bp.route('/<category_name>')
def view_category(category_name):
    subcategories = Category.get_subcategories_by_category(category_name)
    products = Category.get_products_by_category(category_name)
    return render_template('category_detail.html', 
                           category=category_name,
                           subcategories=subcategories,
                           products=products)
