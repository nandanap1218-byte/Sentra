from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def home(request):
    return JsonResponse({
        "message": "SENTRA Backend API is running.",
        "status": "success",
        "endpoints": {
            "register": "/api/auth/register/",
            "login": "/api/auth/login/",
            "me": "/api/auth/me/",
            "users": "/api/auth/users/",
            "admin": "/admin/",
        }
    })


urlpatterns = [
    path("", home, name="home"),

    path("admin/", admin.site.urls),

    path("api/auth/", include("users.urls")),
]