def KeyboardButton(*rows, resize_keyboard: bool = True, one_time_keyborad: bool = False):
    return {
        "keyboard": list(rows),
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyborad
    }
