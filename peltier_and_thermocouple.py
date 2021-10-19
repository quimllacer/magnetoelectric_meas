# PID for the for the thermoelectric heater-cooler (peltier element)
import sys
import time
import os
import numpy as np
import pandas as pd
import serial
import pyvisa as visa
from datetime import datetime
from simple_pid import PID
from cpx400sp import CPX400SP
from coldplate_commands import COLDPLATE
from general_functions import new_datefolder


#Set parameters    
cpx = CPX400SP('192.168.1.131', 9221)
cp = COLDPLATE("COM5")
tc = serial.Serial('COM4', 9800, timeout=1)
print(cpx.get_identification())
current = 4
voltage = 7
setup_time = 60
loop_time = 200
# Temperature function
temp_ampl = 1
temp_freq = 0.05
temp_slope = 0.05
temp_offset = 100
P = 0.3
I = 0.1
D = 0.05

def sine(tdelta, frequency, amplitude, slope, offset):
        return amplitude * np.sin(2*np.pi*frequency*tdelta) + slope*tdelta + offset


# Initialize
cpx.set_current(current)
cpx.set_voltage(0)
cpx.set_output(1)
tc.flushInput()
tc.flushOutput()
cp.set_tempTarget(temp_offset)
cp.set_tempOn()
tc.readline()
print("Setup time...")
start_time = time.time()
while time.time() - start_time <= setup_time:
    tdelta = round((time.time() - start_time), 2)
    print([tdelta,
               tc.readline().decode().strip(),
               round(cp.get_tempActual(),1)])
tc.flushInput()
tc.flushOutput()

# Set variables
pid = PID(P, I, D, setpoint=temp_offset, sample_time = 0.1)
start_time = time.time()
data = []
starting_peltier_voltage = 0


# Loop
print("Loop time...")
while time.time() - start_time <= loop_time:
    if voltage > 7:
        voltage = 7
    tdelta = round((time.time() - start_time), 2)
    ext_temp = float(tc.readline().decode().strip())
    cpx.set_voltage(voltage)
    cpx.set_output(1)
    reading = [tdelta,
               float(cpx.get_voltage()[:-2]),
               float(cpx.get_current()[:-2]),
               ext_temp,
               round(cp.get_tempActual(),1)]
    print(reading)
    data.append(reading)
    voltage = pid(ext_temp)
    # Set new target temperature
    new_target_temp = sine(tdelta,
                           frequency = temp_freq,
                           amplitude = temp_ampl,
                           slope = temp_slope,
                           offset = temp_offset)
    pid.setpoint = new_target_temp


cpx.set_voltage(0)
cpx.set_output(0)
tc.close()
del cp

# Define measurement file name
name = "/{}__{}expt__{}P__{}I__{}D".format(datetime.now().strftime("%Hh%Mm%Ss"),
                                           loop_time,
                                           P,
                                           I,
                                           D)
file_name = new_datefolder("data") + name
print("File name: " + file_name)

df = pd.DataFrame(data, columns = ["time",
                                       "voltage",
                                       "current",
                                       "ext_tempereture",
                                       "int_temperature"])

df.to_excel('{}.xlsx'.format(file_name))




# pid = PID(P, 0.1, 0.05, setpoint=40)

# # Assume we have a system we want to control in controlled_system
# v = controlled_system.update(starting_voltage)
# print(k.read_latest()[-1])


# while True:
#     # Compute new output from the PID according to the systems current value
#     new_voltage_setpoint = pid(current_temperature)

#     # Feed the PID output to the system and get its current value
#     v = controlled_system.update(new_voltage_setpoint)
