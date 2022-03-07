import os

import click
from flask import Flask, render_template
from flask_login import current_user
from flask_wtf.csrf import CSRFError

# from .blueprints.admin import admin_bp
# from .blueprints.ajax import ajax_bp
from .blueprints.auth import auth_bp
from .blueprints.main import main_bp
from .blueprints.rider import rider_bp
from .blueprints.shop import shop_bp
from .blueprints.user import user_bp
from .extensions import bootstrap, db, login_manager, mail, dropzone, moment, whooshee, avatars, csrf
# from .extensions import scheduler
from .models import User, Dish, Tag, Follow, Notification, Comment, Collect, Order, Rider, Shop, File
from .settings import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('ygq')
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errorhandlers(app)
    register_shell_context(app)
    register_template_context(app)

    return app


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    dropzone.init_app(app)
    moment.init_app(app)
    whooshee.init_app(app)
    avatars.init_app(app)
    csrf.init_app(app)
    # scheduler.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(rider_bp, url_prefix='/rider')
    app.register_blueprint(shop_bp, url_prefix='/shop')
    # app.register_blueprint(admin_bp, url_prefix='/admin')
    # app.register_blueprint(ajax_bp, url_prefix='/ajax')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Dish=Dish, Tag=Tag,
                    Follow=Follow, Collect=Collect, Comment=Comment,
                    Notification=Notification)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 500


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command()
    def init():
        click.echo('Initializing the database...')
        db.create_all()

        click.echo('Initializing the roles and permissions...')

        click.echo('Done.')

    @app.cli.command()
    @click.option('--user', default=10, help='Quantity of users, default is 10.')
    @click.option('--follow', default=30, help='Quantity of follows, default is 30.')
    @click.option('--tag', default=20, help='Quantity of tags, default is 20.')
    @click.option('--collect', default=50, help='Quantity of collects, default is 50.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 100.')
    @click.option('--dish', default=100, help='Quantity of dishes, default is 100.')
    @click.option('--order', default=100, help='Quantity of orders, default is 200.')
    @click.option('--shop', default=20, help='Quantity of shops, default is 20.')
    def forge(user, follow, tag, collect, comment, dish, order, shop):
        """Generate fake data."""

        from .fakes import fake_shop, fake_comment, fake_follow, fake_tag, fake_user, \
            fake_collect, fake_dish,fake_order

        db.drop_all()
        db.create_all()

        click.echo('Generating %d users...' % user)
        fake_user(user)
        click.echo('Generating %d shops...' % shop)
        fake_shop(shop)
        click.echo('Generating %d follows...' % follow)
        fake_follow(follow)
        click.echo('Generating %d tags...' % tag)
        fake_tag(tag)
        click.echo('Generating %d dishes...' % dish)
        fake_dish(dish)
        click.echo('Generating %d collects...' % collect)
        fake_collect(collect)
        click.echo('Generating %d comments...' % comment)
        fake_comment(comment)
        click.echo('Generating %d orders...' % order)
        fake_order(order)
        click.echo('Done.')
