from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

class NonPaginatedResultSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class CustomPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'next_params': self.get_next_link_params(),
            'prev_params': self.get_previous_link_params(),
            'current': self.offset,
            'results': data
        })

    def get_next_link_params(self):
        if self.offset + self.limit >= self.count:
            return None

        offset = self.offset + self.limit
        return f"?limit={self.limit}&offset={offset}"

    def get_previous_link_params(self):
        if self.offset <= 0:
            return None

        if self.offset - self.limit <= 0:
            return f"?limit={self.limit}"

        offset = self.offset - self.limit
        return f"?limit={self.limit}&offset={offset}"