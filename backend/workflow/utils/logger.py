import logging
import os


class _ColorFormatter(logging.Formatter):
    _RESET = "\033[0m"
    _COLORS = {
        logging.DEBUG: "\033[36m",     # cyan
        logging.INFO: "\033[32m",      # green
        logging.WARNING: "\033[33m",   # yellow
        logging.ERROR: "\033[31m",     # red
        logging.CRITICAL: "\033[35m",  # magenta
    }

    def format(self, record: logging.LogRecord) -> str:
        original_levelname = record.levelname
        color = self._COLORS.get(record.levelno, "")
        if color:
            record.levelname = f"{color}{record.levelname}{self._RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


def setup_logging(level: int | None = None) -> None:
    root_logger = logging.getLogger()

    if getattr(root_logger, "_travel_logging_configured", False):
        return

    resolved_level = level
    if resolved_level is None:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        resolved_level = getattr(logging, env_level, logging.INFO)

    handler = logging.StreamHandler()
    setattr(handler, "_travel_color_handler", True)
    handler.setFormatter(
        _ColorFormatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    )

    has_our_handler = any(
        getattr(existing_handler, "_travel_color_handler", False)
        for existing_handler in root_logger.handlers
    )
    if not has_our_handler:
        root_logger.addHandler(handler)

    root_logger.setLevel(resolved_level)
    setattr(root_logger, "_travel_logging_configured", True)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
