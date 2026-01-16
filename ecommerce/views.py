"""
Custom error views for the ecommerce system.
"""

from django.shortcuts import render
from django.http import HttpResponseServerError


def bad_request(request, exception=None):
    """400 error handler."""
    return render(request, '400.html', status=400)


def permission_denied(request, exception=None):
    """403 error handler."""
    return render(request, '403.html', status=403)


def page_not_found(request, exception=None):
    """404 error handler."""
    return render(request, '404.html', status=404)


def server_error(request, exception=None):
    """500 error handler."""
    return render(request, '500.html', status=500)
