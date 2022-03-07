from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import IntegerField, StringField, PasswordField, SubmitField, HiddenField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp

from ..models import User


class EditProfileForm(FlaskForm):
    """用户资料编辑表单"""
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    username = StringField('Username', validators=[DataRequired(), Length(1, 20),
                                                   Regexp('^[a-zA-Z0-9]*$',
                                                          message='The username should contain only a-z, A-Z and 0-9.')])
    location_x = IntegerField('location-x', validators=[DataRequired()])
    location_y = IntegerField('location-y', validators=[DataRequired()])
    tel = StringField('tel', validators=[DataRequired(), Length(6, 20)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already in use.')


class EditOrder(FlaskForm):
    """订单编辑表单"""
    number = IntegerField('number', validators=[DataRequired()])
    location_x = IntegerField('location-x', validators=[DataRequired()])
    location_y = IntegerField('location-y', validators=[DataRequired()])
    submit = SubmitField()

    def validate_number(self, field):
        if field.data <= 0:
            raise ValidationError('Quantity must be greater than zero!')


class UploadAvatarForm(FlaskForm):
    image = FileField('Upload', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'The file format should be .jpg or .png.')
    ])
    submit = SubmitField()


class CropAvatarForm(FlaskForm):
    """头像图片裁剪表单"""
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField('Crop and Update')


class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('The email is already in use.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField()


class DeleteAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError('Wrong username.')
