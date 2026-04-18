#app/models/wishlist_2.py
from flask import current_app as app

class WishlistItem:
    def __init__(self, id, accountid, productid, time_added, product_name=None, description=None, price=None, image=None):
        self.id = id
        self.accountid = accountid
        self.productid = productid
        self.time_added = time_added
        self.product_name = product_name
        self.description = description
        self.price = price
        self.image = image
        # Flag to denote if this item is already in the cart.
        self.in_cart = False

    @staticmethod
    def get(id):
        rows = app.db.execute('''
            SELECT w.id, w.accountid, w.productid, w.time_added,
                   p.name, p.description, p.price, p.image
            FROM Wishlist_2 w
            JOIN Products_2 p ON w.productid = p.id
            WHERE w.id = :id
        ''', id=id)
        return WishlistItem(*rows[0]) if rows else None

    @staticmethod
    def get_all_by_uid_since(accountid, since):
        rows = app.db.execute('''
            SELECT w.id, w.accountid, w.productid, w.time_added,
                   p.name, p.description, p.price, p.image
            FROM Wishlist_2 w
            JOIN Products_2 p ON w.productid = p.id
            WHERE w.accountid = :accountid
              AND w.time_added >= :since
            ORDER BY w.time_added DESC
        ''', accountid=accountid, since=since)
        return [WishlistItem(*row) for row in rows]

    @staticmethod
    def insert_object(accountid, productid, time_added):
        try:
            rows = app.db.execute("""
                INSERT INTO Wishlist_2(accountid, productid, time_added)
                VALUES(:accountid, :productid, :time_added)
                RETURNING id
            """, accountid=accountid, productid=productid, time_added=time_added)
            new_id = rows[0][0]
            return WishlistItem.get(new_id)
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def remove_object(wishlist_id):
        try:
            app.db.execute('DELETE FROM Wishlist_2 WHERE id = :id', id=wishlist_id)
            return True
        except Exception as e:
            print(str(e))
            return False
