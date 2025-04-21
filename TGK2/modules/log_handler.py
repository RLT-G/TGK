import logging
from datetime import datetime
from colorama import Fore, Style, init
from modules.settings import LOGGER_TZ

init(autoreset=True)  


class MoscowFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.CYAN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA + Style.BRIGHT
    }

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=LOGGER_TZ)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S")

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        log_message = super().format(record)
        if record.levelno >= logging.ERROR:
            return log_color + Style.BRIGHT + log_message + Style.RESET_ALL
        return log_color + log_message + Style.RESET_ALL


logger = logging.getLogger("custom_logger")
logger.setLevel(logging.DEBUG)  


formatter = MoscowFormatter("%(asctime)s - %(levelname)s - %(message)s")


console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)


file_handler = logging.FileHandler("tgk_logs.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)


logger.addHandler(console_handler)
logger.addHandler(file_handler)


if __name__ == '__main__':
    logger.debug("It is DEBUG msg")
    logger.info("It is INFO msg")
    logger.warning("It is WARNING msg")
    logger.error("It is ERROR msg")
    logger.critical("It is CRITICAL msg")
