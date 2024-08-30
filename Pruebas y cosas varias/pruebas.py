""" This example demonstrates how to use the FMU.get*() and FMU.set*() functions
 to set custom input and control the simulation """

from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result, download_test_file
import numpy as np
import shutil



# define the model name and simulation parameters
fmu_filename = 'bouncingBall.fmu'

# read the model description
model_description = read_model_description(fmu_filename)

print(model_description)

for variable in model_description.modelVariables:
    print(variable)
    