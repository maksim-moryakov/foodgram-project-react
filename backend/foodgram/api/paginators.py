from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Переопределение параметра стандартного пагинатора"""
    page_size_query_param = 'limit'
