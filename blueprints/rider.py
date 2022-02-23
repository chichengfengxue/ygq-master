from flask import render_template, redirect, url_for, current_app, request, Blueprint, abort
from flask_login import login_required, current_user

from ..decorators import confirm_required
from ..models import User, Rider, Order


rider_bp = Blueprint('rider', __name__)


@rider_bp.route('/<username>', methods=['GET'])
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Order.query.with_parent(user.rider).order_by(Order.timestamp.desc()).paginate(page, per_page)
    orders = pagination.items
    return render_template('rider/index.html', rider=user.rider, pagination=pagination, orders=orders)


@rider_bp.route('/active/<int:rider_id>', methods=['PUT'])
@login_required
@confirm_required
def setting_active(rider_id):
    rider = Rider.query.get_or_404(rider_id)
    if current_user != rider.user:
        abort(403)
    rider.change_active()
    return redirect(url_for('.index', rider_id=rider.id))
