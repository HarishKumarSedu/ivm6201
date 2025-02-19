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
    if pin:
        return pin.lower() in ''.join(pins).lower()
    else:
        return None
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

        
def I2C_read_register_bits(slave,register_addr:Union[int,hex],msb:int,lsb: int):
    try:
        if slave:
            # check if the lsb and msb mentioned in absolute bit postion 
            msb = msb-8 if msb >=8 else msb
            lsb = msb-8 if lsb >=8 else lsb
            bit_width = 2**(msb - lsb+1)
            mask = ((bit_width-1) << lsb)
            device_data = int.from_bytes(slave.read_register(register_addr),'little')
            # print(f' register read full {hex(register_addr)} {hex(device_test)}')
            device_bitmodified_data = (device_data & mask) >> lsb
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
        print(register,value)
        # check if the lsb and msb mentioned in absolute bit postion 
        msb = msb-8 if msb >=8 else msb
        lsb = msb-8 if lsb >=8 else lsb
        device_data = I2C_read_register(slave=slave,register_addr=register_addr) # write the existing data
        # print(f'data read {register_addr}',device_data)
        bit_width = 2**(msb - lsb+1)
        mask = ~((bit_width-1) << lsb)
        device_data = (device_data & mask) | ((int(value)) << lsb) # modify the data
        slave.write([register_addr,device_data])
        device_data = I2C_read_register(slave=slave,register_addr=register_addr) # read dat back to confirm writing
        # print(f'data read {register_addr} ({hex(register_addr)})',hex(device_data))
        return device_data
    
    else:
        return None
def I2C_read_multiple_registers(slave, registers:[]):
    bitwidth_filled = 0
    final_value = 0
    register_data=0
    if slave:
        # check if there is an empty registers 
        if registers:
            for register in registers[::-1]:
                register_addr = register.get('address')
                msb = register.get('msb')
                lsb = register.get('lsb')
                # check if the lsb and msb mentioned in absolute bit postion 
                msb = msb-8 if msb >=8 else msb
                lsb = msb-8 if lsb >=8 else lsb
                register_data = I2C_read_register_bits(slave=slave, register_addr=register_addr, msb=msb, lsb=lsb)
                # register_data = random.randint(0,2)
                final_value = (register_data << bitwidth_filled) | final_value
                bitwidth_filled = (msb-lsb+1) + bitwidth_filled
                # print(f' register {hex(register_addr)} value = {hex(final_value)}')
                # print(f'read register: {register} register data: {hex(register_data)} value:{hex(final_value)} ')
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
            for register in registers[::-1]:
                register_addr = register.get('address')
                msb = register.get('msb')
                lsb = register.get('lsb')
                # check if the lsb and msb mentioned in absolute bit postion 
                msb = msb-8 if msb >=8 else msb
                lsb = msb-8 if lsb >=8 else lsb
                mask = (2**(msb-lsb+1)-1) << bitwidth_filled
                new_value = (value & mask) >> bitwidth_filled
                register_data = I2C_write_register(slave=slave, register=register,value=new_value)
                bitwidth_filled = (msb-lsb+1) + bitwidth_filled
                # print(f'write register = {register}, value={hex(register_data)}')
            return I2C_read_multiple_registers(slave=slave, registers=registers)
        else : return None
    else:
        return None
def device_test():
        # Connect to MCP2221
    mcp = EasyMCP2221.Device()

    print("Searching...")

    for addr in range(0, 0x7F):
        try:
            mcp.I2C_read(addr)
            print("I2C slave found at address 0x%02X" % (addr))

        except EasyMCP2221.exceptions.NotAckError:
            pass

if __name__=='__main__':
    device = get_device()
    # device_test()
    slave = get_slave(device=device,address=ivm6201_config.Address)
    # select page 0 
    I2C_write_register(slave=slave, register={'address':0xFE, 'msb':0, 'lsb':0}, value=int(0x0))
    I2C_write_register(slave=slave, register={'address':0x18, 'msb':2, 'lsb':0}, value=int(0x7))
    # print('Device id and version id ', hex(I2C_read_register(slave=slave, register_addr=0xFF)))
    # print('device id',hex(I2C_read_register_bits(slave=slave,register_addr=0xFF, msb=7,lsb=3)))
    print('8bit data ', hex(I2C_read_register(slave=slave, register_addr=0x18)))
    # print('bit data',hex(I2C_read_register_bits(slave=slave,register_addr=0x0, msb=1,lsb=0)))
    # final_value = I2C_write_multiple_registers(slave=slave, registers=[{'address':0x20, 'msb':0, 'lsb':0},{'address':0xFC, 'msb':1, 'lsb':0}],value=int(0x6))
    # print(hex(final_value))
    # print(hex(I2C_read_register_bits(slave=slave, register_addr=0xFC,msb=1,lsb=0)))
    # print(hex(I2C_read_multiple_registers(slave=slave, registers=[{'address':0x20, 'msb':0, 'lsb':0},{'address':0xFC, 'msb':1, 'lsb':0},])))
