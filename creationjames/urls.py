from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_tools/', include('admin_tools.urls')),
    path('grappelli/', include('grappelli.urls')),
    path('', include('homepage.urls')),
    path('authentication/', include('authentication.urls')),
    path('ecommerce/', include('ecommerce.urls')),
    path('association/', include('association.urls')),
    path('parti/', include('parti.urls')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
