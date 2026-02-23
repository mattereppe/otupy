import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path

class LoggerManager:
    def __init__(self, logfile: Path, json_logs: bool = False, level: int = logging.INFO):
        self.logger = logging.getLogger("EBPFManager")
        self.logger.setLevel(level)
        if not self.logger.handlers:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            if json_logs:
                formatter = self.JSONFormatter()
            fh = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=3)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            self.logger.addHandler(logging.StreamHandler())

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            return json.dumps({
                "time": self.formatTime(record),
                "level": record.levelname,
                "msg": record.getMessage()
            })