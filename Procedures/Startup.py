# import the dfttool functionalities
print(f'... Startup Procedure ......')
from dfttools import VFORCE
# force 14V on "VCC" pin wrt GND1+
VFORCE(signal="VCC",reference="GND1m",value=14)