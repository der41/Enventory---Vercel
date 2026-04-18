"""Rename product image files (and DB rows that reference them) to remove
spaces. Vercel's static file handler 404s on URL-encoded space paths, so
underscored filenames are the safest portable form.

Usage:
    export DATABASE_URL=postgresql://...
    python scripts/rename_image_files.py
"""
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = REPO_ROOT / "app" / "static" / "images"


def safe_name(name: str) -> str:
    return name.replace(" ", "_")


def main() -> int:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set.", file=sys.stderr)
        return 1

    renames: list[tuple[str, str]] = []
    for path in IMAGES_DIR.iterdir():
        if not path.is_file() or " " not in path.name:
            continue
        new_path = path.with_name(safe_name(path.name))
        if new_path.exists():
            print(f"SKIP {path.name} — target {new_path.name} already exists")
            continue
        path.rename(new_path)
        renames.append((path.name, new_path.name))
        print(f"renamed: {path.name}  →  {new_path.name}")

    if not renames:
        print("No files needed renaming.")
        return 0

    engine = create_engine(db_url)
    with engine.begin() as conn:
        for old_name, new_name in renames:
            old_ref = f"images/{old_name}"
            new_ref = f"images/{new_name}"
            res = conn.execute(
                text("UPDATE Products_2 SET image = :new WHERE image = :old"),
                {"old": old_ref, "new": new_ref},
            )
            if res.rowcount:
                print(f"DB updated for {old_name}: {res.rowcount} row(s)")

    print(f"Done. Renamed {len(renames)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
