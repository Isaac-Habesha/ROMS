from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('menu/', include('apps.menu.urls')),
    path('orders/', include('apps.orders.urls')),
    path('approvals/', include('apps.approvals.urls')),
    path('kitchen/', include('apps.kitchen.urls')),
    path('payments/', include('apps.payments.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('audit/', include('apps.audit.urls')),
    path('restaurant/', include('apps.restaurants.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

