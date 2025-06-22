# import the dfttool functionalities
print(f'... Startup Procedure ......')
from dfttools import VFORCE
# apply vddio @ 1.8v wrt "GND1m"
# force all "VCC"'s @14V wrt "GND1m" 
VFORCE(signal="VCC",reference="GND1m",value=14)
VFORCE(signal="CD/DIAG",reference="GND1m",value=14)