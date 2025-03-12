from enum import Enum, auto

class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"

class Language(Enum):
    ZH_CN = "zh_CN"
    EN_US = "en_US"

class CloseAction(Enum):
    ASK = "ask"  # 每次询问
    MINIMIZE = "minimize"  # 最小化到托盘
    EXIT = "exit"  # 退出程序

    @classmethod
    def get_display_name(cls, value):
        display_names = {
            cls.ASK: "每次询问",
            cls.MINIMIZE: "缩小到托盘",
            cls.EXIT: "退出程序"
        }
        return display_names.get(value, str(value)) 