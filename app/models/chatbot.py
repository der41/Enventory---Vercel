# app/models/chatbot.py
"""
Simple RAG assistant for Eventory **PLUS small action-commands**
(add to cart / wishlist / share link).

dependencies (pyproject.toml)
    langchain-google-genai>=0.1.0
    google-generativeai   >=0.3.0
"""

from __future__ import annotations

import os, re, unicodedata
from typing import List, Optional
from markupsafe import escape

from flask import current_app as app, url_for
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_community.vectorstores import FAISS


# ─────────────────────────  LLM initialisation  ──────────────────────────────
_chat_model: Optional[ChatGoogleGenerativeAI] = None
_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
_vector_store: Optional[FAISS] = None

VECTOR_INDEX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "vector_index",
)


def _require_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "Set env-var GOOGLE_API_KEY (get one at https://ai.google.dev)."
        )
    return key


def _get_chat_model() -> ChatGoogleGenerativeAI:
    global _chat_model
    if _chat_model is None:
        _chat_model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=_require_api_key(),
            temperature=0.3,
            max_output_tokens=1024,
        )
    return _chat_model


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _require_api_key()
        _embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return _embeddings


# ─────────────────────────  internal helpers  ────────────────────────────────

_EXTERNAL_URL_RE = re.compile(
    r"https?://(?:www\.)?eventory\.com/products/(?P<slug>[^/?#]+)",
    re.IGNORECASE,
)

def _rewrite_links(md: str) -> str:
    # Phase 1: external Eventory URLs → local markdown links
    def _external_to_local(m):
        slug = m.group("slug").lower()
        rows = app.db.execute(
            """
            SELECT id, name
              FROM Products_2
             WHERE lower(regexp_replace(name,'[^a-z0-9]+','-','g')) = :s
             LIMIT 1
            """,
            s=slug,
        )
        if not rows:
            return m.group(0)  # leave untouched
        pid, name = rows[0]
        local_url = url_for("product_2.product_detail", product_id=pid)
        return f"[{name}]({local_url})"

    text = _EXTERNAL_URL_RE.sub(_external_to_local, md)

    # Phase 2: wrap bullet-point names themselves
    #   turn "* Name - desc" into "* [Name](/product/id) - desc"
    BULLET_RE = re.compile(r"^\*\s*([^-\n]+?)\s*-\s*", re.MULTILINE)
    def _bullet_link(m):
        name = m.group(1).strip()
        rows = app.db.execute(
            "SELECT id FROM Products_2 WHERE name = :n LIMIT 1",
            n=name,
        )
        if not rows:
            return m.group(0)
        pid = rows[0][0]
        local_url = url_for("product_2.product_detail", product_id=pid)
        return f"* [{name}]({local_url}) - "

    return BULLET_RE.sub(_bullet_link, text)

#give a short overview of the cart
def _get_cart_overview(uid: int) -> str:
    rows = app.db.execute(
        """
        SELECT p.name, c.quantity
        FROM Cart c
        JOIN Products_2 p ON p.id = c.productid
        WHERE c.accountid = :uid
        LIMIT 8
        """,
        uid=uid,
    )
    return "Cart empty." if not rows else " | ".join(f"{n}×{q}" for n, q in rows)

#Check inventory for the product
def _check_inventory(pid: int) -> int | None:
    row = app.db.execute(
        """SELECT qtyavailable
           FROM Inventory
           WHERE productid=:pid
             AND sellerid=(SELECT sellerid FROM Products_2 WHERE id=:pid)""",
        pid=pid,
    )
    return int(row[0][0]) if row else None

