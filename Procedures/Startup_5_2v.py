# import the dfttool functionalities
from dfttools import VFORCE
# force 5.2V on "VCC" pin wrt GND1+
VFORCE(signal="VCC",reference="GND1p",value=5.2)