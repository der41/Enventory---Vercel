from flask import current_app as app

class Category:
    def __init__(self, id, category, subcategory):
        self.id = id
        self.category = category
        self.subcategory = subcategory

    @staticmethod
    def get_all_categories():
        rows = app.db.execute('''
            SELECT DISTINCT category
            FROM ProductCategories
            ORDER BY category
        ''')
        return [row[0] for row in rows]

    @staticmethod
    def get_subcategories_by_category(category_name):
        rows = app.db.execute('''
            SELECT id, category, subcategory
            FROM ProductCategories
            WHERE category = :category
            ORDER BY subcategory
        ''', category=category_name)
        return [Category(*row) for row in rows]

    @staticmethod
    def get_products_by_category(category_name):
        rows = app.db.execute('''
            SELECT p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image,
                COALESCE(SUM(li.qty), 0) AS total_purchased,
                ROUND(AVG(r.rating), 1) AS avg_rating,
                COUNT(r.rating) AS num_reviews
            FROM Products_2 p
            JOIN ProductCategories pc ON p.categoryid = pc.id
            LEFT JOIN LineItem li ON p.id = li.productid
            LEFT JOIN Product_Reviews r ON p.id = r.productid
            WHERE pc.category = :category AND p.status = TRUE
            GROUP BY p.id
        ''', category=category_name)
        
        from .product_2 import Product_2
        return [Product_2(*row[:8], total_purchased=row[8], avg_rating=row[9], num_reviews=row[10]) for row in rows]

