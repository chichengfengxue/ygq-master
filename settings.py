import os
import sys
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class Operations:
    CONFIRM = 'confirm'
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'


class BaseConfig:

    # email
    YGQ_ADMIN_EMAIL = os.getenv('YGQ_ADMIN', 'admin@helloflask.com')
    YGQ_MAIL_SUBJECT_PREFIX = '[YGQ]'
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('YGQ Admin', MAIL_USERNAME)

    # 每页记录数
    YGQ_DISH_PER_PAGE = 12
    YGQ_COMMENT_PER_PAGE = 15
    YGQ_NOTIFICATION_PER_PAGE = 20
    YGQ_USER_PER_PAGE = 20
    YGQ_MANAGE_PHOTO_PER_PAGE = 20
    YGQ_MANAGE_USER_PER_PAGE = 30
    YGQ_MANAGE_TAG_PER_PAGE = 50
    YGQ_MANAGE_COMMENT_PER_PAGE = 30
    YGQ_SEARCH_RESULT_PER_PAGE = 20

    # 图片上传
    YGQ_UPLOAD_PATH = os.path.join(basedir, 'uploads')
    YGQ_DISH_SIZE = {'small': 400, 'medium': 800}
    YGQ_DISH_SUFFIX = {
        YGQ_DISH_SIZE['small']: '_s',
        YGQ_DISH_SIZE['medium']: '_m',
    }
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024  # 上传最大值

    DROPZONE_ALLOWED_FILE_TYPE = 'default'  # 设置允许的文件类型
    DROPZONE_MAX_FILE_SIZE = 30
    DROPZONE_MAX_FILES = 30
    DROPZONE_ENABLE_CSRF = True

    SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')

    BOOTSTRAP_SERVE_LOCAL = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 头像上传
    AVATARS_SAVE_PATH = os.path.join(YGQ_UPLOAD_PATH, 'avatars')
    AVATARS_SIZE_TUPLE = (30, 100, 200)  # 小、中、大头像图片大小元组

    WHOOSHEE_MIN_STRING_LEN = 1  # 搜索关键字的最小字符数

    # 定时器配置项
    # 持久化配置，数据持久化至MongoDB
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=prefix + os.path.join(basedir, 'data-dev.db'))}
    # 线程池配置，最大20个线程
    SCHEDULER_EXECUTORS = {'default': ThreadPoolExecutor(20)}
    # 调度开关开启
    SCHEDULER_API_ENABLED = True
    # 设置容错时间为 1小时
    SCHEDULER_JOB_DEFAULTS = {'misfire_grace_time': 3600}
    # 配置时区
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = \
        prefix + os.path.join(basedir, 'data-dev.db')
    REDIS_URL = "redis://localhost"


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'  # in-memory database


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',
                                        prefix + os.path.join(basedir, 'data.db'))


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
