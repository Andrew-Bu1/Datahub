import logging
import sys


class CustomFormatter(logging.Formatter):

    DEBUG = "\x1b[2;37m"  # dim white
    INFO = "\x1b[36m"     # cyan
    WARNING = "\x1b[38;5;214m"    # orange/yellow
    ERROR = "\x1b[38;5;196m"      # red
    CRITICAL = "\x1b[1;38;5;201m" # bold magenta
    RESET = "\x1b[0m"


    BASE_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    FORMATS = {
        logging.DEBUG: DEBUG + BASE_FMT + RESET,
        logging.INFO: INFO + BASE_FMT + RESET,
        logging.WARNING: WARNING + BASE_FMT + RESET,
        logging.ERROR: ERROR + BASE_FMT + RESET,
        logging.CRITICAL: CRITICAL + BASE_FMT + RESET,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self.DATE_FMT)
        return formatter.format(record)


def setup_logging(level: int | str = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)

    fmt = CustomFormatter()
    handler.setFormatter(fmt)
    root.addHandler(handler)
