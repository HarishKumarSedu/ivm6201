# Import necessary modules 
from dfttools import *
from Procedures import Startup
from Procedures import Startup_REF
import numpy as np
Test_name = 'FRO_Trim'
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'i2c_page_sel', 'length': 2, 'registers': [{'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG0'}, {'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x01)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'otp_burnt_b', 'length': 1, 'registers': [{'REG': '0x40', 'POS': 7, 'RegisterName': 'OTP register 0', 'RegisterLength': 8, 'Name': 'otp_burnt_b', 'Mask': '0x80', 'Length': 1, 'FieldMSB': 7, 'FieldLSB': 7, 'Attribute': 'NNNNNNNN', 'Default': '80', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x00)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'i2c_page_sel', 'length': 2, 'registers': [{'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG0'}, {'REG': '0xFE', 'POS': 0, 'RegisterName': 'Page selection', 'RegisterLength': 8, 'Name': 'i2c_page_sel', 'Mask': '0x1', 'Length': 1, 'FieldMSB': 0, 'FieldLSB': 0, 'Attribute': '0000000N', 'Default': '00', 'User': '000000YY', 'Clocking': 'SMB', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x01)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'dig_test_en', 'length': 5, 'registers': [{'REG': '0x03', 'POS': 0, 'RegisterName': 'Digital Test settings 1', 'RegisterLength': 8, 'Name': 'dig_test_en[4:0]', 'Mask': '0x1F', 'Length': 5, 'FieldMSB': 4, 'FieldLSB': 0, 'Attribute': '000NNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x02)
I2C_WRITE(device_address="0x68", field_info={'fieldname': 'dig_test_sel', 'length': 8, 'registers': [{'REG': '0x04', 'POS': 0, 'RegisterName': 'Digital Test settings 2', 'RegisterLength': 8, 'Name': 'dig_test_sel[7:0]', 'Mask': '0xFF', 'Length': 8, 'FieldMSB': 7, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0x02)

typical_frequency = 3e6  # 3 MHz 
# Calculate the acceptable range of frequencies based on a ±15% tolerance 
error_percentage = 0.15
error_spread = typical_frequency*error_percentage
low_frequency = typical_frequency - (typical_frequency * error_percentage)  # Lower limit of acceptable frequency 
high_frequency = typical_frequency + (typical_frequency * error_percentage)  # Upper limit of acceptable frequency 

### Trimming Parameters 
# Step size for trimming (frequency adjustment per step) 
bit_width = {'fieldname': 'ref_fro_trim', 'length': 3, 'registers': [{'REG': '0xC1', 'POS': 0, 'RegisterName': 'OTP register 129', 'RegisterLength': 8, 'Name': 'ref_fro_trim[2:0]', 'Mask': '0x7', 'Length': 3, 'FieldMSB': 2, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}.get('length')
num_steps = 2**bit_width  # 3-bit resolution gives 8 steps 
step_size = (high_frequency - low_frequency) / (num_steps)  # Step size in Hz 
# Standard deviation for white noise in frequency measurement (simulating real-world noise) 
noise_std_dev = 1000  # Noise in Hz 

### Initialization 
# Initialize variables to track the minimum error and corresponding trim code 
min_error = float('inf')
optimal_code = None
optimal_measured_frequency = None

### Trimming Loop 
# Simulate measurements and find the optimal trim code that minimizes frequency error 
for i in range(num_steps):
    # Generate expected frequency values based on step size 
    expected_frequency = low_frequency + i * step_size   
    # Set the trim value for the current iteration 
    I2C_WRITE(device_address=0x68, field_info={'fieldname': 'ref_fro_trim', 'length': 3, 'registers': [{'REG': '0xC1', 'POS': 0, 'RegisterName': 'OTP register 129', 'RegisterLength': 8, 'Name': 'ref_fro_trim[2:0]', 'Mask': '0x7', 'Length': 3, 'FieldMSB': 2, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=i)
    # Measure the actual frequency value (simulated here as noisy_frequency) 
    measured_frequency = FREQMEASURE(signal="I2SData1", reference="GND1m", expected_value=expected_frequency,error_spread=error_spread)
    # Calculate the error between measured and typical frequencies 
    error = abs(measured_frequency - typical_frequency)
    
    # Update optimal trim code if a smaller error is found 
    if error < min_error:
        min_error = error
        optimal_code = hex(i)  # Save the trim code corresponding to minimum error 
        optimal_measured_frequency = measured_frequency

### Output Results 
# Output results of the trimming process 
print(f"Optimal Trim Code: {optimal_code}")
print(f"Optimal Measured Frequency: {optimal_measured_frequency} Hz")
print(f"Minimum Frequency Error: {min_error} Hz")

### Validation and Finalization 
# Check if the measured frequency falls within the acceptable range 
if low_frequency < optimal_measured_frequency < high_frequency:
    print(f'............ {Test_name} Trim  Passed ........')
    # Write the optimal trim code to the FRO trim register 
    I2C_WRITE(device_address=0x68, field_info={'fieldname': 'ref_fro_trim', 'length': 3, 'registers': [{'REG': '0xC1', 'POS': 0, 'RegisterName': 'OTP register 129', 'RegisterLength': 8, 'Name': 'ref_fro_trim[2:0]', 'Mask': '0x7', 'Length': 3, 'FieldMSB': 2, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=optimal_code)
else:
    print(f'............ {Test_name} Trim  Failed ........')
    I2C_WRITE(device_address=0x68, field_info={'fieldname': 'ref_fro_trim', 'length': 3, 'registers': [{'REG': '0xC1', 'POS': 0, 'RegisterName': 'OTP register 129', 'RegisterLength': 8, 'Name': 'ref_fro_trim[2:0]', 'Mask': '0x7', 'Length': 3, 'FieldMSB': 2, 'FieldLSB': 0, 'Attribute': 'NNNNNNNN', 'Default': '00', 'User': '00000000', 'Clocking': 'FRO', 'Reset': 'C', 'PageName': 'PAG1'}]}, write_value=0)
