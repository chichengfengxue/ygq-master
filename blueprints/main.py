from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, abort, Blueprint
from flask_login import login_required, current_user
from sqlalchemy.sql.expression import func

from ..decorators import confirm_required, permission_required
from ..extensions import db
from ..forms.shop import DescriptionForm, TagForm
from ..forms.main import CommentForm
from ..models import User, Order, Dish, Tag, Follow, Collect, Comment, Notification
from ..utils import redirect_back, flash_errors

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['YGQ_DISH_PER_PAGE']
    pagination = Dish.query.order_by(Dish.sales.desc()).paginate(page, per_page)
    dishes = pagination.items
    tags = Tag.query.join(Tag.dishes).group_by(Tag.id).order_by(func.count(Dish.id).desc()).limit(10)
    return render_template('main/index.html', pagination=pagination, dishes=dishes, tags=tags)


@main_bp.route('/explore')
def explore():
    dishes = Dish.query.order_by(func.random()).limit(12)
    return render_template('main/explore.html', dishes=dishes)


@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        flash('Enter keyword about dish, user or tag.', 'warning')
        return redirect_back()

    category = request.args.get('category', 'dish')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['YGQ_SEARCH_RESULT_PER_PAGE']
    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    elif category == 'tag':
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    else:
        pagination = Dish.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items
    return render_template('main/search.html', q=q, results=results, pagination=pagination, category=category)


@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['YGQ_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['YGQ_UPLOAD_PATH'], filename)


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/dish/<int:dish_id>')
def show_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['YGQ_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(dish).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()

    description_form.description.data = dish.description
    return render_template('main/dish.html', dish=dish, comment_form=comment_form,
                           description_form=description_form, tag_form=tag_form,
                           pagination=pagination, comments=comments)


@main_bp.route('/collect/<int:dish_id>', methods=['POST'])
@login_required
@confirm_required
def collect(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    if current_user.is_collecting(dish):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_dish', dish_id=dish_id))

    current_user.collect(dish)
    flash('Photo collected.', 'success')
    return redirect(url_for('.show_dish', dish_id=dish_id))


@main_bp.route('/uncollect/<int:dish_id>', methods=['POST'])
@login_required
def uncollect(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    if not current_user.is_collecting(dish):
        flash('Not collect yet.', 'info')
        return redirect(url_for('.show_dish', dish_id=dish_id))

    current_user.uncollect(dish)
    flash('Dish uncollected.', 'info')
    return redirect(url_for('.show_dish', dish_id=dish_id))


@main_bp.route('/dish/<int:dish_id>/description', methods=['POST'])
@login_required
def edit_description(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    if current_user != dish.shop.user:
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        dish.description = form.description.data
        db.session.commit()
        flash('Description updated.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_dish', dish_id=dish_id))


@main_bp.route('/dish/<int:dish_id>/comment/new', methods=['POST'])
@login_required
def new_comment(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, dish=dish)
        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_dish', dish_id=dish_id, page=page))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_dish', dish_id=comment.dish_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')


@main_bp.route('/delete/dish/<int:dish_id>', methods=['POST'])
@login_required
def delete_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    if current_user != dish.shop.user:
        abort(403)

    db.session.delete(dish)
    db.session.commit()
    flash('Photo deleted.', 'info')
    return redirect(url_for('shop.index', username=dish.user.username))


@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['YGQ_DISH_PER_PAGE']
    order_rule = 'time'
    pagination = Dish.query.with_parent(tag).order_by(Dish.timestamp.desc()).paginate(page, per_page)
    dishes = pagination.items

    if order == 'by_collects':
        dishes.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/tag.html', tag=tag, pagination=pagination, dishes=dishes, order_rule=order_rule)
