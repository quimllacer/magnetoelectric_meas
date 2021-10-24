# ============================================================================
# Name        : coldplate_example.py
# Author      : Joaquin llacer (jwintle@ethz.ch)
# Version     : 1.0.0
# Created on  : 31.03.2021
# Copyright   :
# Description : This is an example script on how to control the QInstruments Coldplate.
# ============================================================================

#!/usr/bin/env python3

import sys
import time
import os
import numpy as np
import pandas as pd
import pyvisa as visa
from datetime import datetime
import matplotlib.pyplot as plt

from general_functions import new_datefolder
from data_analysis import analyze
from keithley6517_commands import KEITHLEY6517
from osensapy import osensapy
from cpx400sp import CPX400SP

def main():

    # Set parameters
    # *********************************************************************************
    sample_identification = "test"
    loop_time = 60*1  # Time that current vs temperature will be measured.
    # CPX Voltage function
    volt_ampl = 22.3
    volt_freq = 0.1
    # Keithley
    current_range = 20E-9 # Upper current range limit.
    nplcycles = 1 # Integration period based on power line frequency (0.01-10)
    average_window = 0 # Average filter window
    # *********************************************************************************
    # Safety
    assert volt_ampl <= 23

    # Initiate communication with the devices
    k = KEITHLEY6517("ASRL/dev/ttyUSB1::INSTR", baud_rate = 19200, sleep = 0.05)
    cpx = CPX400SP('192.168.1.131', 9221)
    transmitter = osensapy.Transmitter("COM3", 247)

    # Functions
    def setup_keithley(current_range, nplcycles, average_window):
        # Reset device to defaults
        k.reset()
        k.clear_reg()
        k.status_queue_next("Reset")

        # Select sensing function
        k.sense_function("'current'")
        k.status_queue_next("Sensing function")

        # Zero correct
        k.current_range(20E-12)
        k.system_zcorrect("ON")
        k.status_queue_next("Zero correct")

        # Select measurement range of interest
        k.current_range(current_range)
        k.system_zcheck("OFF")
        k.status_queue_next("Current range")

        # Integration time
        k.current_nplcycles(nplcycles)
        k.system_pwrlinesync("OFF")
        k.status_queue_next("Integration time")

        # Timestamp
        k.system_tstamp_type("relative")
        k.system_tstamp_relative_reset()
        k.system_tstamp_format("absolute")
        k.status_queue_next("Timestamp")

        # Median filter
        k.current_median_state("ON")
        k.current_median_rank(1)
        k.status_queue_next("Median filter")

        # Average filter
        if average_window != 0:
            k.current_average_state("OFF")
            k.current_average_type("scalar")
            k.current_average_tcontrol("repeat")
            k.current_average_count(average_window)
            k.status_queue_next("Average filter")

        # External temperature
        k.system_tscontrol("ON")
        k.status_queue_next("External temperature")

        # Data format
        k.format_elements(elements = "tstamp, reading")
        k.status_queue_next("Data format")

        # Timeout
        k.pyvisa_timeout(10000) # In milliseconds
    def counter(seconds, message, delay = 1):
        start_time = time.time()
        while time.time() - start_time <= seconds:
            tdelta = time.time() - start_time
            time_left = round(seconds-tdelta, 1)
            print("Time left: {}, {}".format(time_left, message))
            time.sleep(delay)
    def sine(tdelta, frequency, amplitude, slope, offset):
        return amplitude * np.sin(2*np.pi*frequency*tdelta) + slope*tdelta + offset
    def square(tdelta, frequency, amplitude):
        if round(sine(tdelta, frequency, 1, 0, 0), 3) <= 0:
            square = 0
        else:
            square = amplitude
        applied_funct_voltage = square
        return applied_funct_voltage
    def reading_period(df, column_name):
        timedeltas = [df[column_name][i-1] - df[column_name][i] for i in range(1, len(df[column_name]))]
        sampling_rate = abs(sum(timedeltas))/len(timedeltas)
        print("Sampling rate was: {} ms".format(round(sampling_rate*1000, 3)))


    # Setup
    print("Setting up the AMF...")
    cpx.set_output(1)
    cpx.set_current(20)
    cpx.set_voltage(0)
    print("Setting up the electrometer...")
    setup_keithley(current_range = current_range, nplcycles = 1, average_window = average_window)
    k.system_tstamp_relative_reset()
    print("Finished setup, ready to start measurement.")

    # Set variables
    start_time = time.time()
    subset = []
    data = []

    cpx_target_voltage = 0

    # Loop
    while time.time() - start_time <= loop_time:
        # Measure and save
        reading = k.read_latest()
        tdelta = reading[1]
        osensa_temp = transmitter.read_channel_temp("A")
        reading.insert(3, float(cpx.get_current()[:-2]))
        reading.insert(3, float(cpx.get_voltage()[:-2]))
        reading.insert(3, round(cpx_target_voltage, 3))
        reading.insert(3, round(osensa_temp, 3))
        data.append(reading)
        print(reading)

        # Set new target voltage
        cpx_target_voltage = square(tdelta,
                               frequency = volt_freq,
                               amplitude = volt_ampl)
        assert cpx_target_voltage <= volt_ampl
        cpx.set_voltage(cpx_target_voltage)

    # Define measurement file name
    name = "/{}_{}s_ME_{}".format(datetime.now().strftime("%Hh%Mm%Ss"),
                                               loop_time,
                                               sample_identification)
    file_name = new_datefolder("../data") + name
    # Save the data
    df = pd.DataFrame(data, columns = ["current",
                                       "time",
                                       "osensa_temp",
                                       "cpx_target_voltage",
                                       "cpx_volt",
                                       "cpx_curr"])
    df = df[["time",
             "current",
             "osensa_temp",
             "cpx_target_voltage",
             "cpx_volt",
             "cpx_curr"]]
    #df = df.rolling(window = 5, min_periods = 5, axis = 0).mean()
    #df.to_csv('test.csv', header=False, index=False)
    df.to_excel('{}.xlsx'.format(file_name))


    # Print statistics
    print("######################################################################")
    reading_period(df, "time")
    print("Measured current mean: {}    std: {}".format(df.current.mean(), df.current.std()))
    print("######################################################################")
    print("File name: " + file_name)

    cpx.set_voltage(0)
    cpx.set_output(0)
    del k


if __name__ == "__main__":
    main()
