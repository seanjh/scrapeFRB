import os.path
import logging
import logging.handlers

def configure_logger(name, path):
    # Create log handlers
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s (%(module)s): %(message)s', 
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )

    file_name = os.path.join(path, 'frb.log')
    fh = logging.handlers.TimedRotatingFileHandler(
        file_name, when='midnight', interval=1, backupCount=5
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    return logger