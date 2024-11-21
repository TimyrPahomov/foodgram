"""Константы проекта."""

AVATAR_PATH = 'me/avatar'
DOWNLOAD_SHOPPING_CART_PATH = 'download_shopping_cart'
EMAIL_MAX_LENGTH = 254
FIRST_NAME_MAX_LENGTH = 150
FAVORITE_PATH = 'favorite'
INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH = 64
INGREDIENT_NAME_MAX_LENGTH = 128
LAST_NAME_MAX_LENGTH = 150
LEFT_POINT = 0
MAX_REPR_LENGTH = 25
MIN_COOKING_TIME = 1
INVALID_COOKING_TIME_MESSAGE = (
    f'Значение должно быть больше {MIN_COOKING_TIME}.'
)
PAGE_SIZE = 6
PASSWORD_CHANGE_PATH = 'set_password'
POINT = 1
RECIPE_ALREADY_IN_FAVORITE_MESSAGE = 'Рецепт уже добавлен в избранное.'
RECIPE_ALREADY_IN_SHOPPING_CART_MESSAGE = 'Рецепт уже в списке покупок.'
RECIPE_LINK_PATH = 'get-link'
RECIPE_NAME_MAX_LENGTH = 128
RECIPE_NOT_IN_FAVORITE_MESSAGE = 'Рецепт отсутствует в избранном.'
RECIPE_NOT_IN_SHOPPING_CART_MESSAGE = 'Рецепт отсутствует в списке покупок.'
SHOPPING_CART_PATH = 'shopping_cart'
SHORT_LINK_LENGTH = 3
SUBSCRIBE_PATH = 'subscribe'
SUBSCRIBE_TO_YOURSELF_MESSAGE = 'Нельзя подписаться на себя.'
SUBSCRIPTIONS_PATH = 'subscriptions'
SYMBOLS_FOR_LINK = (
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz1234567890'
)
TAG_MAX_LENGTH = 32
USERNAME_MAX_LENGTH = 150
USERNAME_REGEX = r'^[\w.@+-]+\Z'
USER_ALREADY_SUBSCRIBE_MESSAGE = 'Вы уже подписаны на этого пользователя.'
USER_NOT_SUBSCRIBE_MESSAGE = 'Вы не подписаны на данного пользователя.'
USER_PROFILE = 'me'
ZERO_VALUE = 0
