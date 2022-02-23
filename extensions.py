from flask_avatars import Avatars
from flask_bootstrap import Bootstrap
from flask_dropzone import Dropzone
from flask_login import LoginManager, AnonymousUserMixin
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_wtf import CSRFProtect
from flask_apscheduler import APScheduler as _BaseAPScheduler


class APScheduler(_BaseAPScheduler):
    """重写APScheduler，实现上下文管理机制，小优化功能也可以不要。对于任务函数涉及数据库操作有用"""
    def run_job(self, id, jobstore=None):
        with self.app.app_context():
            super().run_job(id=id, jobstore=jobstore)


bootstrap = Bootstrap()
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
dropzone = Dropzone()
moment = Moment()
whooshee = Whooshee()
avatars = Avatars()
csrf = CSRFProtect()
# scheduler = APScheduler()
# scheduler.start()


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    user = User.query.get(int(user_id))
    return user


login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'

login_manager.refresh_view = 'auth.re_authenticate'
login_manager.needs_refresh_message = '为了保护你的账户安全，请重新登录。'
login_manager.needs_refresh_message_category = 'warning'


class Guest(AnonymousUserMixin):
    """访客(使得未登录用户也有can和is_admin方法)"""
    def can(self, permission_name):
        return False

    @property
    def is_admin(self):
        return False


login_manager.anonymous_user = Guest  # 继承自匿名用户类


