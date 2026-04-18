from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.inventory import Inventory
from app.storage import upload_product_image

bp = Blueprint('inventory_bp', __name__)

@bp.route('/inventory')
@login_required
def view_inventory():
    seller_id = Inventory.get_seller_id_from_account(current_user.id)
    if not seller_id:
        return "You are not a registered seller.", 403

    products = Inventory.get_full_inventory_by_seller(seller_id)
    return render_template("inventory.html", products=products)

@bp.route('/inventory/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    seller_id = Inventory.get_seller_id_from_account(current_user.id)
    if not seller_id:
        return "Unauthorized access", 403

    Inventory.soft_delete_product(product_id, seller_id)
    return redirect(url_for('inventory_bp.view_inventory'))

@bp.route('/inventory/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    seller_id = Inventory.get_seller_id_from_account(current_user.id)
    if not seller_id:
        return "Unauthorized access", 403

    categories = Inventory.get_all_categories()
    subcategories = Inventory.get_all_subcategories()
    product = Inventory.get_product_details(product_id, seller_id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        subcategory = request.form['subcategory']
        price = float(request.form['price'])
        status = request.form['status'] == 'true'
        image = request.files.get('image')

        category_id = Inventory.add_or_get_category(category, subcategory)
        Inventory.update_product_details(product_id, name, description, price, category_id, status)
        Inventory.update_inventory_timestamp(product_id, seller_id)

        if image and image.filename:
            url = upload_product_image(image, name)
            Inventory.set_image_path(product_id, url)

        flash("Product updated successfully.", "success")
        return redirect(url_for('inventory_bp.view_inventory'))

    return render_template("edit_product.html", product=product,
                           categories=categories, subcategories=subcategories,
                           current_category=product['category'],
                           current_subcategory=product['subcategory'])

@bp.route('/inventory/manage/<int:product_id>', methods=['GET', 'POST'])
@login_required
def manage_inventory(product_id):
    seller_id = Inventory.get_seller_id_from_account(current_user.id)
    if not seller_id:
        return "Unauthorized access", 403

    inventory = Inventory.get_inventory_item(product_id, seller_id)
    product = Inventory.get_product_name(product_id)

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        action = request.form['action']
        Inventory.modify_quantity(product_id, seller_id, quantity, action)
        Inventory.update_inventory_timestamp(product_id, seller_id)
        return redirect(url_for('inventory_bp.view_inventory'))

    return render_template("manage_inventory.html", inventory=inventory, product=product)

@bp.route('/inventory/add_new', methods=['GET', 'POST'])
@login_required
def add_new_product():
    seller_id = Inventory.get_seller_id_from_account(current_user.id)
    if not seller_id:
        return "Unauthorized access", 403

    categories = Inventory.get_all_categories()
    subcategories = Inventory.get_all_subcategories()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        subcategory = request.form['subcategory']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        image = request.files.get('image')

        category_id = Inventory.add_or_get_category(category, subcategory)
        product_id = Inventory.add_product(name, description, seller_id, price, category_id)
        Inventory.add_to_inventory(product_id, seller_id, quantity)

        if image and image.filename:
            url = upload_product_image(image, name)
            Inventory.set_image_path(product_id, url)

        flash("Product successfully added.", "success")
        return redirect(url_for('inventory_bp.view_inventory'))

    return render_template('add_new_product.html', categories=categories, subcategories=subcategories)
