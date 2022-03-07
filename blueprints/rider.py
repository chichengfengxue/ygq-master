from flask import render_template, redirect, url_for, current_app, request, Blueprint, abort, flash
from flask_login import login_required, current_user

from ..decorators import confirm_required
from ..models import User, Rider, Order


rider_bp = Blueprint('rider', __name__)


@rider_bp.route('/<int:rider_id>', methods=['GET'])
def index(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['YGQ_DISH_PER_PAGE']
    pagination = Order.query.with_parent(rider).order_by(Order.start_time.desc()).paginate(page, per_page)
    orders = pagination.items
    return render_template('rider/index.html', rider=rider, pagination=pagination, orders=orders)


@rider_bp.route('/active/<int:rider_id>', methods=['POST'])
@login_required
@confirm_required
def active(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    if current_user != rider.user:
        abort(403)
    if not rider.active:
        rider.to_active()
        flash('Active!', 'info')
    return redirect(url_for('.index', rider_id=rider.id))


@rider_bp.route('/inactive/<int:rider_id>', methods=['POST'])
@login_required
@confirm_required
def inactive(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    if current_user != rider.user:
        abort(403)
    if rider.active:
        rider.to_inactive()
        flash('Inactive!', 'info')
    return redirect(url_for('.index', rider_id=rider.id))