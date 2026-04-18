from flask import current_app as app, url_for


def image_url(image):
    """Render a product image reference.

    Absolute URLs (Vercel Blob uploads) are returned as-is; legacy static
    filenames fall through to Flask's static endpoint.
    """
    if not image:
        return ""
    if image.startswith("http://") or image.startswith("https://"):
        return image
    return url_for("static", filename=image)


def get_top3_images(purchase_id):
    """Return a list of up to 3 image filenames for the given purchase_id."""
    rows = app.db.execute('''
        SELECT p.image
        FROM LineItem li
        JOIN Products_2 p ON li.productid = p.id
        WHERE li.purchaseid = :purchase_id
        ORDER BY li.linenumber
        LIMIT 3
    ''', purchase_id=purchase_id)
    # Return only non-null images.
    return [row[0] for row in rows if row[0]]

def get_address(address_id):
    """Return an address object/dict for the given address_id."""
    rows = app.db.execute('''
        SELECT streetaddresslineone, streetaddresslinetwo, cityname, state, country, zipcode
        FROM Address
        WHERE id = :address_id
    ''', address_id=address_id)
    if rows:
        # You can return a simple dict.
        r = rows[0]
        return {
            'streetaddresslineone': r[0],
            'streetaddresslinetwo': r[1],
            'cityname': r[2],
            'state': r[3],
            'country': r[4],
            'zipcode': r[5]
        }
    return None