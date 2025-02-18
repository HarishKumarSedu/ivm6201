import os
import sys
import logging
from rich.logging import RichHandler
from pathlib import Path

logging_str = "[%(asctime)s: %(levelname)s: %(module)s: %(message)s]"

log_dir = "logs"
log_filepath = Path(os.path.join(log_dir,"running_logs.log"))
os.makedirs(log_dir, exist_ok=True)


logging.basicConfig(
    level= logging.NOTSET,
    format= logging_str,

    handlers=[
        logging.FileHandler(log_filepath),
        # logging.StreamHandler(sys.stdout)
        RichHandler(),
    ]
)

log = logging.getLogger("IVM6201")