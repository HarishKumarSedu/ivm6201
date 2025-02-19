import os
from box.exceptions import BoxValueError
import yaml
from logger import log 
import json
from ensure import ensure_annotations
from box import ConfigBox
from typing import Union
import EasyMCP2221
from EasyMCP2221 import Device
from time import sleep
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

def get_device(deviceNo=0):
    try:
        device = Device(devnum=deviceNo)
        return device
    except Exception as e :
        log.error(e)
        return None

def get_slave(device: Device,address=ivm6201.Address):
        try:
            slave = device.I2C_Slave(address)
            sleep(0.01)
            if slave:
                return slave
            else:
                return None
            
        except EasyMCP2221.exceptions.NotAckError:
            print
def I2C_read_register(slave,register_addr:0x00):
    try:
        if slave:
            return int.from_bytes(slave.read_register(register_addr),'little')
        else :
            return None
    except Exception as e:
        print(e)
        
def I2C_read_register_bits(slave,register_addr:0x00,msb:int,lsb: int):
    try:
        if slave:
            bit_width = 2**(msb - lsb+1)
            mask = ((bit_width-1) << lsb)
            device_data = int.from_bytes(slave.read_register(register_addr),'little')
            device_bitmodified_data = int(device_data) >> lsb
            return device_bitmodified_data
        else :
            return None
    except Exception as e:
        print(e)
        
def I2C_write_register(slave,register:dict,value:Union[int,float],*args,**kwargs):
    if slave:
        register_addr = register.get('address')
        msb = register.get('msb')
        lsb = register.get('lsb')
        device_data = I2C_read_register(slave=slave,register_addr=register_addr) # write the existing data
        bit_width = 2**(msb - lsb+1)
        mask = ~((bit_width-1) << lsb)
        device_data = (device_data & mask) | ((int(value)) << lsb) # modify the data
        slave.write([register_addr,device_data])
        return I2C_read_register(slave=slave,register_addr=register_addr)
    else:
        return None
def device_test():
        # Connect to MCP2221
    mcp = EasyMCP2221.Device()

    print("Searching...")

    for addr in range(0, 0x80):
        try:
            mcp.I2C_read(addr)
            print("I2C slave found at address 0x%02X" % (addr))

        except EasyMCP2221.exceptions.NotAckError:
            pass

if __name__=='__main__':
    device = get_device()
    slave = get_slave(device=device,address=ivm6201.Address)
    I2C_write_register(slave=slave, register={'address':0xFE, 'msb':7, 'lsb':0}, value=1)
    print(I2C_read_register(slave=slave, register_addr=0xFE))
    print(I2C_read_register_bits(slave=slave,register_addr=0xFE, msb=7,lsb=0))