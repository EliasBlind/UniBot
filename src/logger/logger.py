import logging

import src.config.config as config

def configure(cfg: config.Config):
    if cfg.env in ("local", "development"):
        log_level = logging.DEBUG
    elif cfg.env == "production":
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    cfg.log_path.mkdir(parents=True, exist_ok=True)
    log_file_path = cfg.log_path / cfg.log_name

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info(f" Logger was configurate. Level: {logging.getLevelName(log_level)}")