from loguru import logger
import sys
import json
from pathlib import Path

def format_message(record):
    """Custom format for log messages to avoid extra newlines in JSON logs."""
    return record["message"]

class NebulaLogger:
    def __init__(self):
        self.logger = logger
        self.logger.remove()  # Remove default handler to ensure full control

    def add_file_transport(self, log_dir: Path, rotation="00:00", retention="10 days", serialize=True):
        """
        Adds a file transport for logging.

        Args:
            log_dir (Path): The directory to store log files.
            rotation (str, optional): When to rotate the log file. Defaults to "00:00".
            retention (str, optional): How long to keep log files. Defaults to "10 days".
            serialize (bool, optional): Whether to serialize log records to JSON. Defaults to True.
        """
        log_file = log_dir / "nebula_cli_{time:YYYY-MM-DD}.log"
        self.logger.add(
            log_file,
            rotation=rotation,
            retention=retention,
            serialize=serialize,
            level="DEBUG",
            format=format_message,
            catch=True,
            enqueue=True,
        )

    def add_console_transport(self, level="INFO"):
        """
        Adds a console transport for logging.

        Args:
            level (str, optional): The minimum log level to display. Defaults to "INFO".
        """
        self.logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )

    def get_logger(self):
        return self.logger

# --- JSON Log Structure ---
# The `serialize=True` option in Loguru will produce JSON logs with the following structure:
# {
#   "text": "Log message",
#   "record": {
#     "elapsed": { "repr": "0:00:00.000123", "seconds": 0.000123 },
#     "exception": null,
#     "extra": {},
#     "file": { "name": "app.py", "path": "/path/to/src/nebula_cli/app.py" },
#     "function": "some_function",
#     "level": { "icon": "ℹ️", "name": "INFO", "no": 20 },
#     "line": 42,
#     "message": "Log message",
#     "module": "app",
#     "name": "nebula_cli.app",
#     "process": { "id": 12345, "name": "MainProcess" },
#     "thread": { "id": 54321, "name": "MainThread" },
#     "time": { "repr": "2025-09-04 15:00:00.000+00:00", "timestamp": 1756988400.0 }
#   }
# }

def setup_logging():
    """
    Configures and returns a logger instance for the Nebula CLI.
    """
    log_dir = Path("./.logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    nebula_logger = NebulaLogger()
    nebula_logger.add_file_transport(log_dir)
    # By default, we might not want console output unless specified by a verbose flag.
    # nebula_logger.add_console_transport() 
    
    return nebula_logger.get_logger()

log = setup_logging()