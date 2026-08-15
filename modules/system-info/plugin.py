"""系统信息模块"""

import platform
import psutil


def init():
    """模块初始化：注册 widget"""
    register_widget(
        name="system",
        label="系统信息",
        description="本地系统基本信息",
        icon="monitor",
        refresh_interval=60,
        handler=get_system_info,
    )


def get_system_info():
    """获取系统信息"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
    except ImportError:
        cpu_percent = 0
        memory = None

    return {
        "status": "ok",
        "label": "系统信息",
        "data": {
            "platform": f"{platform.system()} {platform.release()}",
            "hostname": platform.node(),
            "python": platform.python_version(),
            "cpu": f"{cpu_percent}%" if cpu_percent else "N/A",
            "memory": f"{memory.percent}%" if memory else "N/A",
        },
    }