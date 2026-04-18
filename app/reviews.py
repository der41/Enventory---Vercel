from flask import Blueprint, jsonify, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from .models.review import Review

bp = Blueprint('reviews', __name__)  # <--- Blueprint must be declared BEFORE any @bp.route()

@bp.route('/reviews')
def reviews():
    if current_user.is_authenticated:
        try:
            items = Review.get_recent_by_accountid(current_user.id)
            return render_template('reviews.html', items=items)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "User not authenticated"}), 401

@bp.route('/review/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.get(review_id)
    if not review or review.accountid != current_user.id:
        flash("Unauthorized access to edit review.", "danger")
        return redirect(url_for('accounts.account'))

    if request.method == 'POST':
        new_rating = request.form.get('rating')
        new_comment = request.form.get('comment')
        Review.update(review_id, new_rating, new_comment)
        flash("Review updated successfully!", "success")
        return redirect(url_for('accounts.account'))

    return render_template('edit_review.html', review=review)

@bp.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.get(review_id)
    if not review or review.accountid != current_user.id:
        flash("Unauthorized access to delete review.", "danger")
        return redirect(url_for('accounts.account'))

    Review.delete(review_id)
    flash("Review deleted successfully!", "success")
    return redirect(url_for('accounts.account'))
