import os
from werkzeug.utils import secure_filename


def upload_product_image(file_storage, product_name: str) -> str:
    """Upload a product image to Vercel Blob and return its public URL.

    Requires the BLOB_READ_WRITE_TOKEN environment variable (injected
    automatically by Vercel when a Blob store is attached to the project).
    """
    import vercel_blob

    filename = secure_filename(f"{product_name}.png")
    data = file_storage.read()
    result = vercel_blob.put(f"products/{filename}", data, {"addRandomSuffix": "true"})
    return result["url"]
