import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger("pipeline")
    if logger.handlers:
        return logger  # éviter doublons

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Fichier
    fh = RotatingFileHandler("pipeline.log", maxBytes=5_000_000, backupCount=3)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
