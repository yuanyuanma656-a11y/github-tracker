import logging

from config import LOG_DIR, LOG_FILE


def setup_logger() -> logging.Logger:
    """创建并配置项目日志记录器。"""

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger("github_tracker")

    # 防止重复添加 Handler
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # 写入日志文件
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 输出到终端
    console_handler = logging.StreamHandler()

    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()