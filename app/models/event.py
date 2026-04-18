from flask import current_app as app
from app.models.product_2 import Product_2


class Event:
    def __init__(self, name, type=None, categoryid=None):
        self.name = name
        self.type = type
        self.categoryid = categoryid

    @staticmethod
    def get_all():
        rows = app.db.execute("""
            SELECT DISTINCT name
            FROM Events
        """)
        return [Event(*row) for row in rows]

    @staticmethod
    def get_categoryids_by_event_name(event_name):
        rows = app.db.execute("""
            SELECT DISTINCT categoryid
            FROM Events
            WHERE name = :event_name
        """, event_name=event_name)
        return [row[0] for row in rows]

    @staticmethod
    def get_products_by_event(event_name):
        rows = app.db.execute('''
            SELECT p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image,
                COALESCE(SUM(li.qty), 0) AS total_purchased,
                ROUND(AVG(r.rating), 1) AS avg_rating,
                COUNT(r.rating) AS num_reviews
            FROM Products_2 p
            JOIN Events e ON p.categoryid = e.categoryid
            LEFT JOIN LineItem li ON li.productid = p.id
            LEFT JOIN Product_Reviews r ON r.productid = p.id
            WHERE e.name = :event_name AND p.status = TRUE
            GROUP BY p.id
        ''', event_name=event_name)

        return [Product_2(*row[:8], total_purchased=row[8], avg_rating=row[9], num_reviews=row[10]) for row in rows]

    from flask import current_app as app

    @staticmethod
    def get_event_by_product_id(product_id):
        rows = app.db.execute('''
            SELECT DISTINCT e.name
            FROM Events e
            JOIN ProductCategories pc ON e.categoryid = pc.id
            JOIN Products_2 p ON p.categoryid = pc.id
            WHERE p.id = :product_id
        ''', product_id=product_id)

        return [row[0] for row in rows]  # Return list of event names

