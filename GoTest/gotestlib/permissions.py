from django.urls import reverse
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework import status
from django.conf import settings
from django.core.cache import cache
from django.contrib import auth
from account.models import Account
from django.core.exceptions import ObjectDoesNotExist
import datetime
from rest_framework import status
from rest_framework.response import Response


class RolePermission(BasePermission):
    """
    判斷登入角色帳號權限
    """

    def has_permission(self, request, view):
        if is_common_pages(request.path):
            return True
        if is_role_permitted(request.path, request.user):
            return True
        return False

def is_common_pages(request_path):
    """
    判斷頁面是否為不需特別設定權限的頁面
    """
    common_pages = [
        reverse("login"),  # /account/login
        reverse("logout"),  # /account/logout
        reverse("profile"),  # /account/profile
        reverse("changepassword"),  # /account/changepassword
        # reverse("dashboard_list"),  # /dashboard/list
        "/",  # 首頁
    ]
    if request_path in common_pages:
        return True
    return False


def is_role_permitted(request_path, user):
    """
    檢查使用者所屬角色是否有該 app 的權限
    """
    app = request_path.split("/")[1]
    if user.role and user.role.systempermissions.filter(feature=app).exists():
        return True
    return False

