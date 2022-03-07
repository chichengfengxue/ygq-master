from flask import url_for

from .extensions import db
from .models import Notification


def push_new_order_notification(order, receiver):
    """推送新订单消息"""
    message = 'You have a new order<a href="%s">%s</a>! \n %s' % \
              (url_for('user.show_order', order_id=order.id), order.id, order.start_time)
    notification = Notification(message=message, receiver=receiver, timestamp=order.start_time)
    db.session.add(notification)
    db.session.commit()


def push_delivered_notification(order):
    """推送订单已送达消息"""
    message = 'Your order<a href="%s">%s</a> has been delivered! \n %s' % \
              (url_for('user.show_order', order_id=order.id), order.id, order.start_time+order.time)
    notification = Notification(message=message, receiver=order.consumer, timestamp=order.start_time+order.time)
    db.session.add(notification)
    db.session.commit()
