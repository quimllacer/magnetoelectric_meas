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
from simple_pid import PID
import matplotlib.pyplot as plt

from general_functions import new_datefolder
from data_analysis import analyze
from keithley6517_commands import KEITHLEY6517
from coldplate_commands import COLDPLATE
from cpx400sp import CPX400SP


def main():

    # Set parameters
    # *********************************************************************************
    sample_identification = "test"
    setup_time = 3*60 # Time allowed to the Coldplate to reach thermal the temperature offset.
    loop_time = 60*10  # Time that current vs temperature will be measured.
    # Temperature function
    temp_ampl = 1
    temp_freq = 0.01
    temp_slope = 0.002
    temp_offset = 80
    # Keithley
    current_range = 20E-9 # Upper current range limit.
    nplcycles = 1 # Integration period based on power line frequency (0.01-10)
    average_window = 0 # Average filter window
    # Peltier cell
    peltier_status = "active"
    pelt_limit_voltage = 5
    pelt_limit_current = 4
    P, I, D = (0.6, 0.03, 0.05) #Good PID values are 0.6, 0.03, 0.05
    # *********************************************************************************


    # Initiate communication with the devices
    cp = COLDPLATE("/dev/ttyUSB0")
    k = KEITHLEY6517("ASRL/dev/ttyUSB1::INSTR", baud_rate = 19200, sleep = 0.05)
    cpx = CPX400SP('192.168.1.131', 9221)

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
        k.format_elements(elements = "tstamp, reading, vsource, etemperature")
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
    def v_function(tdelta, function, frequency, amplitude, slope, offset):
        if function  == "sine":
            applied_funct_voltage = sine(tdelta, frequency, amplitude,  slope, offset)
        elif function  == "square":
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

    # Setup peltier element
    print("Setting up peltier element...")
    pid = PID(P, I, D, setpoint=temp_offset, sample_time = 0.1)
    if peltier_status == "active":
        cpx.set_output(1)
        cpx.set_current(pelt_limit_current)
        cpx.set_voltage(0)
        temp_margin = 5
    else:
        cpx.set_output(0)
        temp_margin = 0
        cpx.set_current(0)
    new_target_temp = temp_offset

    # Setup
    print("Bringing thermocycler to the starting temperature...")
    cp.set_tempTarget(temp_offset-temp_margin)
    cp.set_tempOn()
    print("Setting up the electrometer...")
    setup_keithley(current_range = current_range, nplcycles = 1, average_window = average_window)
    print("Wait until starting temperature is reached...")
    past_time = 0
    while past_time < setup_time:
        reading = k.read_latest()[1:3]
        past_time = reading[0]
        ext_temp = reading[1]
        if past_time > setup_time/2:
            pelt_voltage = pid(ext_temp)
            if pelt_voltage > pelt_limit_voltage:
                pelt_voltage = pelt_limit_voltage
            cpx.set_voltage(pelt_voltage)
        print(reading)

    cp.set_tempLimiterMax(99)
    cp.set_tempLimiterMin(-10)
    k.system_tstamp_relative_reset()
    print("Finished setup, ready to start measurement.")

    # Set variables
    start_time = time.time()
    subset = []
    data = []

    # tdelta = k.read_latest()[1]
    pelt_voltage = 0

    # Loop
    while time.time() - start_time <= loop_time:
        # Measure and save
        reading = k.read_latest()
        tdelta = reading[1]
        reading.insert(3, float(cpx.get_current()[:-2]))
        reading.insert(3, float(cpx.get_voltage()[:-2]))
        reading.insert(3, round(pelt_voltage, 3))
        reading.insert(3, round(new_target_temp, 3))
        reading.insert(3, round(cp.get_tempActual(), 3))
        data.append(reading)
        print(reading)



        # Set new target temperature
        new_target_temp = sine(tdelta,
                               frequency = temp_freq,
                               amplitude = temp_ampl,
                               slope = temp_slope,
                               offset = temp_offset)
        pid.setpoint = new_target_temp
        pelt_voltage = pid(reading[2])
        # To avoid damaging the peltier element
        if pelt_voltage > pelt_limit_voltage:
            pelt_voltage = pelt_limit_voltage
        cpx.set_voltage(pelt_voltage)
        if peltier_status == "active":
            cp_temp_freq = 0
            cp_temp_ampl = 0
        else:
            cp_temp_freq = temp_freq
            cp_temp_ampl = temp_ampl

        cp.set_tempTarget(sine(tdelta,
                               frequency = cp_temp_freq,
                               amplitude = cp_temp_ampl,
                               slope = temp_slope,
                               offset = temp_offset-temp_margin))

    # Define measurement file name
    name = "/{}_{}s_{}".format(datetime.now().strftime("%Hh%Mm%Ss"),
                                               loop_time,
                                               sample_identification)
    file_name = new_datefolder("../data") + name
    # Save the data
    df = pd.DataFrame(data, columns = ["current",
                                       "time",
                                       "ext_temp",
                                       "int_temp",
                                       "new_target_temp",
                                       "pid_out_volt",
                                       "pelt_volt",
                                       "pelt_curr",
                                       "vsource"])
    df = df[["time",
             "current",
             "int_temp",
             "ext_temp",
             "new_target_temp",
             "pid_out_volt",
             "pelt_volt",
             "pelt_curr",
             "vsource"]]
    #df = df.rolling(window = 5, min_periods = 5, axis = 0).mean()
    #df.to_csv('test.csv', header=False, index=False)
    df.to_excel('{}.xlsx'.format(file_name))
    analyzed_data = analyze(df, points_p_period = 10, freq = 0.01, window = 11)
    analyzed_data.to_excel('{}.xlsx'.format(file_name + "ANALYZED"))


    # Print statistics
    print("######################################################################")
    reading_period(df, "time")
    print("Measured current mean: {}    std: {}".format(df.current.mean(), df.current.std()))
    print("######################################################################")
    print("File name: " + file_name)

    cpx.set_voltage(0)
    cpx.set_output(0)
    del cp
    del k


if __name__ == "__main__":
    main()
