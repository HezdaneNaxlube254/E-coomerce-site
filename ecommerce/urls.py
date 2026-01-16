"""ecommerce URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.conf.urls import handler400, handler403, handler404, handler500
from .health_views import HealthView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('users/', include('users.urls')),
    path('orders/', include('orders.urls')),
    path('health/', HealthView.as_view(), name='health'),
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler400 = 'ecommerce.views.bad_request'
handler403 = 'ecommerce.views.permission_denied'
handler404 = 'ecommerce.views.page_not_found'
handler500 = 'ecommerce.views.server_error'