# Load a pre-built FAISS index shipped in the repo (see scripts/build_vector_index.py).
def _ensure_vector_index() -> FAISS:
    global _vector_store
    if _vector_store is None:
        if not os.path.isdir(VECTOR_INDEX_DIR):
            raise RuntimeError(
                f"Vector index missing at {VECTOR_INDEX_DIR}. "
                "Run `python scripts/build_vector_index.py` locally and commit the result."
            )
        _vector_store = FAISS.load_local(
            VECTOR_INDEX_DIR,
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
    return _vector_store

# get the product id from the name or id
def _find_product(term: str) -> Optional[int]:
    """
    Accepts a product *id* or a name fragment. Returns the first matching id or None.
    """
    if term.isdigit():
        # does that id exist?
        rows = app.db.execute("SELECT 1 FROM Products_2 WHERE id=:pid", pid=int(term))
        if rows:
            return int(term)

    rows = app.db.execute(
        """
        SELECT id FROM Products_2
        WHERE lower(name) LIKE lower(:t)
        ORDER BY id LIMIT 1
        """,
        t=f"%{term}%",
    )
    return rows[0][0] if rows else None

@staticmethod
def _add_to_cart(uid: int, pid: int, qty: int = 1) -> None:
    # Try to find an existing row
    existing = app.db.execute(
        "SELECT quantity FROM Cart WHERE accountid = :uid AND productid = :pid",
        uid=uid, pid=pid
    )
    if existing:
        # update
        app.db.execute(
            """
            UPDATE Cart
               SET quantity = quantity + :q
             WHERE accountid = :uid
               AND productid = :pid
            """,
            uid=uid, pid=pid, q=qty
        )
    else:
        # insert fresh
        app.db.execute(
            """
            INSERT INTO Cart(accountid, productid, quantity)
            VALUES(:uid, :pid, :q)
            """,
            uid=uid, pid=pid, q=qty
        )

@staticmethod
def _add_to_wishlist(uid: int, pid: int) -> None:
    # Only insert if it doesn't already exist
    exists = app.db.execute(
        "SELECT 1 FROM Wishlist_2 WHERE accountid = :uid AND productid = :pid",
        uid=uid, pid=pid
    )
    if not exists:
        app.db.execute(
            """
            INSERT INTO Wishlist_2(accountid, productid)
            VALUES(:uid, :pid)
            """,
            uid=uid, pid=pid
        )


# ─────────────────────────  Gemini prompt  ───────────────────────────────────
SYSTEM_PROMPT = """
You are Eventory’s shopping assistant.
1. When you recommend products, simply list names & descriptions.
2. **If you need to give me a link**, output exactly (on its own line):
   
   share <Product Name>
   
   and do NOT write any URL yourself. I will handle that.
3. Prices are in USD.
4. if you add to cart or wishlist use the action add_cart or add_wish
"""

PROMPT_TMPL = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT + "\n\n{context}"),
    ("human", "{question}"),
])


# ─────────────────────────  main callable  ───────────────────────────────────
ACTION_PATTERNS = {
    "add_cart": re.compile(r"add\s+(.*?)\s+to\s+cart", re.I),
    "add_wish": re.compile(r"add\s+(.*?)\s+to\s+wishlist", re.I),
    "share": re.compile(r"share\s+(.*?)$", re.I),
}


def ask_bot(question: str, user_id: int | None = None) -> str:
    # 1 — quick “action” intents issued by the user directly
    for action, patt in ACTION_PATTERNS.items():
        m = patt.search(question)
        if m and user_id:
            target = m.group(1).strip()
            pid = _find_product(target)
            if not pid:
                return f"Sorry, I couldn’t find any product matching “{target}.”"
            inv = _check_inventory(pid)
            if inv is None or inv < 1:
                return "Sorry, there is no inventory available for this product."
            if action == "add_cart":
                _add_to_cart(user_id, pid)
                return "✅ Added to your cart."
            if action == "add_wish":
                _add_to_wishlist(user_id, pid)
                return "💖 Added to your wishlist."
            if action == "share":
                link = url_for("product_2.product_detail", product_id=pid, _external=True)
                return f"[Open product page]({link})"

    # 2 — RAG fallback
    ctx_parts = []
    if user_id:
        ctx_parts.append(f"Current cart: {_get_cart_overview(user_id)}")
    vs = _ensure_vector_index()
    retrieved = vs.similarity_search(question, k=3)
    if retrieved:
        snippets = "\n\n".join(doc.page_content.split("\n", 1)[1] for doc in retrieved)
        ctx_parts.append(f"Relevant products:\n{snippets}")
    context = "\n\n".join(ctx_parts) or "No extra context."

    raw = (PROMPT_TMPL | _get_chat_model() | StrOutputParser()).invoke({
        "context": context,
        "question": question
    }).strip()

    # 3 — post-process any instructions emitted by the LLM
    out_lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()

        # LLM asking us to add to cart:
        if stripped.lower().startswith("add_cart "):
            pname = stripped[len("add_cart "):].strip()
            pid = _find_product(pname)
            if pid and user_id:
                _add_to_cart(user_id, pid)
                out_lines.append(f"✅ Added **{pname}** to your cart.")
            else:
                out_lines.append(f"⚠️ Couldn’t find product “{pname}.”")

        # LLM asking us to add to wishlist:
        elif stripped.lower().startswith("add_wish "):
            pname = stripped[len("add_wish "):].strip()
            pid = _find_product(pname)
            if pid and user_id:
                _add_to_wishlist(user_id, pid)
                out_lines.append(f"💖 Added **{pname}** to your wishlist.")
            else:
                out_lines.append(f"⚠️ Couldn’t find product “{pname}.”")

        # LLM asking us to share a link:
        elif stripped.lower().startswith("share "):
            pname = stripped[len("share "):].strip()
            pid = _find_product(pname)
            if pid:
                link = url_for("product_2.product_detail", product_id=pid, _external=True)
                out_lines.append(f"[{pname}]({link})")
            else:
                out_lines.append(f"⚠️ Couldn’t find product “{pname}.”")

        # everything else just pass through
        else:
            out_lines.append(stripped)

    return "\n".join(out_lines)