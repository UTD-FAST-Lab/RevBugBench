import logging
import os
import pathlib
import shutil


def mkdir(path: str) -> None:
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def rm_before_mkdir(path: str) -> None:
    if os.path.exists(path):
        logging.warning(f'removing directory before make: {path}')
        shutil.rmtree(path)
    mkdir(path)


def rm_if_exist(path: str) -> None:
    if os.path.exists(path):
        logging.warning(f'removing directory: {path}')
        shutil.rmtree(path)


def error_if_not_exist(path: str) -> None:
    if not os.path.exists(path):
        logging.error(f'{path} does not exist')
        exit(1)
