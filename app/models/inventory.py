from flask import current_app as app

class Inventory:
    @staticmethod
    def get_full_inventory_by_seller(seller_id):
        return app.db.execute("""
            SELECT p.id, p.name, p.description, i.qtyavailable, i.qtyinstock, i.qtyinprocess, i.timeadded, p.image
            FROM Inventory i
            JOIN Products_2 p ON i.productid = p.id
            WHERE i.sellerid = :seller_id AND p.status = TRUE
        """, seller_id=seller_id)

    @staticmethod
    def soft_delete_product(product_id, seller_id):
        return app.db.execute("""
            UPDATE Products_2
            SET status = FALSE
            WHERE id = :product_id AND sellerid = :seller_id
        """, product_id=product_id, seller_id=seller_id)

    @staticmethod
    def get_product_details(product_id, seller_id):
        rows = app.db.execute("""
            SELECT p.id, p.name, p.description, p.price, p.status, pc.category, pc.subcategory
            FROM Products_2 p
            JOIN ProductCategories pc ON p.categoryid = pc.id
            WHERE p.id = :product_id AND p.sellerid = :seller_id
        """, product_id=product_id, seller_id=seller_id)
        if rows:
            row = rows[0]
            return {
                'id': row[0], 'name': row[1], 'description': row[2],
                'price': row[3], 'status': row[4], 'category': row[5], 'subcategory': row[6]
            }
        return None

    @staticmethod
    def update_product_details(product_id, name, description, price, category_id, status):
        return app.db.execute("""
            UPDATE Products_2
            SET name = :name, description = :description, price = :price,
                categoryid = :category_id, status = :status
            WHERE id = :product_id
        """, name=name, description=description, price=price,
              category_id=category_id, status=status, product_id=product_id)

    @staticmethod
    def update_inventory_timestamp(product_id, seller_id):
        return app.db.execute("""
            UPDATE Inventory
            SET timeadded = current_timestamp AT TIME ZONE 'UTC'
            WHERE productid = :product_id AND sellerid = :seller_id
        """, product_id=product_id, seller_id=seller_id)

    @staticmethod
    def get_inventory_item(product_id, seller_id):
        rows = app.db.execute("""
            SELECT qtyavailable, qtyinstock, qtyinprocess
            FROM Inventory
            WHERE productid = :product_id AND sellerid = :seller_id
        """, product_id=product_id, seller_id=seller_id)
        if rows:
            row = rows[0]
            return {'qtyavailable': row[0], 'qtyinstock': row[1], 'qtyinprocess': row[2]}
        return None

    @staticmethod
    def get_product_name(product_id):
        rows = app.db.execute("""
            SELECT name FROM Products_2 WHERE id = :product_id
        """, product_id=product_id)
        return {'name': rows[0][0]} if rows else {'name': ''}

    @staticmethod
    def modify_quantity(product_id, seller_id, quantity, action):
        if action == 'add':
            return app.db.execute("""
                UPDATE Inventory
                SET qtyinstock = qtyinstock + :qty,
                    qtyavailable = qtyavailable + :qty
                WHERE productid = :product_id AND sellerid = :seller_id
            """, qty=quantity, product_id=product_id, seller_id=seller_id)
        elif action == 'remove':
            return app.db.execute("""
                UPDATE Inventory
                SET qtyinstock = GREATEST(qtyinstock - :qty, qtyinprocess),
                    qtyavailable = GREATEST(qtyavailable - :qty, 0)
                WHERE productid = :product_id AND sellerid = :seller_id
            """, qty=quantity, product_id=product_id, seller_id=seller_id)

    @staticmethod
    def get_seller_id_from_account(account_id):
        rows = app.db.execute("""
            SELECT sellerid FROM Accounts
            WHERE id = :account_id AND sellerid IS NOT NULL
        """, account_id=account_id)
        return rows[0][0] if rows else None

    @staticmethod
    def add_or_get_category(category, subcategory):
        rows = app.db.execute("""
            SELECT id FROM ProductCategories
            WHERE category = :category AND subcategory = :subcategory
        """, category=category, subcategory=subcategory)

        if rows:
            return rows[0][0]
        else:
            result = app.db.execute("""
                INSERT INTO ProductCategories (category, subcategory)
                VALUES (:category, :subcategory)
                RETURNING id
            """, category=category, subcategory=subcategory)
            return result[0][0]

    @staticmethod
    def set_image_path(product_id, image_path):
        return app.db.execute("""
            UPDATE Products_2
            SET image = :image_path
            WHERE id = :product_id
        """, image_path=image_path, product_id=product_id)

    @staticmethod
    def get_all_categories():
        rows = app.db.execute("SELECT DISTINCT category FROM ProductCategories")
        return [row[0] for row in rows]

    @staticmethod
    def get_all_subcategories():
        rows = app.db.execute("SELECT DISTINCT subcategory FROM ProductCategories")
        return [row[0] for row in rows]

    @staticmethod
    def add_product(name, description, seller_id, price, category_id):
        result = app.db.execute("""
            INSERT INTO Products_2 (name, description, sellerid, price, categoryid, status)
            VALUES (:name, :description, :sellerid, :price, :categoryid, TRUE)
            RETURNING id
        """, name=name, description=description, sellerid=seller_id,
              price=price, categoryid=category_id)
        return result[0][0]

    @staticmethod
    def add_to_inventory(product_id, seller_id, quantity):
        return app.db.execute("""
            INSERT INTO Inventory (productid, sellerid, qtyinstock, qtyinprocess, qtyavailable)
            VALUES (:product_id, :seller_id, :qty, 0, :qty)
        """, product_id=product_id, seller_id=seller_id, qty=quantity)
