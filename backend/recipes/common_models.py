# from django.db import models

# from recipes.models import Recipe, User


# class UserRecipeModel(models.Model):
#     """Абстрактная модель. Добавляет поля user и recipe."""

#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE,
#         verbose_name='Пользователь',
#     )
#     recipe = models.ForeignKey(
#         Recipe,
#         on_delete=models.CASCADE,
#         verbose_name='Рецепт',
#     )

#     class Meta:
#         abstract = True

#     def __str__(self):
#         return f'{self.user} - {self.recipe}'
