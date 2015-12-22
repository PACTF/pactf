from django.shortcuts import render
from django.conf import settings

def get_default_dict(request):
    result = {}
    result['production'] = not settings.DEBUG
    return result

def index(request):
    params = get_default_dict(request)
    pass
