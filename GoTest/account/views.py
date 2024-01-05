from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from account.serializers import (
    ProfileSerializer,
    ChangePasswordPostSerializer,
    UserListSerializer,
    RoleSerializer,
    ForgotPasswordPostSerializer,
    SetPasswordGetSerializer,
    SetPasswordPostSerializer,
)
from account.models import Account, Role, SystemPermissions, AccountAuth
from gotestlib.account import check_password_pattern, get_password_pattern
from gotestlib.utils import check_serializer_errors
from gotestlib.permissions import RolePermission
import uuid

PARAMETER_ERROR = "parameter error"


# Create your views here.
class LoginView(BaseLoginView):
    """
    Override django.contrib.auth.views.LoginView
    """

    template = "sign-in.html"

    def get(self, request):
        """
        先判斷是否要用驗證碼
        """
        return render(
            request,
            self.template,
        )

    def post(self, request, *args, **kwargs):
        """
        Override django.views.generic.edit.ProcessFormView 的 post 方法,
        檢查密碼是否輸入錯誤三次而被鎖定
        """
        username = request.POST.get("username", None)
        # user = Account.objects.filter(username=username, is_active=True).first()

        # 以下為 django 原始碼, 驗證登入資訊, is_valid 就會檢查帳密
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            context = {
                "form_invalid": form.errors,
            }

            return render(request, self.template, context)


