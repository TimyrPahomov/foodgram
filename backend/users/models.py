from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from utils.constants import (EMAIL_MAX_LENGTH, MAX_REPR_LENGTH,
                             PASSWORD_MAX_LENGTH, USERNAME_MAX_LENGTH,
                             USERNAME_REGEX)


class FoodgramUser(AbstractUser):
    """Модель Пользователя."""

    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )
    username = models.CharField(
        'Юзернейм пользователя',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(
            RegexValidator(
                regex=USERNAME_REGEX,
                message='Недопустимый символ в имени пользователя.'
            ),

        )
    )
    first_name = models.CharField(
        'Имя пользователя',
        max_length=USERNAME_MAX_LENGTH
    )
    last_name = models.CharField(
        'Фамилия пользователя',
        max_length=USERNAME_MAX_LENGTH
    )
    password = models.CharField('Пароль',
                                max_length=PASSWORD_MAX_LENGTH)
    avatar = models.ImageField(
        'Аватар пользователя',
        upload_to='users/avatars/',
        null=True,
        default=None
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('first_name',)

    def __str__(self):
        return (
            f"{self.first_name[:MAX_REPR_LENGTH]} "
            f"{self.last_name[:MAX_REPR_LENGTH]}."
        )
