from django.contrib import admin
from django.urls import include, path

from utils.functions import redirection

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_link>', redirection),
]
