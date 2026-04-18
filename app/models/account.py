from flask_login import UserMixin, login_required, current_user
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash


from .. import login

class Account(UserMixin):
    def __init__(self, id, email, username, acctcreationdate, accountbalance, sellerid):
        self.id = id
        self.email = email
        self.username = username
        self.acctcreationdate = acctcreationdate
        self.accountbalance = accountbalance
        self.sellerid = sellerid


    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
SELECT password, id, email, username, acctcreationdate, accountbalance, sellerid
FROM Accounts
WHERE email = :email
""",
                              email=email)
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return Account(*(rows[0][1:]))

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
SELECT email
FROM Accounts
WHERE email = :email
""",
                              email=email)
        return len(rows) > 0

    @staticmethod
    #need to figure out how to allow someone to register as a seller, by creating a new seller id
    #new seller id can be whatever the max seller ID is + 1
    def register(email, password, username, accountbalance, register_as_seller=False):
        try:
            rows = app.db.execute("""
INSERT INTO Accounts(email, password, username, accountbalance)
VALUES(:email, :password, :username, :accountbalance)
RETURNING id
""",
                                  email=email,
                                  password=generate_password_hash(password),
                                  username=username,
                                  accountbalance=0.0)
            id = rows[0][0]
            user_id = rows[0][0]
            if register_as_seller:
                rows = app.db.execute("""
                SELECT MAX(sellerid) FROM Accounts
                """)
                max_sellerid = rows[0][0] or 0
                new_sellerid = max_sellerid + 1

                #update new user record with the generated sellerid
                app.db.execute("""
                UPDATE ACCOUNTS
                SET sellerid = :new_sellerid
                WHERE id = :user_id
                """, new_sellerid=new_sellerid, user_id=user_id)
                print(f"New Seller ID: {new_sellerid}")

            return Account.get(id)
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    @login.user_loader
    def get(id):
        rows = app.db.execute("""
SELECT id, email, username, acctcreationdate, accountbalance, sellerid
FROM Accounts
WHERE id = :id
""",
                              id=id)
        return Account(*(rows[0])) if rows else None

    #function to delete an an account given account_id
    @staticmethod
    def delete_account(user_id):
        try:
            # Delete the user account
            app.db.execute("""
            DELETE FROM Accounts WHERE id = :user_id
            """, user_id=user_id)

            # Delete the account from all other tables as well
            app.db.execute("""
            DELETE FROM Purchases_2 WHERE accountid = :user_id
            """, user_id=user_id)

            app.db.execute("""
            DELETE FROM Cart WHERE accountid = :user_id
            """, user_id=user_id)

            app.db.execute("""
            DELETE FROM Wishlist_2 WHERE accountid = :user_id
            """, user_id=user_id)

            app.db.execute("""
            DELETE FROM Loyalty WHERE accountid = :user_id
            """, user_id=user_id)

            app.db.execute("""
            DELETE FROM Address WHERE accountid = :user_id
            """, user_id=user_id)

            app.db.execute("""
            DELETE FROM Seller_Reviews WHERE accountid = :user_id
            """, user_id=user_id)

            app.db.execute("""
            DELETE FROM Product_Reviews WHERE accountid = :user_id
            """, user_id=user_id)

            return True  # Deletion was successful
        except Exception as e:
            print(f"Error deleting account: {e}")
            return False  # False if the account was not successfully deleted

