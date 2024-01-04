import re

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from account.models import Account, Role


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "username",
            "remarks",
            "email",
            "display_name",
            "is_active",
            "role",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["email", "display_name", "remarks",]


class GetUserTokenSerializer(serializers.Serializer):
    account = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class ChangePasswordPostSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)


class SetPasswordGetSerializer(serializers.Serializer):
    c = serializers.CharField(required=True)


class SetPasswordPostSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    password_confirm = serializers.CharField(required=True)
    code = serializers.CharField(required=True)


class ForgotPasswordPostSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)


class RoleSerializer(serializers.ModelSerializer):
    # 名稱為 unique, 但不區分大小寫 (由lookup="iexact"設定)
    name = serializers.CharField(
        max_length=20,
        validators=[UniqueValidator(queryset=Role.objects.all(), lookup="iexact")],
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "systempermissions",
            "account",
        ]
        extra_kwargs = {
            "systempermissions": {"allow_empty": True, "required": False},
            "account": {"allow_empty": True, "required": False},
        }

    def validate_name(self, data):
        # 名稱只能英數
        regex = re.compile("^[a-zA-Z0-9]+$")
        if not regex.match(data):
            raise serializers.ValidationError(code="englishordigits")
        # 編輯的時候, 不可編輯 admin、defaultrole 角色的名稱
        # 判斷原本角色名稱是 admin或defaultrole, 修改後不是 admin或defaultrole 的話就拋出 error
        if (
            # self.instance 為 DB 內資料, 修改的時候才會有
            self.instance
            and (
                (self.instance.name.lower() == "admin" and data.lower() != "admin")
                or (
                    self.instance.name.lower() == "defaultrole"
                    and data.lower() != "defaultrole"
                )
            )
        ):
            if self.instance.name.lower() == "admin" and data.lower() != "admin":
                raise serializers.ValidationError(code="can_not_edit_admin_name")
            if (
                self.instance.name.lower() == "defaultrole"
                and data.lower() != "defaultrole"
            ):
                raise serializers.ValidationError(code="can_not_edit_defaultrole_name")
        return data
