from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Пагинатор для динамического определения размера страницы."""

    page_size_query_param = 'limit'