class ProfileView(generics.GenericAPIView):
    """
    使用者個人資料
    """

    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get_object(self, pk, email):
        try:
            return Account.objects.get(pk=pk, email=email)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request):
        profile = Account.objects.get(
            username=self.request.user.username, email=self.request.user.email
        )
        return Response(
            {
                "profile": profile,
                "password_pattern": get_password_pattern(),
            },
            template_name="profile.html",
        )

    def put(self, request):
        account = self.get_object(
            pk=self.request.user.id, email=self.request.user.email
        )
        serializer = ProfileSerializer(account, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"result": _("Edit profile success")}, status=status.HTTP_200_OK
            )
        else:
            # email 已存在則回傳自訂錯誤訊息
            if check_serializer_errors(serializer.errors, "unique"):
                return Response(
                    {"result": _("EMAIL_ALREADY_EXISTS")},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                "result": _("EDIT_PROFILE_FAILED"),
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChangePasswordPostView(generics.GenericAPIView):
    serializer_class = ChangePasswordPostSerializer
    permission_classes = (IsAuthenticated,)
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.data.get("old_password", None)
            new_password = serializer.data.get("new_password", None)
            confirm_password = serializer.data.get("confirm_password", None)
        else:
            return Response(
                {
                    "result": _("PARAMETER_ERROR"),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = request.user.password
        if not check_password(old_password, password):
            return Response(
                {"result": _("Old Password not match")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if old_password == new_password:
            return Response(
                {"result": _("New password cannot be the same as your old password")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not check_password_pattern(new_password):
            return Response(
                {"result": _("new password pattern error")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_password != confirm_password:
            return Response(
                {"result": _("Password not equal")}, status=status.HTTP_400_BAD_REQUEST
            )

        # 強迫使用者第一次登入之後修改密碼, 只有在自己的個人資料頁面修改才算
        # 修改完之後將強制修改密碼的 flag 改為 False
        request.user.force_password_change = False
        # 更新上次修改密碼時間
        request.user.last_change_password_time = timezone.now()
        # 修改完密碼後將密碼過期的 flag 改為 False
        request.user.is_password_expired = False
        request.user.set_password(new_password)
        request.user.save()
        return Response(
            {"result": _("Change password success")}, status=status.HTTP_200_OK
        )


class UserListView(generics.GenericAPIView):
    """
    使用者管理頁面 & 新增使用者
    """

    permission_classes = (
        IsAuthenticated,
        RolePermission,
    )
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request):
        account_list = Account.objects.all()
        roles = Role.objects.all()
        return Response(
            template_name="user.html",
            data={
                "account_list": account_list,
                "roles": roles,
                "password_pattern": get_password_pattern(),
            },
        )

    def post(self, request):
        serializer = UserListSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get("username", None)
            role = serializer.validated_data.get("role", None)
            email = serializer.validated_data.get("email", None)
            display_name = serializer.validated_data.get("display_name", None)
            remarks = serializer.validated_data.get("remarks", None)
            is_active = serializer.validated_data.get("is_active", None)
            new_password = request.POST.get("new_password", None)
            confirm_password = request.POST.get("confirm_password", None)
        else:
            # username、email 已存在則回傳自訂錯誤訊息
            if check_serializer_errors(serializer.errors, "unique"):
                if "username" in serializer.errors:
                    return Response(
                        {"result": _("Account already exists")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if "email" in serializer.errors:
                    return Response(
                        {"result": _("EMAIL_ALREADY_EXISTS")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            return Response(
                {
                    "result": _("PARAMETER_ERROR"),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password_pattern(new_password):
            return Response(
                {"result": _("INSUFFICIENT_PASSWORD_COMPLEXITY")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {"result": _("PASSWORD_MUST_BE_THE_SAME_AS_PASSWORD_CONFIRM")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            Account.objects.create_user(
                email=email,
                username=username,
                is_active=is_active,
                role=role,
                display_name=display_name,
                password=new_password,
                remarks=remarks,
            )
        except Exception as error:
            return Response(
                {"result": _("Create Account Error"), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"result": _("Create user success")}, status=status.HTTP_200_OK)


class UserPostView(generics.GenericAPIView):
    """
    使用者管理 編輯 & 刪除
    """

    serializer_class = UserListSerializer
    permission_classes = (
        IsAuthenticated,
        RolePermission,
    )
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get_object(self, pk):
        try:
            return Account.objects.get(pk=pk)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        account = self.get_object(pk=pk)
        serializer = UserListSerializer(account)
        return Response(serializer.data)

    def put(self, request, pk):
        account = self.get_object(pk=pk)
        serializer = UserListSerializer(account, data=request.data)

        if serializer.is_valid():
            serializer.save()
            new_password = request.POST.get("new_password", None)
            confirm_password = request.POST.get("confirm_password", None)
        else:
            # email 已存在則回傳自訂錯誤訊息
            if check_serializer_errors(serializer.errors, "unique"):
                return Response(
                    {"result": _("EMAIL_ALREADY_EXISTS")},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "result": _("PARAMETER_ERROR"),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password and confirm_password:
            if not check_password_pattern(new_password):
                return Response(
                    {"result": _("INSUFFICIENT_PASSWORD_COMPLEXITY")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if new_password != confirm_password:
                return Response(
                    {"result": _("PASSWORD_MUST_BE_THE_SAME_AS_PASSWORD_CONFIRM")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            account.set_password(new_password)
            account.save()
        return Response({"result": _("Edit user success")}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        account = self.get_object(pk)
        # Administrator不能被刪除
        if account.username == "Administrator":
            return Response(
                {
                    "result": _("This account cannot be deleted"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListView(generics.GenericAPIView):
    """
    角色列表 & 新增
    """

    permission_classes = (
        IsAuthenticated,
        RolePermission,
    )
    serializer_class = RoleSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request):
        roles = Role.objects.all()
        systempermissions = SystemPermissions.objects.all()
        account = Account.objects.all()
        return Response(
            {
                "roles": roles,
                "systempermissions": systempermissions,
                "account": account,
            },
            template_name="role.html",
        )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # role = serializer.save()

            # create_role_dashboard_permission(role)

            return Response(
                {"result": _("Add role success")}, status=status.HTTP_201_CREATED
            )
        else:
            # unique -> 名稱不可重複, 不區分大小寫
            if check_serializer_errors(serializer.errors, "unique"):
                return Response(
                    {"result": _("Name already exists"), "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # englishordigits -> 名稱只能是英數
            if check_serializer_errors(serializer.errors, "englishordigits"):
                return Response(
                    {
                        "result": _("Name only accept english or digits"),
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # {'systempermissions': [ErrorDetail(string='無效的主鍵 "9" - 物件不存在。', code='does_not_exist')]}
            if check_serializer_errors(serializer.errors, "does_not_exist"):
                return Response(
                    {
                        "result": _(
                            "User, system permission or datasource not exist, please refresh or try again later."
                        ),
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "result": "PARAMETER_ERROR",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


def check_system_permissions(systempermissions, role_id):
    """檢查系統權限"""
    # 取得系統權限
    systempermission_dashboard = SystemPermissions.objects.filter(
        feature="dashboard"
    ).first()
    if not systempermission_dashboard:
        return
    # 如果該角色的儀表板權限不在表中，則移除該角色所擁有的所有儀表版
    if systempermission_dashboard.id not in systempermissions:
        dashboard_permissions = DashboardPermission.objects.filter(role=role_id)
        for dashboard_permission in dashboard_permissions:
            dashboard_permission.edit = False
            dashboard_permission.home_sort = False
            dashboard_permission.save()


def check_account_role():
    """檢查因為編輯角色功能而被變成沒有角色的帳號，將該帳號的角色變成預設角色"""
    account_obj = Account.objects.filter(role=None)
    default_role = Role.objects.filter(name="normal").first()
    for account in account_obj:
        account.role = default_role
        account.save()


class RoleView(generics.GenericAPIView):
    """
    角色編輯 & 刪除
    """

    permission_classes = (
        IsAuthenticated,
        RolePermission,
    )
    serializer_class = RoleSerializer
    renderer_classes = [JSONRenderer]

    def get_object(self, pk):
        """
        取得 Role model
        """
        try:
            return Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        serializer = RoleSerializer(self.get_object(pk))
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        role = self.get_object(pk)
        serializer = self.get_serializer(role, data=request.data)
        if serializer.is_valid():
            serializer.save()
            systempermissions = serializer.data.get("systempermissions")
            role_id = serializer.data.get("id")
            check_system_permissions(systempermissions, role_id)
            check_account_role()
            return Response(
                {"result": _("Edit role success")}, status=status.HTTP_200_OK
            )
        else:
            # can_not_edit_admin_name -> admin 角色的名稱不可編輯
            if check_serializer_errors(serializer.errors, "can_not_edit_admin_name"):
                return Response(
                    {
                        "result": _("Admin's role name cannot be edited"),
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # can_not_edit_defaultrole_name -> defaultrole 角色的名稱不可編輯
            if check_serializer_errors(
                serializer.errors, "can_not_edit_defaultrole_name"
            ):
                return Response(
                    {
                        "result": _("Defaultrole's role name cannot be edited"),
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # unique -> 名稱不可重複, 不區分大小寫
            if check_serializer_errors(serializer.errors, "unique"):
                return Response(
                    {"result": _("Name already exists"), "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # englishordigits -> 名稱只能是英數
            if check_serializer_errors(serializer.errors, "englishordigits"):
                return Response(
                    {
                        "result": _("Name only accept english or digits"),
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # {'systempermissions': [ErrorDetail(string='無效的主鍵 "9" - 物件不存在。', code='does_not_exist')]}
            if check_serializer_errors(serializer.errors, "does_not_exist"):
                return Response(
                    {
                        "result": _(
                            "User, system permission or datasource not exist, please refresh or try again later."
                        ),
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "result": "PARAMETER_ERROR",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, pk, format=None):
        role = self.get_object(pk)
        admin_role = Role.objects.filter(name__iexact="admin").first()
        default_role = Role.objects.filter(name__iexact="defaultrole").first()

        # admin、defaultrole角色不能被刪除
        if role == admin_role or role == default_role:
            return Response(
                {"result": _("This Role cannot be deleted")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 刪除角色時, 將該角色的 alert 和 report 轉至 default_role 角色
            # 此段使用資料庫 transaction, 刪除失敗時會 rollback
            with transaction.atomic():
                # 檢查是否有 admin、default_role 角色, 以及被刪除的不是 admin、default_role 角色
                if (admin_role and (role != admin_role)) or (
                    default_role and (role != default_role)
                ):
                    pass
                role.delete()
        except ProtectedError:
            # 尚有帳號時, 角色不可被刪除
            return Response(
                {"result": _("Role in use, please delete accounts first")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


def create_accountauth(account, auth_type):
    # 用 uuid4 產生隨機字串用以驗證帳戶
    sign_up_code = uuid.uuid4().hex
    AccountAuth.objects.create(
        auth_type=auth_type, account=account, code=sign_up_code, is_authenticated=False
    )
    return sign_up_code


class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordPostSerializer
    permission_classes = (AllowAny,)
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request):
        return Response(
            template_name="forgot-password.html",
        )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            username = serializer.data.get("username", None)
        else:
            return Response(
                {"result": _(PARAMETER_ERROR), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            account = Account.objects.get(username=username)
            display_name = account.display_name
            if account.is_ad_account:
                return Response(
                    {
                        "result": _(
                            "This account is an AD account, please contact AD admin."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception:
            return Response(
                {"result": _("Account not found")}, status=status.HTTP_400_BAD_REQUEST
            )

        code = create_accountauth(account, AccountAuth.auth_type_choices.PASSWORD_RESET)
        # 驗證帳號網址
        auth_url = request.build_absolute_uri("/resetpassword?c=" + code)
        # site_ip, unused = get_localip()
        # # 送出驗證信
        # content = render_to_string(
        #     "email/signup_auth.html",
        #     {"display_name": display_name, "auth_url": auth_url, "ip": site_ip},
        # )
        # result = safe_mail(
        #     subject="SAFE3.0 forgot password",
        #     recipients=[account.email],
        #     body=content,
        # )
        result = True
        if not result:
            return Response(
                {"result": _("Please contact admin")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"result": _("Reset password email send success")},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SetPasswordPostSerializer
        return SetPasswordGetSerializer

    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        template_name = "resetpassword.html"
        if serializer.is_valid():
            code = serializer.data.get("c", None)
        else:
            return Response(
                {"result": _("URL invalid")},
                template_name=template_name,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            accountauth = AccountAuth.objects.select_related("account").get(
                code=code, is_authenticated=False
            )
            user_email = accountauth.account.email
        except Exception:
            return Response(
                {"result": _("URL invalid, please contact admin")},
                template_name=template_name,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 帳號驗證須於 10 分鐘內
        if timezone.now() > (accountauth.create_time + timezone.timedelta(minutes=10)):
            return Response(
                {"result": _("The URL has expired, please reset the password again")},
                template_name=template_name,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "email": user_email,
                "code": code,
                "password_pattern": get_password_pattern(),
            },
            template_name=template_name,
        )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.data.get("email", None)
            code = serializer.data.get("code", None)
            password = serializer.data.get("password", None)
            password_confirm = serializer.data.get("password_confirm", None)
        else:
            return Response(
                {"result": PARAMETER_ERROR, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            accountauth = AccountAuth.objects.select_related("account").get(
                code=code, is_authenticated=False
            )
        except Exception:
            return Response(
                {"result": _("URL invalid, please contact admin")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if timezone.now() > (accountauth.create_time + timezone.timedelta(minutes=10)):
            return Response(
                {"result": _("The URL has expired, please reset the password again")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password_pattern(password):
            return Response(
                {"result": _("Insufficient password complexity")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password != password_confirm:
            return Response(
                {"result": _("Password must be the same as password confirm")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account = accountauth.account
        if account.email != email:
            return Response(
                {"result": _("User email error")}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            accountauth.is_authenticated = True
            accountauth.save()
            account = Account.objects.get(email=email)
            account.set_password(password)
            account.save()
            return Response(
                {"result": _("Reset password success")}, status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"result": _("User email error")}, status=status.HTTP_400_BAD_REQUEST
            )
