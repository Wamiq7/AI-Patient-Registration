import logging
import time


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


def setup_logging(level: str) -> None:
    root = logging.getLogger()
    log_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(log_level)

    if root.handlers:
        for handler in root.handlers:
            handler.setLevel(log_level)
        return

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(
        UTCFormatter(
            fmt="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
