from flask import current_app as app


class Purchase:
    def __init__(self, id, accountid, total, time_purchased, addressid):
        self.id = id
        self.accountid = accountid
        self.total = total
        self.time_purchased = time_purchased
        self.addressid = addressid

    @staticmethod
    def get(id):
        rows = app.db.execute('''
            SELECT id, accountid, total, time_purchased, addressid
            FROM Purchases_2
            WHERE id = :id
        ''', id=id)
        return Purchase(*(rows[0])) if rows else None
    
    @staticmethod
    def get_all_by_accountid_since(accountid, since):
        rows = app.db.execute('''
SELECT id, accountid, total, time_purchased, addressid
FROM Purchases_2
WHERE accountid = :accountid
AND time_purchased >= :since
ORDER BY time_purchased ASC
''',
                              accountid=accountid,
                              since=since)
        return [Purchase(*row) for row in rows]
    
    @staticmethod
    def get_all_by_accountid(accountid):
        rows = app.db.execute('''
SELECT id, accountid, total, time_purchased, addressid
FROM Purchases_2
WHERE accountid = :accountid
''',
                              accountid=accountid)
        return [Purchase(*row) for row in rows]
    @staticmethod
    def fulfilled_for(account_id):
        """
        Purchases where every line item already has a fulfillmenttimestamp.
        """
        rows = app.db.execute(
            '''
            SELECT p.id, p.accountid, p.total, p.time_purchased, p.addressid
            FROM Purchases_2 p
            WHERE p.accountid = :uid
              AND NOT EXISTS (
                    SELECT 1
                    FROM LineItem l
                    WHERE l.purchaseid = p.id
                      AND l.fulfillmenttimestamp IS NULL
              )
            ORDER BY p.time_purchased DESC
            ''',
            uid=account_id,
        )
        return [Purchase(*row) for row in rows]

    @staticmethod
    def in_process_for(account_id):
        """
        Purchases that still have at least one un-fulfilled line item.
        """
        rows = app.db.execute(
            '''
            SELECT DISTINCT p.id, p.accountid, p.total, p.time_purchased, p.addressid
            FROM Purchases_2 p
            JOIN LineItem l ON l.purchaseid = p.id
            WHERE p.accountid = :uid
              AND l.fulfillmenttimestamp IS NULL
            ORDER BY p.time_purchased DESC
            ''',
            uid=account_id,
        )
        return [Purchase(*row) for row in rows]