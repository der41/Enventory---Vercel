from flask import Flask
from flask_login import LoginManager
from .config import Config
from .db import DB
from .tools import get_top3_images, get_address, image_url

login = LoginManager()
login.login_view = 'accounts.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.db = DB(app)
    login.init_app(app)

    from .index import bp as index_bp
    app.register_blueprint(index_bp)

    from .accounts import bp as accounts_bp
    app.register_blueprint(accounts_bp)

    from .wishlist_2 import bp as wishlist_bp
    app.register_blueprint(wishlist_bp)

    from .cart import bp as cart_bp
    app.register_blueprint(cart_bp)

    from .inventory import bp as inventory_bp
    app.register_blueprint(inventory_bp)

    from .reviews import bp as reviews_bp
    app.register_blueprint(reviews_bp)

    from .event_routes import bp as events_bp
    app.register_blueprint(events_bp)

    from .product_routes import bp as product_2_bp
    app.register_blueprint(product_2_bp)

    from app.category_routes import bp as category_bp
    app.register_blueprint(category_bp)

    from .purchase_2 import bp as purchase_bp
    app.register_blueprint(purchase_bp)

    from .orderfulfillment import bp as orderfulfillment_bp
    app.register_blueprint(orderfulfillment_bp)

    from app.review_routes import bp as review_bp
    app.register_blueprint(review_bp, url_prefix='/review')

    from .chatbot import bp as chatbot_bp
    app.register_blueprint(chatbot_bp)
    
    from .analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp)

    from .product_search import bp as product_search_bp
    app.register_blueprint(product_search_bp)


    @app.context_processor
    def utility_processor():
        return dict(get_top3_images=get_top3_images, get_address=get_address, image_url=image_url)

    from flask_login import current_user

    @app.context_processor
    def inject_account():
        if current_user.is_authenticated:
            return {'account': current_user}
        return {}

    return app
