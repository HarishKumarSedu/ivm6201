from dfttools import *
from Procedures import Startup,Startup_REF
import numpy as np

I2C_WRITE(device_address="0x68", field_info={'fieldname': 'i2c_page_sel', 'length': 2, 'registers': [{'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG0'}, {'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x01)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'otp_burnt_b', 'length': 1, 'registers': [{'REG': '0x40', 'POS': 7, 'RegisterName': 'OTP register 0', 'RegisterLength': 8, 'Name': 'otp_burnt_b', 'Mask': '0x80', 'Length': 1, 'FieldMSB': 7, 'FieldLSB': 7, 'Attribute': 'NNNNNNNN', 'Default': '80', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x00)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'i2c_page_sel', 'length': 2, 'registers': [{'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG0'}, {'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x01)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'amux2_en', 'length': 1, 'registers': [{'REG': '0x20', 'POS': 1, 'RegisterName': 'Analog test 3', 'RegisterLength': 8, 'Name': 'amux2_en', 'Mask': '0x2', 'Length': 1, 'FieldMSB': 1, 'FieldLSB': 1, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '0000YYYY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x01)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'ref_test_en', 'length': 1, 'registers': [{'REG': '0x1E', 'POS': 5, 'RegisterName': 'Analog test 1', 'RegisterLength': 8, 'Name': 'ref_test_en', 'Mask': '0x20', 'Length': 1, 'FieldMSB': 5, 'FieldLSB': 5, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x01)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'ana_test_sel', 'length': 4, 'registers': [{'REG': '0x1F', 'POS': 0, 'RegisterName': 'Analog test 2', 'RegisterLength': 8, 'Name': 'ana_test_sel[3:0]', 'Mask': '0xF', 'Length': 4, 'FieldMSB': 3, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x06)

# Initial value
low_value = 1.18
typical_value = 1.242
high_value = 1.3
bit_width = {'fieldname': 'ref_vbg_trim', 'length': 4, 'registers': [{'REG': '0xC1', 'POS': 4, 'RegisterName': 'OTP register 129', 'RegisterLength': 8, 'Name': 'ref_vbg_trim[3:0]', 'Mask': '0xF0', 'Length': 4, 'FieldMSB': 3, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}.get('length')

# Number of steps width of the field / bits
num_steps = 2**bit_width  # 4-bit
# Step size
step_size = typical_value / num_steps 
print(step_size)

# Standard deviation for white noise
noise_std_dev = 0.025

# Initialize minimum error and optimal code
min_error = float('inf')
optimal_code = None
optimal_measured_value = None

# Simulate measurements and find the optimal code
for i in range(num_steps):
    # Generate monotonic values with step size
    expected_values = low_value + i * step_size 
    # Add white noise to each value
    noisy_values = expected_values + np.random.normal(0, noise_std_dev) * np.random.choice([1,-1])
    # Pass the noisy value as the expected measurement values
    # SaveMeas__Voltage__hwmute__GND
    measured_value = VMEASURE(signal="CD/DIAG", reference="GND1m", expected_value=noisy_values)
    error = abs(measured_value - typical_value)
    if error < min_error:
        min_error = error
        optimal_code = hex(i)
        optimal_measured_value = measured_value

# Check for limits
if low_value < optimal_measured_value < high_value:
    print(f'............ Trim_Bg Test Passed ........')
    I2C_WRITE(device_address=0x68, field_info="{'fieldname': 'ref_vbg_trim', 'length': 4, 'registers': [{'REG': '0xC1', 'POS': 4, 'RegisterName': 'OTP register 129', 'RegisterLength': 8, 'Name': 'ref_vbg_trim[3:0]', 'Mask': '0xF0', 'Length': 4, 'FieldMSB': 3, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}", write_value=optimal_code)
else:
    print(f'............ Trim_Bg Test Failed ........')
print(f"Optimal Code: {optimal_code}")
print(f"Optimal measured value : {optimal_measured_value}")
print(f"Minimum Error: {min_error}")


