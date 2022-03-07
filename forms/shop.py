from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Optional, Length


class DescriptionForm(FlaskForm):
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    submit = SubmitField()


class TagForm(FlaskForm):
    tag = StringField('Add Tag (use space to separate)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField()


class Apply2Shop(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    location_x = IntegerField('location-x', validators=[DataRequired()])
    location_y = IntegerField('location-y', validators=[DataRequired()])
    tel = IntegerField('tel', validators=[DataRequired()])
    submit = SubmitField()


class DishForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    price = IntegerField('price', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    tag = StringField('Add Tag (use space to separate)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField()

    def validate_number(self, field):
        if field.data <= 0:
            raise ValidationError('Quantity must be greater than zero!')