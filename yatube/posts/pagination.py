from django.conf import settings
from django.core.paginator import Paginator


def get_paginator_page(request, query_set):
    paginator = Paginator(query_set, settings.COUNT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
