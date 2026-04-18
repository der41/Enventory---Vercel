from flask import current_app as app

class Review:
    def __init__(self, id, review_type, target_id, accountid, comment, rating, time_submitted):
        self.id = id
        self.review_type = review_type  # 'product' or 'seller'
        self.target_id = target_id
        self.accountid = accountid      # 🆕 Added accountid
        self.comment = comment
        self.rating = rating
        self.time_submitted = time_submitted

    @staticmethod
    def get_recent_by_accountid(accountid, limit=5):
        rows = app.db.execute("""
            SELECT * FROM (
                SELECT id, 'product' AS review_type, productid AS target_id, accountid, comment, rating, time_submitted
                FROM Product_Reviews
                WHERE accountid = :accountid

                UNION ALL

                SELECT id, 'seller' AS review_type, sellerid AS target_id, accountid, comment, rating, time_submitted
                FROM Seller_Reviews
                WHERE accountid = :accountid
            ) AS all_reviews
            ORDER BY time_submitted DESC
            LIMIT :limit
        """, accountid=accountid, limit=limit)

        return [Review(*row) for row in rows]

    @staticmethod
    def get_by_productid(productid):
        rows = app.db.execute("""
            SELECT id, 'product' AS review_type, productid AS target_id, accountid, comment, rating, time_submitted
            FROM Product_Reviews
            WHERE productid = :productid
            ORDER BY time_submitted DESC
        """, productid=productid)

        return [Review(*row) for row in rows]

    @staticmethod
    def get(review_id):
        row = app.db.execute('''
            SELECT id, 'product' AS review_type, productid AS target_id, accountid, comment, rating, time_submitted
            FROM Product_Reviews
            WHERE id = :review_id

            UNION ALL

            SELECT id, 'seller' AS review_type, sellerid AS target_id, accountid, comment, rating, time_submitted
            FROM Seller_Reviews
            WHERE id = :review_id
        ''', review_id=review_id)

        if row:
            return Review(*row[0])
        else:
            return None

    @staticmethod
    def update(review_id, new_rating, new_comment):
        # Try updating Product_Reviews
        updated = app.db.execute('''
            UPDATE Product_Reviews
            SET rating = :new_rating, comment = :new_comment
            WHERE id = :review_id
            RETURNING id
        ''', new_rating=new_rating, new_comment=new_comment, review_id=review_id)

        if not updated:  # If not found in Product_Reviews, try Seller_Reviews
            app.db.execute('''
                UPDATE Seller_Reviews
                SET rating = :new_rating, comment = :new_comment
                WHERE id = :review_id
            ''', new_rating=new_rating, new_comment=new_comment, review_id=review_id)

    @staticmethod
    def delete(review_id):
        # Try deleting from Product_Reviews first
        deleted = app.db.execute('''
            DELETE FROM Product_Reviews
            WHERE id = :review_id
            RETURNING id
        ''', review_id=review_id)

        if not deleted:  # If not found in Product_Reviews, try Seller_Reviews
            app.db.execute('''
                DELETE FROM Seller_Reviews
                WHERE id = :review_id
            ''', review_id=review_id)
