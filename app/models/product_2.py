from flask import current_app as app


class Product_2:
    def __init__(self, id, name, description, sellerid, price, categoryid, status,image,sellername=None, total_purchased=None, avg_rating=None, num_reviews=None):
        self.id = id
        self.name = name
        self.description = description
        self.sellerid = sellerid
        self.price = price
        self.categoryid = categoryid
        self.status = status
        self.image = image
        self.sellername=sellername #optional argument, to show seller name in product details
        self.total_purchased = total_purchased # optional arg, for showing total number of product purchased in the listing
        self.avg_rating = avg_rating #to show little stars on the product cards in index.html
        self.num_reviews = num_reviews #again putting here for product card

    @staticmethod
    def get(id):
        rows = app.db.execute('''
            SELECT id, name, description, sellerid, price, categoryid, status,image
            FROM Products_2
            WHERE id = :id
        ''', id=id)
        return Product_2(*rows[0]) if rows else None

    @staticmethod
    def get_total_purchased_by_id(product_id):
        rows = app.db.execute('''
            SELECT COUNT(*) 
            FROM LineItem 
            WHERE productid = :product_id
        ''', product_id=product_id)
        
        return rows[0][0] if rows else 0

    @staticmethod
    def get_all(status=True):
        rows = app.db.execute('''
            SELECT 
                p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image,
                COALESCE(li_summary.total_qty, 0) AS total_purchased,
                ROUND(AVG(r.rating), 1) AS avg_rating,
                COUNT(r.rating) AS num_reviews
            FROM Products_2 p
            LEFT JOIN (
                SELECT productid, SUM(qty) AS total_qty
                FROM LineItem
                GROUP BY productid
            ) li_summary ON p.id = li_summary.productid
            LEFT JOIN Product_Reviews r ON p.id = r.productid 
            WHERE p.status = :status
            GROUP BY p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image, li_summary.total_qty
        ''', status=status)

        return [
            Product_2(*row[:8], total_purchased=row[8], avg_rating=row[9], num_reviews=row[10])
            for row in rows
        ]



    #KH: adding in for milestone 2 requirement
    @staticmethod
    def get_top_k_expensive(k, status=True):
        k = int(k)
        query = f'''
            SELECT p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image,
                COALESCE(SUM(li.qty), 0) AS total_purchased,
                ROUND(AVG(r.rating), 1) AS avg_rating,
                COUNT(r.rating) AS num_reviews
            FROM Products_2 p
            LEFT JOIN LineItem li ON p.id = li.productid
            LEFT JOIN Product_Reviews r ON p.id = r.productid
            WHERE p.status = :status
            GROUP BY p.id
            ORDER BY price DESC
            LIMIT {k}
        '''
        rows = app.db.execute(query, status=status)
        return [Product_2(*row[:8], total_purchased=row[8], avg_rating=row[9], num_reviews=row[10]) for row in rows]

    # KH: want to include seller id to show sellername on product detail page
    #   but making a new method instead of using get() method above
    #   just to make sure it doesnt break index.html
    # EOR: pdating this linek to get corrected path and get seller profile to show up 
    @staticmethod
    def get_with_seller(id):
        rows = app.db.execute('''
            SELECT p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image,
                a.username AS sellername,
                COALESCE(SUM(li.qty), 0) AS total_purchased
            FROM Products_2 p
            JOIN Accounts a ON p.sellerid = a.id
            LEFT JOIN LineItem li ON p.id = li.productid
            WHERE p.id = :id
            GROUP BY p.id, a.username
        ''', id=id)
        return Product_2(*rows[0]) if rows else None


    @staticmethod
    def get_by_category_ids(category_ids):
        if not category_ids:
            return []
        placeholder = ','.join([f":id{i}" for i in range(len(category_ids))])
        query = f"""
            SELECT id, name, description, sellerid, price, categoryid, status, image
            FROM Products_2
            WHERE categoryid IN ({placeholder})
        """
        params = {f"id{i}": cid for i, cid in enumerate(category_ids)}
        rows = app.db.execute(query, **params)
        return [Product_2(*row) for row in rows]


    # wanted to add the ability to sort by popularity 
    # popularity defined as most frequently purchases
    @staticmethod
    def get_all_sorted_by_popularity():
        rows = app.db.execute('''
            SELECT 
                p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image,
                COALESCE(li_summary.total_qty, 0) AS total_purchased,
                ROUND(AVG(r.rating), 1) AS avg_rating,
                COUNT(r.rating) AS num_reviews
            FROM Products_2 p
            LEFT JOIN (
                SELECT productid, SUM(qty) AS total_qty
                FROM LineItem
                GROUP BY productid
            ) li_summary ON p.id = li_summary.productid
            LEFT JOIN Product_Reviews r ON p.id = r.productid
            WHERE p.status = TRUE
            GROUP BY p.id, p.name, p.description, p.sellerid, p.price, p.categoryid, p.status, p.image, li_summary.total_qty
            ORDER BY total_purchased DESC
        ''')
        return [
            Product_2(*row[:8], total_purchased=row[8], avg_rating=row[9], num_reviews=row[10])
            for row in rows
        ]


    # for product recommendations on product details page
    @staticmethod
    def get_also_bought(product_id):
        rows = app.db.execute('''
            SELECT p.id, p.name, p.image, p.price, COUNT(*) AS freq
            FROM LineItem li1
            JOIN LineItem li2 ON li1.purchaseid = li2.purchaseid AND li1.productid != li2.productid
            JOIN Products_2 p ON li2.productid = p.id
            WHERE li1.productid = :product_id
            GROUP BY p.id, p.name, p.image, p.price
            ORDER BY freq DESC
            LIMIT 4
        ''', product_id=product_id)

        return [Product_2(id=row[0], name=row[1], image=row[2], price=row[3],
                        description=None, sellerid=None, categoryid=None,
                        status=True) for row in rows]


