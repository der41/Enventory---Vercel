from flask import render_template, redirect, url_for, flash, request, jsonify
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from decimal import Decimal
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from .models.account import Account
from .models.purchase_2 import Purchase
from .models.review import Review

from flask import Blueprint
bp = Blueprint('accounts', __name__)

# Adding all Flask forms for Account management

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class EditAccountForm(FlaskForm):
    username = StringField('New Username', validators=[Length(min=1, max=64)])
    email = StringField('New Email', validators=[Email()])
    password = PasswordField('New Password', validators=[Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Update Info')

    def validate_email(self, email):
        if email.data != current_user.email and Account.email_exists(email.data):
            raise ValidationError('That email is already taken.')

class RegistrationForm(FlaskForm):
    username = StringField('UserName', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    register_as_seller = BooleanField('Register as a new Seller')
    submit = SubmitField('Register')

    def validate_email(self, email):
        if Account.email_exists(email.data):
            raise ValidationError('Already an account with this email.')

# --- Routes ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        account = Account.get_by_auth(form.email.data, form.password.data)
        if account is None:
            flash('Invalid email or password')
            return redirect(url_for('accounts.login'))
        login_user(account)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if Account.register(email=form.email.data,
                             password=form.password.data,
                             username=form.username.data,
                             accountbalance=0.0,
                             register_as_seller=form.register_as_seller.data):
            flash('Congratulations, your account is now registered!')
            return redirect(url_for('accounts.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('index.index'))

@bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    # Find all the products the current user has ever bought:
    purchases_ready   = Purchase.fulfilled_for(current_user.id)   # all items shipped
    purchases_pending = Purchase.in_process_for(current_user.id)  # still being prepared

    # --- FIXED user_reviews query ---
    user_reviews = app.db.execute("""
        SELECT pr.id, pr.productid, p.name, pr.rating, pr.comment
        FROM Product_Reviews pr
        JOIN Products_2 p ON pr.productid = p.id
        WHERE pr.accountid = :accountid
        LIMIT 50
    """, accountid=current_user.id)

    seller_reviews = []
    if current_user.sellerid:
        seller_reviews = app.db.execute("""
        SELECT rating, comment
        FROM Seller_Reviews
        WHERE sellerid = :sellerid
        """, sellerid=current_user.sellerid)
        print(f"Current User's Seller ID: {current_user.sellerid}")
        print(f"Seller reviews: {seller_reviews}")  


    #Manage Account Balance
    if request.method == 'POST':
        deposit_raw = request.form.get('deposit', '').strip()
        withdraw_raw = request.form.get('withdraw', '').strip()

        if deposit_raw and withdraw_raw:
            return jsonify({'error': 'Please enter only a deposit or a withdrawal, not both.'}), 400
        elif not deposit_raw and not withdraw_raw:
            return jsonify({'error': 'Please enter a deposit or a withdrawal amount.'}), 400

        current_balance = Decimal(current_user.accountbalance)

        if deposit_raw:
            try:
                deposit_amount = Decimal(deposit_raw)
                if deposit_amount <= 0:
                    raise ValueError
            except:
                return jsonify({'error': 'Invalid deposit amount.'}), 400
            new_balance = current_balance + deposit_amount

        elif withdraw_raw:
            try:
                withdraw_amount = Decimal(withdraw_raw)
                if withdraw_amount <= 0:
                    raise ValueError
            except:
                flash("Invalid withdrawal amount.", "danger")
                return redirect(url_for('accounts.account'))

            if withdraw_amount > current_balance:
                flash("Sorry, you cannot withdraw more than your current balance!", "danger")
                return redirect(url_for('accounts.account'))
            new_balance = current_balance - withdraw_amount
            flash(f"Successfully withdrew ${withdraw_amount}", "success")


        app.db.execute("""
        UPDATE Accounts
        SET accountbalance = :new_balance
        WHERE id = :user_id
        """, new_balance=new_balance, user_id=current_user.id)

        current_user.accountbalance = new_balance
        flash(f"Balance updated: ${new_balance}", "success")
        return redirect(url_for('accounts.account'))

    # Get loyalty points and status for current user
    loyalty = app.db.execute("""
    SELECT loyaltypoints, loyaltystatus
    FROM Loyalty
    WHERE accountid = :accountid
    """, accountid=current_user.id)


    # If the user has loyalty data, store it; otherwise, set it to 0 and 'Silver'
    if loyalty:
        loyalty_points = loyalty[0][0]
        loyaltystatus = loyalty[0][1]
    else:
        loyalty_points = 0
        loyaltystatus = 'Silver'  # If they have no points, make them 'Silver'

    # Return template with all variables needed for account methods
    return render_template(
        'account.html',
        account=current_user,
        acctcreationdate=current_user.acctcreationdate,
        purchase_history=purchases_ready,
        purchase_in_process=purchases_pending,
        seller_reviews=seller_reviews,
        user_reviews=user_reviews,
        loyalty_points=loyalty_points,
        loyalty_status=loyaltystatus
    )

@bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    success = Account.delete_account(current_user.id)
    if success:
        logout_user()
        flash("Your account has been deleted successfully.", "success")
        return redirect(url_for('index.index'))
    else:
        flash("An error occurred while trying to delete your account. Please try again.")
        return redirect(url_for('index.index'))

@bp.route('/account/edit', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = EditAccountForm()

    if form.validate_on_submit():
        updated = False

        if form.username.data and form.username.data != current_user.username:
            app.db.execute("""
                UPDATE Accounts SET username = :username WHERE id = :id
            """, username=form.username.data, id=current_user.id)
            current_user.username = form.username.data
            updated = True

        if form.email.data and form.email.data != current_user.email:
            app.db.execute("""
                UPDATE Accounts SET email = :email WHERE id = :id
            """, email=form.email.data, id=current_user.id)
            current_user.email = form.email.data
            updated = True

        if form.password.data:
            hashed_pw = generate_password_hash(form.password.data)
            app.db.execute("""
                UPDATE Accounts SET password = :password WHERE id = :id
            """, password=hashed_pw, id=current_user.id)
            updated = True

        if updated:
            flash('Your account information has been updated.', 'success')
        else:
            flash('No changes were made.', 'info')

        return redirect(url_for('accounts.account'))

    return render_template('edit_account.html', form=form)
