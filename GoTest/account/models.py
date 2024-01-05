from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime
import pytz
from django.conf import settings
from django.utils import timezone

# Create your models here.
DEFAULT_TIME = datetime(1970, 1, 1, tzinfo=pytz.timezone(settings.TIME_ZONE))


class SystemPermissions(models.Model):
    """
    角色權限
    """

    feature = models.CharField("Features", max_length=20)
    display_name = models.CharField(
        "Display Name", max_length=30, help_text="顯示名稱及多語系字串"
    )


class Role(models.Model):
    """
    角色
    """

    # 只能英數, 不區分大小寫 -> 由 serializer 限制
    name = models.CharField("Name", max_length=20, unique=True)
    description = models.CharField("Description", max_length=255, blank=True)
    # 多對多權限設定
    systempermissions = models.ManyToManyField(SystemPermissions)


class Account(AbstractUser):
    """
    Model 繼承 AbstractUser, 這邊未定義的要去父類別看
    first_name + last_name 長度要 < display_name
    """

    email = models.EmailField("Email", max_length=255, unique=True, null=True)
    display_name = models.CharField("Display Name", max_length=60, blank=False)
    remarks = models.TextField("Remarks", blank=True)
    # admin role使用者api token
    token = models.CharField("api token", max_length=36, blank=True, null=True)
    token_time = models.DateTimeField("Token time", blank=True, null=True)
    # 尚有帳號時, 角色不可被刪除
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="account", null=True
    )
    channel = models.CharField("channel", max_length=255)
    force_password_change = models.BooleanField(
        "Force password change", default=True, help_text="是否強制修改密碼"
    )
    lock_time = models.DateTimeField(
        "Lock time", default=DEFAULT_TIME, help_text="帳號被鎖定時間，15分鐘之後才能解鎖"
    )
    login_failed_count = models.IntegerField(
        "Login failed count", default=0, help_text="登入密碼錯誤次數"
    )
    # 最後修改密碼時間
    last_change_password_time = models.DateTimeField(
        "Last Change Password Time", default=datetime.now, blank=True
    )
    # 密碼是否到期
    is_password_expired = models.BooleanField(
        "Is Password Expired", default=False, help_text="密碼是否到期"
    )
    # 輸贏總金額加總
    total_money = models.IntegerField("Total Money", default=0, help_text="輸贏錢總金額")
    # 總金額除以參戰次數
    kda = models.IntegerField("KDA", default=0, help_text="總金額除以參戰次數")
    # 勝率
    winning_percentage = models.FloatField(
        "Winning Percentage", default=0, help_text="勝率"
    )
    # 場數
    session = models.IntegerField("Session", default=0, help_text="參戰次數")

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Account"


class AccountAuth(models.Model):
    """帳號登入驗證用"""

    class auth_type_choices(models.TextChoices):
        SIGN_UP = "SIGN_UP", "Sign Up"
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
        ADD_USER = "ADD_USER", "Add User"
        RESEND_VALIDATION = "RESEND_VALIDATION", "Resend validation email"

    auth_type = models.CharField(
        "Auth Type", max_length=20, choices=auth_type_choices.choices
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="accountauth"
    )
    code = models.CharField("Code", max_length=32)
    create_time = models.DateTimeField("Create Time", editable=False)
    update_time = models.DateTimeField("Update Time")
    is_authenticated = models.BooleanField("Is Authenticated", default=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.create_time = timezone.now()
        self.update_time = timezone.now()
        return super(AccountAuth, self).save(*args, **kwargs)
