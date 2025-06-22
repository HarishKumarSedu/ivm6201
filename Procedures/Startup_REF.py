# import all the functionalities of the dfttools library
from dfttools import *
import time
# force 4V on ENABLE pin wrt GND1+
VFORCE(signal="Enable",reference="GND1m",value=4)
VFORCE(signal="V5VDR",reference="GND1m",value=5.2)
# VFORCE(signal=VDDIO,reference=GND1-,value=1.8)
# enable pll 
I2C_WRITE( device_address=0x68, field_info=i2c_page_sel, write_value=0x00)
I2C_WRITE( device_address=0x68, field_info=i2c_unlock, write_value=0x01)
I2C_WRITE( device_address=0x68, field_info=tdm_fsyn_rate, write_value=0x01)
I2C_WRITE( device_address=0x68, field_info=unlock_tst_addr, write_value=0xAA)
I2C_WRITE( device_address=0x68, field_info=unlock_tst_addr, write_value=0xBB)
I2C_WRITE( device_address=0x68, field_info=i2c_page_sel, write_value=0x01)
I2C_WRITE( device_address=0x68, field_info=force_pll_en, write_value=0x01)
I2C_WRITE( device_address=0x68, field_info=pll_en_m, write_value=0x01)
I2C_WRITE( device_address=0x68, field_info=otp_burn, write_value=0x01)
I2C_WRITE( device_address=0x68, field_info=i2c_page_sel, write_value=0x01)






