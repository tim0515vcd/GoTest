"""GoTest URL Configuration

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
from django.conf.urls import include
from django.urls import path
from account.views import LoginView, ResetPasswordView, ForgotPasswordView
from base.views import IndexView

urlpatterns = [
    path(
        "",
        LoginView.as_view(template_name="login.html", redirect_authenticated_user=True),
        name="login",
    ),
    path("base/", include("base.urls")),
    path("account/", include("account.urls")),
    path("questionbank/", include("questionbank.urls")),
    path("resetpassword", ResetPasswordView.as_view(), name="resetpassword"),
    path("forgot", ForgotPasswordView.as_view(), name="forgot"),
    path("home", IndexView.as_view(), name="home"),
    path("admin/", admin.site.urls),
]
