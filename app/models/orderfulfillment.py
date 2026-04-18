# app/models/orderfulfillment.py
from flask import current_app as app

class OrderFulfillment:
    @staticmethod
    def get_seller_id(account_id):
        row = app.db.execute("""
            SELECT sellerid FROM Accounts
            WHERE id = :account_id AND sellerid IS NOT NULL
        """, account_id=account_id)
        return row[0][0] if row else None

    @staticmethod
    def get_lineitems_for_seller(seller_id):
        rows = app.db.execute("""
            SELECT li.id AS lineitem_id, li.linenumber, li.qty,
                   p.name AS product_name,
                   pur.id AS purchase_id, pur.time_purchased,
                   li.inprocesstimestamp, li.fulfillmenttimestamp
            FROM LineItem li
            JOIN Purchases_2 pur ON li.purchaseid = pur.id
            JOIN Products_2 p ON li.productid = p.id
            WHERE li.sellerid = :seller_id
            ORDER BY pur.time_purchased DESC
        """, seller_id=seller_id)

        result = []
        for row in rows:
            status = "Received"
            if row.fulfillmenttimestamp:
                status = "Closed"
            elif row.inprocesstimestamp:
                status = "Pending Fulfillment"

            result.append({
                'lineitem_id': row.lineitem_id,
                'linenumber': row.linenumber,
                'qty': row.qty,
                'product_name': row.product_name,
                'purchase_id': row.purchase_id,
                'time_purchased': row.time_purchased,
                'inprocesstimestamp': row.inprocesstimestamp,
                'fulfillmenttimestamp': row.fulfillmenttimestamp,
                'status': status
            })

        return result

    @staticmethod
    def get_lineitem_details(lineitem_id, seller_id):
        rows = app.db.execute("""
            SELECT li.id AS lineitem_id, li.linenumber, li.qty, p.name AS product_name,
                   pur.time_purchased, li.inprocesstimestamp, li.fulfillmenttimestamp,
                   a.streetaddresslineone, a.streetaddresslinetwo, a.cityname,
                   a.state, a.country, a.zipcode
            FROM LineItem li
            JOIN Purchases_2 pur ON li.purchaseid = pur.id
            JOIN Products_2 p ON li.productid = p.id
            JOIN Address a ON pur.addressid = a.id
            WHERE li.id = :lineitem_id AND li.sellerid = :seller_id
        """, lineitem_id=lineitem_id, seller_id=seller_id)

        if not rows:
            return None

        row = rows[0]
        status = "Received"
        if row.fulfillmenttimestamp:
            status = "Closed"
        elif row.inprocesstimestamp:
            status = "Pending Fulfillment"

        address = f"{row.streetaddresslineone}"
        if row.streetaddresslinetwo:
            address += f", {row.streetaddresslinetwo}"
        address += f", {row.cityname}, {row.state}, {row.country}, {row.zipcode}"

        return {
            'lineitem_id': row.lineitem_id,
            'linenumber': row.linenumber,
            'qty': row.qty,
            'product_name': row.product_name,
            'time_purchased': row.time_purchased,
            'inprocesstimestamp': row.inprocesstimestamp,
            'fulfillmenttimestamp': row.fulfillmenttimestamp,
            'address': address,
            'status': status
        }

    @staticmethod
    def set_inprocess(lineitem_id, timestamp):
        app.db.execute("""
            UPDATE LineItem
            SET inprocesstimestamp = :timestamp
            WHERE id = :lineitem_id
        """, timestamp=timestamp, lineitem_id=lineitem_id)

    @staticmethod
    def set_fulfilled(lineitem_id, timestamp):
        app.db.execute("""
            UPDATE LineItem
            SET fulfillmenttimestamp = :timestamp
            WHERE id = :lineitem_id
        """, timestamp=timestamp, lineitem_id=lineitem_id)
