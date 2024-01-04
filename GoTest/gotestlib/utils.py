def check_serializer_errors(errors, code):
    """
    檢查 serializer.errors 內是否有對應的 error code,
    有檢查到回傳 `tuple(欄位名稱, 錯誤訊息)`, 否則回傳 `None`

    serializer.errors 回傳是一個 dictionary, key 是欄位名稱, value 是一個 list
    裡面包含了 `ErrorDetail` 物件, `ErrorDetail` 可能不只有一個, 同一個欄位可能會同時有多個錯誤

    類型: dict{欄位名稱: list[ErrorDetail, ErrorDetail]}
    範例物件: {'email': [ErrorDetail(string='這個 Email 在 帳號 已經存在。', code='unique')],
     'first_name': [ErrorDetail(string='Ensure this field has no more than 30 characters.', code='max_length')]}
    """
    for field_name, error_detail_list in errors.items():
        for error_detail in error_detail_list:
            if error_detail.code == code:
                return field_name, str(error_detail)
    return None