import re


def get_password_pattern():
    """
    密碼強度，須包含大小寫英文、數字、特殊符號、8字元以上
    """
    return "^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\:\(\)\=\+\_\[\]\{\}\-\\|\\\`\~\"'\?\>\<\.\,\/$%\^&\*])(?=.{8,}).*"


def check_password_pattern(password):
    """
    檢查密碼強度
    """
    reg = re.compile(get_password_pattern())
    if reg.match(password):
        return True
    return False


def get_user_systempermissions_list(request_user):
    """
    取得角色系統權限的 list

    回傳 list, ex. ['search', 'report', 'dashboard', 'alert', 'datasource', 'index', 'account', 'systemsettings']
    """
    user_role = request_user.role
    # 如果使用者沒有角色, 直接回傳空 list
    if not user_role:
        return []
    user_systempermissions = user_role.systempermissions.values_list(
        "feature", flat=True
    )
    return list(user_systempermissions)
