import os
import random

from PIL import Image
from faker import Faker
from flask import current_app
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from .extensions import db
from .models import User, Dish, Tag, Comment, Order, File, Shop, Rider
from .notifications import push_new_order_notification, push_delivered_notification

fake = Faker("zh_CN")


def fake_user(count=100):
    for i in range(count):
        user = User(name=fake.name(),
                    confirmed=True,
                    username=fake.user_name(),
                    location_x=random.randint(0, 1000),
                    location_y=random.randint(0, 1000),
                    email=fake.email(),
                    tel=str(random.randint(600000, 19999999999))
                    )
        user.set_password('123456')
        db.session.add(user)
        try:
            db.session.commit()
            rider = Rider(
                location_x=random.randint(0, 1000),
                location_y=random.randint(0, 1000),
                user=user,
            )
            db.session.add(rider)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_follow(count=100):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.follow(User.query.get(random.randint(1, User.query.count())))
    db.session.commit()


def fake_tag(count=20):
    for i in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_shop(count=20):
    for i in range(count):
        shop = Shop(
            name=fake.name(),
            location_x=random.randint(0, 1000),
            location_y=random.randint(0, 1000),
            tel=str(random.randint(600000, 19999999999)),
            user=User.query.get(random.randint(1, User.query.count()))
        )
    db.session.add(shop)
    db.session.commit()


def fake_dish(count=100):
    upload_path = current_app.config['YGQ_UPLOAD_PATH']
    for i in range(count):
        filename = 'random_%d.jpg' % i
        r = lambda: random.randint(128, 255)
        img = Image.new(mode='RGB', size=(800, 800), color=(r(), r(), r()))
        img.save(os.path.join(upload_path, filename))
        file = File(
            filename=filename,
            is_use=True,
            is_img=True
        )

        dish = Dish(
            name=fake.name(),
            description=fake.text(),
            price=random.randint(10, 100),
            timestamp=fake.date_time_this_year(),
            shop=Shop.query.get(random.randint(1, Shop.query.count())),
            sales=random.randint(0, 1000)
        )
        file.dish = dish
        # tags
        for j in range(random.randint(1, 5)):
            tag = Tag.query.get(random.randint(1, Tag.query.count()))
            if tag not in dish.tags:
                dish.tags.append(tag)

        db.session.add(dish)
    db.session.commit()


def fake_collect(count=50):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.collect(Dish.query.get(random.randint(1, Dish.query.count())))
    db.session.commit()


def fake_comment(count=100):
    for i in range(count):
        comment = Comment(
            author=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            dish=Dish.query.get(random.randint(1, Dish.query.count()))
        )
        db.session.add(comment)
    db.session.commit()


def fake_order(count=200):
    for i in range(count):
        dish = Dish.query.get(random.randint(1, Dish.query.count()))
        start_time = fake.date_time_this_year()
        fare = random.randint(1, 50)
        number = random.randint(1, 10)
        rider = Rider.query.get(random.randint(1, Rider.query.count()))
        rider.income += fare
        dish.sales += 1
        order = Order(
            consumer=User.query.get(random.randint(1, User.query.count())),
            rider=rider,
            price=dish.price*number+fare,
            fare=fare,
            start_time=start_time,
            time=start_time+timedelta(seconds=fare),
            dish=dish,
            shop=dish.shop,
            is_finish=True
        )
        db.session.add(order)
    db.session.commit()
