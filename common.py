import os
from box.exceptions import BoxValueError
import yaml
from logger import log 
import json
from ensure import ensure_annotations
from box import ConfigBox
from typing import Union


@ensure_annotations
def read_yaml(path_to_yaml) -> ConfigBox:
    try:
        with open(path_to_yaml) as yaml_file:
            content = yaml.safe_load(yaml_file)
            log.info(f"yaml file: {path_to_yaml} loaded successfully")
            return ConfigBox(content)
    except BoxValueError:
        raise ValueError("yaml file is empty")
    except Exception as e:
        raise e
    
ivm6201 = read_yaml('ivm6201.yaml').ivm6201
def ivm6201_pin_check(pin='', pins=list(ivm6201.pins.values()) ):
    return pin.lower() in ''.join(pins).lower()
    # return pin in pins
        
