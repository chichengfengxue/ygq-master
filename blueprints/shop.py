import os

from flask import render_template, flash, redirect, url_for, current_app, request, Blueprint, abort
from flask_login import login_required, current_user

from ..decorators import confirm_required
from ..extensions import db
from ..forms.shop import DishForm, Apply2Shop, TagForm
from ..models import User, Dish, Shop, File, Tag
from ..utils import redirect_back, rename_file, flash_errors, is_image

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/<int:shop_id>')
def index(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['YGQ_DISH_PER_PAGE']
    pagination = Dish.query.with_parent(shop).order_by(Dish.timestamp.desc()).paginate(page, per_page)
    dishes = pagination.items
    return render_template('shop/index.html', shop=shop, pagination=pagination, dishes=dishes)


@shop_bp.route('/apply/<username>', methods=['GET', 'POST'])
@login_required
@confirm_required
def apply2shop(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user != user:
        abort(403)
    if user.shops:
        return redirect(url_for('.index', shop_id=user.shops[0].id))

    form = Apply2Shop()
    if form.validate_on_submit():
        name = form.name.data
        location_x = form.location_x.data
        location_y = form.location_y.data
        tel = form.tel.data
        shop = Shop(
            location_x=location_x,
            location_y=location_y,
            name=name,
            tel=tel,
            user=user
        )
        db.session.add(shop)
        db.session.commit()
        flash('Shop published.', 'success')
        return redirect(url_for('.index', shop_id=shop.id))

    return render_template('shop/apply_shop.html', form=form)


@shop_bp.route('/delete/dish/<int:dish_id>', methods=['POST'])
@login_required
def delete_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    if current_user != dish.shop.user:
        abort(403)
    db.session.delete(dish)
    db.session.commit()
    flash('Dish deleted.', 'info')
    return redirect_back()


@shop_bp.route('/upload/<int:shop_id>', methods=['GET', 'POST'])
@login_required
@confirm_required
def upload(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if request.method == 'POST' and 'file' in request.files:
        f = request.files.get('file')
        filename = rename_file(f.filename)
        f.save(os.path.join(current_app.config['YGQ_UPLOAD_PATH'], filename))
        file = File(
            filename=filename,
            user=shop.user,
            is_img=is_image(os.path.join(current_app.config['YGQ_UPLOAD_PATH'], filename))
        )
        db.session.add(file)
        db.session.commit()
    return redirect_back()


@shop_bp.route('/shop/<int:shop_id>/dish/new', methods=['GET', 'POST'])
@login_required
def new_dish(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    form = DishForm()

    if form.validate_on_submit():
        dish = Dish(
            price=form.price.data,
            description=form.description.data,
            shop=shop,
            name=form.name.data
        )
        db.session.add(dish)
        db.session.commit()
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in dish.tags:
                dish.tags.append(tag)
                db.session.commit()

        files = File.query.filter_by(is_use=False)
        for file in files:
            file.dish = dish
            file.is_use = True
        db.session.commit()
        flash('Dish published.', 'success')
        return redirect(url_for('main.show_dish', dish_id=dish.id))

    return render_template('shop/new_dish.html', form=form, shop=shop)


@shop_bp.route('/dish/<int:dish_id>/tag/new', methods=['POST'])
@login_required
def new_tag(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    if current_user != dish.shop.user:
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in dish.tags:
                dish.tags.append(tag)
                db.session.commit()
        flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('main.show_dish', dish_id=dish_id))


@shop_bp.route('/delete/tag/<int:dish_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(dish_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    dish = Dish.query.get_or_404(dish_id)
    if current_user != dish.shop.user:
        abort(403)
    dish.tags.remove(tag)
    db.session.commit()

    if not tag.dishes:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('main.show_dish', dish_id=dish_id))