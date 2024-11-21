import io

from rest_framework import renderers

from utils.constants import LEFT_POINT, POINT


class TextIngredientDataRenderer(renderers.BaseRenderer):
    """
    Рендер для работы со списком покупок.

    Возвращает список покупок в виде txt файла.
    """

    media_type = "text/plain"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Метод для настройки рендеринга."""
        text_buffer = io.StringIO()
        left = LEFT_POINT
        right = len(data) - POINT
        point = POINT
        while left <= right:
            if point <= right and left + point <= right:
                if left != right and (
                    data[left]['id'] == data[left + point]['id']
                ):
                    data[left + point]['amount'] += data[left]['amount']
                    left += 1
                    point = 1
                    continue
                point += 1
                continue
            text_buffer.write(
                data[left]['name'] + ' ' + '('
                + data[left]['measurement_unit'] + ')' + ' - '
                + str(data[left]['amount']) + '\n')
            left += 1
            point = 1
        return text_buffer.getvalue()
