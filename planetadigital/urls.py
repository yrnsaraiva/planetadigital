from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('eventos/', include('events.urls', namespace='eventos')),
    path('galeria/', include('gallery.urls')),
    path('loja/', include('shop.urls')),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path('planeta&homies/', include('campaigns.urls', namespace='campaigns')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)