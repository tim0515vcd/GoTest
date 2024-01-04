from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from account.models import Account, Role, SystemPermissions

# Register your models here.
admin.site.register(Account)
admin.site.register(Role)
admin.site.register(SystemPermissions)
