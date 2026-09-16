"""platenumber URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect


class CustomAdminSite(AdminSite):
    """Override admin logout to redirect to our custom logged-out page."""
    def logout(self, request, extra_context=None):
        auth_logout(request)
        return redirect('logged-out')


custom_admin = CustomAdminSite(name='admin')
# Re-register all models that were registered on the default admin site
for model, model_admin in list(admin.site._registry.items()):
    custom_admin.register(model, type(model_admin))


urlpatterns = [
    path('', include("owners.urls")),
    path('admin/', custom_admin.urls),
    path('', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


