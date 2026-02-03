import argparse
import datetime
import os.path
import sys
from datetime import timedelta

import tomli
from pathlib import Path

class Config:
    cfg_path: str = Path(__file__).parent.parent.parent / "config.toml"
    def __init__(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--config", "-c",
            metavar="PATH",
            default=self.cfg_path,
            help=f"Path to config file (Default: {self.cfg_path})"
        )
        args = parser.parse_args()
        if not args.config:
            self.cfg_path = args.config
        if not os.path.exists(self.cfg_path):
            print(f"file {self.cfg_path} not found")
            sys.exit(1)
        try:
            with open(self.cfg_path, "rb") as cfg:
                config_data = tomli.load(cfg)
                self.app = config_data.get("app", {})
                self.storage = config_data.get("storage", {})
                self.log = config_data.get("logger", {})
        except FileNotFoundError as e:
            print(f"File {e} not found")
            sys.exit(1)
        except tomli.TOMLDecodeError as e:
            print(f"Invalid TOML format in {self.cfg_path}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading config: {e}")
            sys.exit(1)
        except KeyError as e:
            print(f"Missing required key in config: {e}")
            sys.exit(1)

    @property
    def env(self) -> str:
        return self.app.get("env", "local")

    @property
    def schedule_update(self) -> int:
        return self.app.get("schedule_update")

    @property
    def root_dir(self) -> Path:
        root_str = self.app.get("root", "")
        expanded_root = os.path.expanduser(root_str)
        return Path(expanded_root)

    @property
    def storage_path(self) -> Path:
        storage_path_str = self.storage.get("path")
        return self.root_dir / storage_path_str

    @property
    def db_name(self) -> str:
        return self.storage.get("name")

    @property
    def log_path(self) -> Path:
        log_path_str = self.log.get("path", "./src/logger")
        return self.root_dir / log_path_str

    @property
    def log_name(self) -> str:
        return self.log.get("name")

