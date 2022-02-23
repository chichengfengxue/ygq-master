from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField


class ActiveSettingForm(FlaskForm):
    active = BooleanField('active')
    submit = SubmitField()
