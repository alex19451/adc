import logging
import pathlib
import yaml
import os
import time
import hashlib
import gitlab
from config import *

def get_custom_logger(name, instance, level):
    """
    Writes messages to the log file.
    Log levels mapping: CRITICAL=50, ERROR=40, WARNING=30, INFO=20, DEBUG=10
    """
    level = logging.INFO if level == "INFO" else logging.DEBUG
    logs_dir = 'log'
    log_file = f'{logs_dir}/{name}-{instance}.log'
    pathlib.Path(logs_dir).mkdir(parents=True, exist_ok=True)
    if LOGGERS.get(name):
        logger = LOGGERS.get(name)
    else:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        fh = logging.FileHandler(filename=log_file)
        fh.setLevel(level)
        formatter = logging.Formatter(fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        LOGGERS.update({name: logger})
    return logger

def yaml_writer(data, dir, file, mode="w"):
    """
    Writes JSON data to the YAML file
    """
    with open(os.path.join(dir, file), mode) as file:
        yaml.safe_dump(data, file)


def retry_with_active(retries,sleep):
    """
    Decorator retry
    """
    def inner(f):
        def wrapper(*args, **kwargs):
          x = 0
          while True:
            try:
              result = f(*args, **kwargs)
              if result.status =="success":
                return "OK"
              else:
                 time.sleep(sleep)
                 x+=1
            except (gitlab.exceptions.GitlabError,gitlab.exceptions.GitlabHttpError,gitlab.exceptions.GitlabGetError,
                    gitlab.exceptions.GitlabCancelError,gitlab.exceptions.GitlabConnectionError,gitlab.exceptions.GitlabCreateError) as e:
              if x == retries:
                return "NOT OK"
              else:
                time.sleep(sleep)
                x += 1
        return wrapper
    return inner


def get_vars_values(dir, vars_file) -> dict:
    """
    Get VPN vars from file with variables in .yaml format
    :returns: VPN variables
    """
    with open(os.path.join(dir, vars_file), 'r') as file:
        return yaml.safe_load(file)

def to_hash_256(value) -> str:
    """
    Hash form password
    """
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def upload_file(upload, dir)->None:
    """
    Upload file
    """
    filename = upload.filename
    file = os.path.join(dir, filename)
    upload.save(file)

def file_params(dir) -> list:
    """
    Params for file
    """
    files_data = list()
    for file in os.listdir(dir):
        file_data = dict()
        filepath = os.path.join(dir, file)
        file_data['name'] = file
        file_data['path'] = filepath
        files_data.append(file_data)
    return files_data
