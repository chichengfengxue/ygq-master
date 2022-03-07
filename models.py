import os
from datetime import datetime


from flask import current_app
from flask_avatars import Identicon
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, whooshee


class Follow(db.Model):
    """关注模型"""
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following', lazy='joined')

    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed = db.relationship('User', foreign_keys=[followed_id], back_populates='followers', lazy='joined')

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Collect(db.Model):
    """收藏模型"""
    collector_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    collector = db.relationship('User', back_populates='collections', lazy='joined')

    collected_id = db.Column(db.Integer, db.ForeignKey('dish.id'), primary_key=True)
    collected = db.relationship('Dish', back_populates='collectors', lazy='joined')

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@whooshee.register_model('name', 'username')
class User(db.Model, UserMixin):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)
    email = db.Column(db.String(254), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(30))
    tel = db.Column(db.String(20), unique=True)
    location_x = db.Column(db.Integer)
    location_y = db.Column(db.Integer)
    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    avatar_raw = db.Column(db.String(64))  # 头像原图

    confirmed = db.Column(db.Boolean, default=False)

    shops = db.relationship('Shop', back_populates='user', cascade='all')
    rider = db.relationship('Rider', back_populates='user', cascade='all')
    orders = db.relationship('Order', back_populates='consumer')
    comments = db.relationship('Comment', back_populates='author', cascade='all')
    notifications = db.relationship('Notification', back_populates='receiver', cascade='all')
    files = db.relationship('File', back_populates='user', cascade='all')
    collections = db.relationship('Collect', back_populates='collector', cascade='all')
    following = db.relationship('Follow', foreign_keys=[Follow.follower_id], back_populates='follower',
                                lazy='dynamic', cascade='all')  # 关注者
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], back_populates='followed',
                                lazy='dynamic', cascade='all')  # 被关注者

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.generate_avatar()
        self.follow(self)  # 关注自己

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        """执行关注"""
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        """执行取消关注"""
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        """判断用户是否正在关注某个用户"""
        if user.id is None:  # 关注自己时，用户还是访客Guest，没有id
            return False
        return self.following.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        """判断用户是否被某个用户关注"""
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def collect(self, dish):
        if not self.is_collecting(dish):
            collect = Collect(collector=self, collected=dish)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, dish):
        collect = Collect.query.with_parent(self).filter_by(collected_id=dish.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def is_collecting(self, photo):
        """判断用户是否已经收藏图片"""
        return Collect.query.with_parent(self).filter_by(collected_id=photo.id).first() is not None

    def generate_avatar(self):
        """生成随机头像文件"""
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()


class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_x = db.Column(db.Integer)
    location_y = db.Column(db.Integer)
    name = db.Column(db.String(30))
    tel = db.Column(db.String(11), unique=True)
    dishes = db.relationship('Dish', back_populates='shop', cascade='all')
    orders = db.relationship('Order', back_populates='shop', cascade='all')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='shops')


class Rider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_x = db.Column(db.Integer)
    location_y = db.Column(db.Integer)
    orders = db.relationship('Order', back_populates='rider')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='rider')
    income = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=False)

    def to_active(self):
        self.active = True
        db.session.commit()

    def to_inactive(self):
        self.active = False
        db.session.commit()


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'))
    dish = db.relationship('Dish', back_populates='orders')
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    shop = db.relationship('Shop', back_populates='orders')
    consumer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    consumer = db.relationship('User', back_populates='orders')
    rider_id = db.Column(db.Integer, db.ForeignKey('rider.id'))
    rider = db.relationship('Rider', back_populates='orders')
    price = db.Column(db.Integer)
    number = db.Column(db.Integer)
    fare = db.Column(db.Integer)
    is_finish = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    time = db.Column(db.DateTime)


tagging = db.Table('tagging',
                   db.Column('dish_id', db.Integer, db.ForeignKey('dish.id')),
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                   )


@whooshee.register_model('description')
class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    price = db.Column(db.Integer)
    description = db.Column(db.String(500))
    filename_s = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    shop = db.relationship('Shop', back_populates='dishes')
    files = db.relationship('File', back_populates='dish')
    orders = db.relationship('Order', back_populates='dish')
    comments = db.relationship('Comment', back_populates='dish', cascade='all')
    collectors = db.relationship('Collect', back_populates='collected', cascade='all')
    tags = db.relationship('Tag', secondary=tagging, back_populates='dishes')
    sales = db.Column(db.Integer, default=0)


@whooshee.register_model('name')
class Tag(db.Model):
    """商品标签"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

    dishes = db.relationship('Dish', secondary=tagging, back_populates='tags')


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64))
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'))
    dish = db.relationship('Dish', back_populates='files')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='files')
    is_use = db.Column(db.Boolean, default=False)
    is_img = db.Column(db.Boolean, default=True)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='comments')
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'))
    dish = db.relationship('Dish', back_populates='comments')

    replies = db.relationship('Comment', back_populates='replied', cascade='all')
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 接收者
    receiver = db.relationship('User', back_populates='notifications')


@db.event.listens_for(User, 'after_delete', named=True)
def delete_avatars(**kwargs):
    """删除头像文件的监听函数"""
    target = kwargs['target']
    for filename in [target.avatar_s, target.avatar_m, target.avatar_l, target.avatar_raw]:
        if filename is not None:  # avatar_raw may be None
            path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
            if os.path.exists(path):  # not every filename map a unique file
                os.remove(path)


@db.event.listens_for(Dish, 'after_delete', named=True)
def delete_photos(**kwargs):
    """图片删除事件监听函数"""
    target = kwargs['target']
    for file in target.files:
        path = os.path.join(current_app.config['YGQ_UPLOAD_PATH'], file.filename)
        if os.path.exists(path):  # not every filename map a unique file
            os.remove(path)
