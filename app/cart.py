# app/cart.py
from flask import Blueprint, render_template, redirect, url_for, jsonify, flash, request
from flask_login import current_user
import datetime
from .models.cart import CartItem
from .models.wishlist_2 import WishlistItem
from flask import current_app as app
from decimal import Decimal

bp = Blueprint('cart', __name__)

@bp.route('/cart')
def cart():
    if current_user.is_authenticated:
        cart_items = CartItem.get_all_by_account(current_user.id)
        wishlist_items = WishlistItem.get_all_by_uid_since(current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))
        # Check if each wishlist item is in cart.
        for item in wishlist_items:
            rows = app.db.execute('''
                SELECT id FROM Cart
                WHERE accountid = :accountid AND productid = :productid
            ''', accountid=current_user.id, productid=item.productid)
            item.in_cart = True if rows else False
    else:
        flash("Please log in to view your cart.", "warning")
        return redirect(url_for('accounts.login', next=request.path))
    return render_template('cart.html', items=cart_items, wishlist_items=wishlist_items)

@bp.route('/cart/add/<int:product_id>', methods=['POST'])
def cart_add(product_id):
    if not current_user.is_authenticated:
        flash("User not authenticated", "danger")
        return redirect(url_for('accounts.login'))

    # 1-10 comes from the <select>; default to 1 just in case
    qty = int(request.form.get("quantity", 1))
    if qty < 1:
        flash("Invalid quantity requested.", "danger")
        return redirect(url_for('product.product_detail', product_id=product_id))

    item = CartItem.add_with_inventory_check(current_user.id, product_id, qty)
    if item is None:
        flash("Sorry, not enough inventory for that quantity.", "warning")
        return redirect(url_for('product_2.product_detail', product_id=product_id))

    next_url = request.args.get("next", url_for('index.index'))
    return redirect(next_url)

@bp.route('/cart/increment/<int:cart_item_id>', methods=['POST'])
def cart_increment(cart_item_id):
    if not current_user.is_authenticated:
        flash("Please log in first.", "warning")
        return redirect(url_for('accounts.login', next=request.referrer or url_for('cart.cart')))

    try:
        _, err = CartItem.increment_with_inventory_check(cart_item_id)
        if err:
            flash(err, "warning")               # => JS alert on cart.html
        return redirect(url_for('cart.cart'))
    except Exception as e:
        flash("Unexpected error: " + str(e), "danger")
        return redirect(url_for('cart.cart'))

@bp.route('/cart/decrement/<int:cart_item_id>', methods=['POST'])
def cart_decrement(cart_item_id):
    if current_user.is_authenticated:
        try:
            CartItem.update_quantity(cart_item_id, -1)
            return redirect(url_for('cart.cart'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for('accounts.login', next=request.referrer or url_for('cart.cart')))

@bp.route('/cart/submit', methods=['POST'])
def cart_submit():
    # Ensure user is logged in.
    if not current_user.is_authenticated:
        flash("User not authenticated")
        return redirect(url_for('accounts.login'))

    # Retrieve all cart items for the buyer.
    items = CartItem.get_all_by_account(current_user.id)
    if not items:
        flash("Your cart is empty.")
        return redirect(url_for('cart.cart'))

    # Calculate the grand total of the order.
    grand_total = sum(Decimal(item.total_price) for item in items)

    # Check if buyer's balance is sufficient.
    buyer_row = app.db.execute('''
        SELECT accountbalance FROM Accounts
        WHERE id = :id
    ''', id=current_user.id)
    if not buyer_row:
        flash("Buyer account not found.")
        return redirect(url_for('cart.cart'))
    buyer_balance = Decimal(buyer_row[0][0])
    if buyer_balance < grand_total:
        flash("Insufficient balance. Your balance is ${:.2f} but total order is ${:.2f}."
              .format(buyer_balance, grand_total))
        return redirect(url_for('cart.cart'))

    # Check that each product's available quantity is sufficient.
    for item in items:
        inv_rows = app.db.execute('''
            SELECT qtyavailable FROM Inventory
            WHERE productid = :productid
              AND sellerid = (SELECT sellerid FROM Products_2 WHERE id = :productid)
        ''', productid=item.productid)
        if not inv_rows:
            flash(f"Inventory for product {item.product_name} not found.")
            return redirect(url_for('cart.cart'))
        qty_available = int(inv_rows[0][0])
        if qty_available < item.quantity:
            flash(f"Not sufficient quantity for product '{item.product_name}'. There are {qty_available} units available, but {item.quantity} are required. We are sorry for the inconvenience.")
            return redirect(url_for('cart.cart'))

    try:
        # Begin order processing.
        # 1. Deduct buyer's balance.
        new_buyer_balance = buyer_balance - grand_total
        app.db.execute('''
            UPDATE Accounts
            SET accountbalance = :balance
            WHERE id = :id
        ''', balance=new_buyer_balance, id=current_user.id)

        # 2. Create a new purchase record.
        purchase_rows = app.db.execute('''
            INSERT INTO Purchases_2 (accountid, total, addressid)
            VALUES (:accountid, :total, (SELECT addressid FROM Accounts WHERE id = :accountid))
            RETURNING id
        ''', accountid=current_user.id, total=grand_total)
        purchase_id = purchase_rows[0][0]

        # 3. Process each cart item.
        line_number = 1
        for item in items:
            # Determine seller id for the product.
            seller_row = app.db.execute('''
                SELECT sellerid FROM Products_2
                WHERE id = :pid
            ''', pid=item.productid)
            if not seller_row:
                flash(f"Seller for product '{item.product_name}' not found.")
                return redirect(url_for('cart.cart'))
            seller_id = seller_row[0][0]

            # Update the seller's balance (increase by this item's total price).
            seller_account_row = app.db.execute('''
                SELECT accountbalance FROM Accounts
                WHERE sellerid = :sellerid
            ''', sellerid=seller_id)
            if not seller_account_row:
                flash(f"Seller account for product '{item.product_name}' not found.")
                return redirect(url_for('cart.cart'))
            seller_balance = Decimal(seller_account_row[0][0])
            new_seller_balance = seller_balance + item.total_price
            app.db.execute('''
                UPDATE Accounts
                SET accountbalance = :balance
                WHERE sellerid = :sellerid
            ''', balance=new_seller_balance, sellerid=seller_id)

            # Update the inventory: subtract the quantity from qtyavailable
            # and add the same amount to qtyinprocess.
            app.db.execute('''
                UPDATE Inventory
                SET qtyavailable = qtyavailable - :qty,
                    qtyinprocess = qtyinprocess + :qty
                WHERE productid = :productid AND sellerid = :sellerid
            ''', qty=item.quantity, productid=item.productid, sellerid=seller_id)

            # 4. Insert a corresponding line item record.
            app.db.execute('''
                INSERT INTO LineItem (purchaseid, linenumber, productid, qty, sellerid, inprocesstimestamp, fulfillmenttimestamp)
                VALUES (:purchaseid, :linenumber, :productid, :qty, :sellerid, TIMEZONE('UTC', NOW()), NULL)
            ''', purchaseid=purchase_id, linenumber=line_number, productid=item.productid, qty=item.quantity, sellerid=seller_id)
            line_number += 1

        # 5. Clear the cart for the buyer.
        app.db.execute('''
            DELETE FROM Cart
            WHERE accountid = :accountid
        ''', accountid=current_user.id)

        return render_template('confirmation.html')
    except Exception as e:
        # If any error occurs, rollback (if your DB wrapper supports it) and display an error.
        flash("Order submission failed: " + str(e))
        return redirect(url_for('cart.cart'))