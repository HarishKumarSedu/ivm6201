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
import random 
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
    
ivm6201_config = read_yaml('ivm6201.yaml').ivm6201
def ivm6201_pin_check(pin='', pins=list(ivm6201_config.pins.values()) ):
    return pin.lower() in ''.join(pins).lower()
    # return pin in pins

def get_device(deviceNo=0):
    if device := Device(devnum=deviceNo):
        return device
    else:
        print(f'!!!!!!!!!!!!!!!!!!!! fail :> MCP not presetn ')
        return None

def get_slave(device: Device,address=ivm6201_config.Address):
    try:
        if device.I2C_read(address):
            sleep(0.01)
            return device.I2C_Slave(address)
        else:
            print(f'!!!!!!!!!!!!!!! fail:> slave not present with address {address}')
            return None
    except EasyMCP2221.exceptions.NotAckError:
        print(f'!!!!!!!!!!!!!!! fail:> slave not present with address {address}')
        return None

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
def I2C_read_multiple_registers(slave, registers:[]):
    bitwidth_filled = 0
    final_value = 0
    if slave:
        # check if there is an empty registers 
        if registers:
            for register in registers:
                register_addr = register.get('address')
                msb = register.get('msb')
                lsb = register.get('lsb')
                register_data = I2C_read_register_bits(slave=slave, register_addr=register_addr, msb=msb, lsb=lsb)
                register_data = random.randint(0,2)
                final_value = (register_data << bitwidth_filled) + final_value
                bitwidth_filled = (msb-lsb+1) + bitwidth_filled
                # print(f'read register: {register} register data: {register_data} value:{hex(final_value)} ')
        return final_value
    else:
        return None
# write mulitple registers
def I2C_write_multiple_registers(slave, registers:[],value=Union[int|float]):
    value = int(value)
    bitwidth_filled = 0
    if slave:
        # check if there is an empty registers 
        if registers:
            for register in registers:
                register_addr = register.get('address')
                msb = register.get('msb')
                lsb = register.get('lsb')
                mask = (2**(msb-lsb+1)-1) << bitwidth_filled
                new_value = (value & mask) >> bitwidth_filled
                register_data = I2C_write_register(slave=slave, register=register,value=new_value)
                bitwidth_filled = (msb-lsb+1) + bitwidth_filled
                # print(f'write register = {register}, value={hex(new_value)}')
            return I2C_read_multiple_registers(slave=slave, registers=registers)
        else : return None
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
    # slave = get_slave(device=device,address=ivm6201_config.Address)
    # select page 0 
    # I2C_write_register(slave=slave, register={'address':0xFE, 'msb':7, 'lsb':0}, value=0)
    # print('Device id and version id ', I2C_read_register(slave=slave, register_addr=0xFF))
    # print('Device id',I2C_read_register_bits(slave=slave,register_addr=0xFE, msb=7,lsb=3))
    final_value = I2C_write_multiple_registers(slave=None, registers=[{'address':0x01, 'msb':7, 'lsb':0},{'address':0x02, 'msb':3, 'lsb':1},{'address':0x03, 'msb':3, 'lsb':3}],value=int(0x9f0))
    print(hex(final_value))
    # print(hex(I2C_read_multiple_registers(slave=None, registers=[{'address':0x01, 'msb':7, 'lsb':0},{'address':0x02, 'msb':3, 'lsb':2}])))
