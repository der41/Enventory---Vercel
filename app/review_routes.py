from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from flask import current_app as app

bp = Blueprint('review', __name__)

# ---------------------------------------
# Product Review
# ---------------------------------------
@bp.route('/add_product_review/<int:productid>', methods=['GET', 'POST'])
def add_product_review(productid):
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        app.db.execute('''
            INSERT INTO Product_Reviews (productid, accountid, rating, comment)
            VALUES (:productid, :accountid, :rating, :comment)
        ''', productid=productid, accountid=current_user.id, rating=rating, comment=comment)

        flash('Product review submitted!', 'success')
        return redirect(url_for('accounts.account'))

    # If GET, show form with context
    product = app.db.execute('SELECT name FROM Products_2 WHERE id = :id', id=productid)[0]
    return render_template('submit_review.html', review_type='Product', item_name=product.name)

# ---------------------------------------
# Seller Review
# ---------------------------------------
@bp.route('/add_seller_review/<int:sellerid>', methods=['GET', 'POST'])
def add_seller_review(sellerid):
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        app.db.execute('''
            INSERT INTO Seller_Reviews (sellerid, accountid, rating, comment)
            VALUES (:sellerid, :accountid, :rating, :comment)
        ''', sellerid=sellerid, accountid=current_user.id, rating=rating, comment=comment)

        flash('Seller review submitted!', 'success')
        return redirect(url_for('accounts.account'))

    # If GET, show form with context
    seller = app.db.execute('SELECT username FROM Accounts WHERE id = :id', id=sellerid)[0]
    return render_template('submit_review.html', review_type='Seller', item_name=seller.username)

# ---------------------------------------
# Seller Profile Page
# ---------------------------------------
@bp.route('/seller/<int:sellerid>')
def seller_profile(sellerid):
    # Get seller username
    seller = app.db.execute('''
        SELECT username
        FROM Accounts
        WHERE id = :id
    ''', id=sellerid)[0]

    # Get all reviews for this seller (no time_created field!)
    reviews = app.db.execute('''
        SELECT rating, comment
        FROM Seller_Reviews
        WHERE sellerid = :sellerid
    ''', sellerid=sellerid)

    # Get all products sold by this seller
    products = app.db.execute('''
        SELECT id, name, price, image
        FROM Products_2
        WHERE sellerid = :sellerid
        AND status = TRUE
    ''', sellerid=sellerid)

    # Calculate average rating
    if reviews:
        avg_rating = sum([r.rating for r in reviews]) / len(reviews)
    else:
        avg_rating = None

    # Pass everything to seller_profile.html
    return render_template('seller_profile.html', seller=seller, reviews=reviews, avg_rating=avg_rating, products=products)
