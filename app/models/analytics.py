from flask import current_app as app

def get_sales_by_product(seller_id, start_date, end_date, date_filter):
    query = '''
    SELECT p.name, SUM(l.qty * p.price) AS total_sales
    FROM LineItem l
    JOIN Products_2 p ON l.productid = p.id
    JOIN Purchases_2 pu ON l.purchaseid = pu.id
    WHERE l.sellerid = :sid
    '''
    params = {'sid': seller_id}

    if start_date and end_date:
        query += ' AND pu.time_purchased BETWEEN :start AND :end'
        params.update({'start': start_date, 'end': end_date})
    else:
        if date_filter == 'YTD':
            query += " AND EXTRACT(YEAR FROM pu.time_purchased) = EXTRACT(YEAR FROM current_date)"
        elif date_filter == 'LastYear':
            query += " AND EXTRACT(YEAR FROM pu.time_purchased) = EXTRACT(YEAR FROM current_date) - 1"
        elif date_filter == 'ThisQuarter':
            query += " AND date_trunc('quarter', pu.time_purchased) = date_trunc('quarter', current_date)"

    query += ' GROUP BY p.name ORDER BY total_sales DESC'
    result = app.db.execute(query, **params)
    return [{'product': row[0], 'sales': float(row[1])} for row in result]

def get_monthly_sales_qty(seller_id, start_date, end_date, date_filter):
    query = '''
    SELECT DATE_TRUNC('month', pu.time_purchased) AS month, p.name, SUM(l.qty)
    FROM LineItem l
    JOIN Products_2 p ON l.productid = p.id
    JOIN Purchases_2 pu ON l.purchaseid = pu.id
    WHERE l.sellerid = :sid
    '''
    params = {'sid': seller_id}

    if start_date and end_date:
        query += ' AND pu.time_purchased BETWEEN :start AND :end'
        params.update({'start': start_date, 'end': end_date})
    else:
        if date_filter == 'YTD':
            query += " AND EXTRACT(YEAR FROM pu.time_purchased) = EXTRACT(YEAR FROM current_date)"
        elif date_filter == 'LastYear':
            query += " AND EXTRACT(YEAR FROM pu.time_purchased) = EXTRACT(YEAR FROM current_date) - 1"
        elif date_filter == 'ThisQuarter':
            query += " AND date_trunc('quarter', pu.time_purchased) = date_trunc('quarter', current_date)"

    query += ' GROUP BY month, p.name ORDER BY month'
    result = app.db.execute(query, **params)

    monthly_data = {}
    for row in result:
        month, product, qty = row
        month_str = month.strftime('%Y-%m')
        if month_str not in monthly_data:
            monthly_data[month_str] = {}
        monthly_data[month_str][product] = int(qty)
    return monthly_data

def get_monthly_avg_times(seller_id, start_date, end_date, date_filter):
    query = '''
    SELECT DATE_TRUNC('month', pu.time_purchased) AS month,
           AVG(EXTRACT(EPOCH FROM (l.fulfillmenttimestamp - pu.time_purchased)) / 86400) AS avg_fulfillment_days,
           AVG(EXTRACT(EPOCH FROM (l.fulfillmenttimestamp - l.inprocesstimestamp)) / 86400) AS avg_processing_days
    FROM LineItem l
    JOIN Purchases_2 pu ON l.purchaseid = pu.id
    WHERE l.sellerid = :sid
      AND pu.time_purchased IS NOT NULL
      AND l.fulfillmenttimestamp IS NOT NULL
      AND l.inprocesstimestamp IS NOT NULL
    '''
    params = {'sid': seller_id}

    if start_date and end_date:
        query += ' AND pu.time_purchased BETWEEN :start AND :end'
        params.update({'start': start_date, 'end': end_date})
    else:
        if date_filter == 'YTD':
            query += " AND EXTRACT(YEAR FROM pu.time_purchased) = EXTRACT(YEAR FROM current_date)"
        elif date_filter == 'LastYear':
            query += " AND EXTRACT(YEAR FROM pu.time_purchased) = EXTRACT(YEAR FROM current_date) - 1"
        elif date_filter == 'ThisQuarter':
            query += " AND date_trunc('quarter', pu.time_purchased) = date_trunc('quarter', current_date)"

    query += ' GROUP BY month ORDER BY month'
    result = app.db.execute(query, **params)

    monthly_data = []
    for row in result:
        month, avg_fulfillment, avg_processing = row
        monthly_data.append({
            'month': month.strftime('%Y-%m'),
            'avg_fulfillment_days': round(avg_fulfillment, 2) if avg_fulfillment is not None else None,
            'avg_processing_days': round(avg_processing, 2) if avg_processing is not None else None
        })
    return monthly_data

def get_zero_qty_products(seller_id):
    result = app.db.execute('''
        SELECT COUNT(*) FROM Inventory
        WHERE sellerid = :sid AND qtyavailable = 0
    ''', sid=seller_id)
    return result[0][0]

def get_unprocessed_orders(seller_id):
    result = app.db.execute('''
        SELECT COUNT(*) FROM LineItem l
        JOIN Purchases_2 pu ON l.purchaseid = pu.id
        WHERE l.sellerid = :sid AND l.inprocesstimestamp IS NULL
    ''', sid=seller_id)
    return result[0][0]

def get_inprocess_unfulfilled_orders(seller_id):
    result = app.db.execute('''
        SELECT COUNT(*) FROM LineItem l
        WHERE l.sellerid = :sid AND l.inprocesstimestamp IS NOT NULL AND l.fulfillmenttimestamp IS NULL
    ''', sid=seller_id)
    return result[0][0]
