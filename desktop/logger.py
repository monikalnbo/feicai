"""Simple file logger for FeiCai."""

import os
import sys
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOG_FILE = os.environ.get("FEICAI_LOG", str(ROOT / "data" / "feicai.log"))
LOG_LEVEL = os.environ.get("FEICAI_LOG_LEVEL", "INFO").upper()


def setup_logger(name="feicai"):
    """初始化日志系统：输出到文件 + 控制台"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件 handler
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    # 控制台 handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = setup_logger()


def try_with_log(fn, fallback=None, msg=""):
    """try/if 模式：执行函数，失败写日志，返回 fallback"""
    try:
        return fn()
    except Exception as e:
        logger.error(f"{msg}: {e}")
        return fallback


async def try_with_log_async(fn, fallback=None, msg=""):
    """异步版 try_with_log"""
    try:
        return await fn()
    except Exception as e:
        logger.error(f"{msg}: {e}")
        return fallback