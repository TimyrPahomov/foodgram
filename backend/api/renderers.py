import io
from rest_framework import renderers


class TextIngredientDataRenderer(renderers.BaseRenderer):

    media_type = "text/plain"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):

        text_buffer = io.StringIO()
        left = 0
        right = len(data) - 1
        while left <= right:
            if left != right and data[left]['id'] == data[left+1]['id']:
                data[left+1]['amount'] += data[left]['amount']
                left += 1
                continue
            text_buffer.write(
                data[left]['name'] + ' ' + '('
                + data[left]['measurement_unit'] + ')' + ' - '
                + str(data[left]['amount']) + '\n')
            left += 1
        return text_buffer.getvalue()
