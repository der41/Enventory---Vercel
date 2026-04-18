# app/models/cart.py
from flask import current_app as app

class CartItem:
    def __init__(self, id, accountid, productid, quantity, product_name=None, price=None, image=None, total_price=None):
        self.id = id
        self.accountid = accountid
        self.productid = productid
        self.quantity = quantity
        self.product_name = product_name
        self.price = price
        self.image = image
        self.total_price = total_price

    @staticmethod
    def get(id):
        rows = app.db.execute('''
            SELECT c.id, c.accountid, c.productid, c.quantity,
                   p.name AS product_name, p.price, p.image,
                   (c.quantity * p.price) AS total_price
            FROM Cart c 
            JOIN Products_2 p ON c.productid = p.id
            WHERE c.id = :id
        ''', id=id)
        return CartItem(*rows[0]) if rows else None

    @staticmethod
    def get_all_by_account(accountid):
        rows = app.db.execute('''
            SELECT c.id, c.accountid, c.productid, c.quantity,
                   p.name AS product_name, p.price, p.image,
                   (c.quantity * p.price) AS total_price
            FROM Cart c 
            JOIN Products_2 p ON c.productid = p.id
            WHERE c.accountid = :accountid
        ''', accountid=accountid)
        return [CartItem(*row) for row in rows]

    @staticmethod
    def insert_object(accountid, productid, quantity):
        try:
            existing = app.db.execute('''
                SELECT id, quantity FROM Cart
                WHERE accountid = :accountid AND productid = :productid
            ''', accountid=accountid, productid=productid)
            if existing:
                current_qty = existing[0][1]
                new_qty = current_qty + quantity
                app.db.execute('''
                    UPDATE Cart
                    SET quantity = :new_qty
                    WHERE id = :id
                ''', new_qty=new_qty, id=existing[0][0])
                return CartItem.get(existing[0][0])
            else:
                rows = app.db.execute('''
                    INSERT INTO Cart (accountid, productid, quantity)
                    VALUES (:accountid, :productid, :quantity)
                    RETURNING id
                ''', accountid=accountid, productid=productid, quantity=quantity)
                new_id = rows[0][0]
                return CartItem.get(new_id)
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def update_quantity(cart_id, delta):
        """Update the quantity by adding delta (which can be negative).
           If the resulting quantity is 0 or less, remove the cart item."""
        try:
            # Get the current item
            item = CartItem.get(cart_id)
            if not item:
                return None
            new_qty = item.quantity + delta
            if new_qty <= 0:
                # Remove the item
                app.db.execute('DELETE FROM Cart WHERE id = :id', id=cart_id)
                return None
            else:
                app.db.execute('''
                    UPDATE Cart
                    SET quantity = :new_qty
                    WHERE id = :id
                ''', new_qty=new_qty, id=cart_id)
                return CartItem.get(cart_id)
        except Exception as e:
            print(str(e))
            return None
        
    @staticmethod
    def add_with_inventory_check(accountid: int, productid: int, quantity: int):
        """
        Insert (or increase) a cart line only if the final quantity
        will not exceed the seller’s current qtyavailable.
        Returns the CartItem on success, or None on failure.
        """
        try:
            # What does the seller still have?
            inv = app.db.execute(
                '''
                SELECT qtyavailable
                FROM Inventory
                WHERE productid = :pid
                  AND sellerid = (SELECT sellerid FROM Products_2 WHERE id = :pid)
                ''',
                pid=productid,
            )
            if not inv:
                return None                       # no inventory row → block
            available = int(inv[0][0])

            # How many of this item are already in the buyer’s cart?
            existing = app.db.execute(
                '''
                SELECT id, quantity
                FROM Cart
                WHERE accountid = :uid AND productid = :pid
                ''',
                uid=accountid,
                pid=productid,
            )
            current_qty = existing[0][1] if existing else 0
            wanted_total = current_qty + quantity

            # Not enough stock?  Bail out.
            if wanted_total > available:
                return None

            # Enough stock – use the *existing* insert/update logic
            return CartItem.insert_object(accountid, productid, quantity)

        except Exception as e:
            print(e)
            return None
        
    @staticmethod
    def increment_with_inventory_check(cart_item_id):
        """
        Add one unit to an existing cart line *only* if inventory allows.
        Returns (CartItem, None) on success or (None, error-message) on failure.
        """
        try:
            # Current cart line
            item = CartItem.get(cart_item_id)
            if not item:
                return None, "Cart item not found."

            # What’s left in stock for this product?
            inv = app.db.execute(
                '''
                SELECT qtyavailable
                FROM Inventory
                WHERE productid = :pid
                  AND sellerid = (SELECT sellerid
                                  FROM Products_2
                                  WHERE id = :pid)
                ''',
                pid=item.productid,
            )
            if not inv:
                return None, "Inventory record missing."

            available = int(inv[0][0])

            if item.quantity + 1 > available:
                return None, f"Only {available} left in stock."

            # Safe to increment
            app.db.execute(
                '''
                UPDATE Cart
                SET quantity = quantity + 1
                WHERE id = :cid
                ''',
                cid=cart_item_id,
            )
            return CartItem.get(cart_item_id), None

        except Exception as e:
            print(e)
            return None, "Could not update quantity."