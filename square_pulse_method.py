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

from general_functions import new_datefolder

from keithley6517_commands import KEITHLEY6517
from coldplate_commands import COLDPLATE


def main():

    # Set parameters
    # *********************************************************************************
    sample_identification = "poled_test"
    setup_time = 30 # Time allowed to the Coldplate to reach thermal the temperature offset.
    loop_time = 250  # Time that current vs temperature will be measured.
    current_range = 200E-12 # Upper current range limit.
    nplcycles = 1 # Integration period based on power line frequency (0.01-10)
    # Temperature function
    tmax = 80
    tmin = 60
    # *********************************************************************************


    # Initiate communication with the devices
    cp = COLDPLATE("COM5")
    k = KEITHLEY6517("ASRL3::INSTR", baud_rate = 19200, sleep = 0.05)

    # Functions
    def setup_keithley(current_range, nplcycles):
        # Reset device to defaults
        k.reset()
        k.clear_reg()

        # Select sensing function
        k.sense_function("'current'")

        # Zero correct
        k.current_range(20E-12)
        k.system_zcorrect("ON")

        # Select measurement range of interest
        k.current_range(current_range)
        k.system_zcheck("OFF")

        # Integration time
        k.current_nplcycles(nplcycles)
        k.system_pwrlinesync("OFF")

        # Timestamp
        k.system_tstamp_type("relative")
        k.system_tstamp_relative_reset()
        k.system_tstamp_format("absolute")

        # Median filter
        k.current_median_state("ON")
        k.current_median_rank(1)

        # Average filter
        k.current_average_state("OFF")
        k.current_average_type("scalar")
        k.current_average_tcontrol("repeat")
        k.current_average_count(10)

        # External temperature
        k.system_tscontrol("ON")

        # Data format
        k.format_elements(elements = "tstamp, reading, vsource, etemperature")
    def counter(seconds, message, delay = 1):
        start_time = time.time()
        while time.time() - start_time <= seconds:
            tdelta = time.time() - start_time
            time_left = round(seconds-tdelta, 1)
            print("Time left: {}, {}".format(time_left, message))
            time.sleep(delay)
    def reading_period(df, column_name):
        timedeltas = [df[column_name][i-1] - df[column_name][i] for i in range(1, len(df[column_name]))]
        sampling_rate = abs(sum(timedeltas))/len(timedeltas)
        print("Sampling rate was: {} ms".format(round(sampling_rate*1000, 3)))


    # Setup
    print("Bringing thermocycler to the starting temperature...")
    cp.set_tempTarget(tmin)
    cp.set_tempOn()
    print("Setting up the electrometer...")
    setup_keithley(current_range = current_range, nplcycles = 1)
    print("Wait until starting temperature is reached...")
    while k.read_latest()[1] < setup_time:
        print(k.read_latest()[1:3])
        time.sleep(1)
    cp.set_tempLimiterMax(99)
    cp.set_tempLimiterMin(-10)
    k.system_tstamp_relative_reset()
    print("Finished setup, ready to start measurement.")

    # Set variables
    start_time = time.time()
    data = []
    new_target_temp = tmin

    cp.set_tempTarget(99)
    # Loop
    while time.time() - start_time <= loop_time:
        tdelta = time.time() - start_time
        # Set new target temperature
        if k.read_latest()[2] > tmax:
            new_target_temp = -10
            cp.set_tempTarget(-10)
        if k.read_latest()[2] < tmin:
            new_target_temp = -99
            cp.set_tempTarget(-99)
        # Measure and save
        reading = k.read_latest()
        reading.insert(3, round(new_target_temp,1))
        reading.insert(3, round(cp.get_tempActual(),1))
        data.append(reading)
        print(reading)

    # Define measurement file name
    name = "/SQUARE__{}_{}_{}s_TEMP_{}min{}max".format(datetime.now().strftime("%Hh%Mm%Ss"),
                                               sample_identification,
                                               loop_time,
                                               tmin,
                                               tmax)
    file_name = new_datefolder("data") + name
    print("File name: " + file_name)

    # Save the data
    df = pd.DataFrame(data, columns = ["current",
                                       "time",
                                       "ext_temp",
                                       "int_temp",
                                       "new_target_temp",
                                       "vsource"])
    df = df[["time", "current", "ext_temp", "int_temp", "new_target_temp", "vsource"]]
    #df.to_csv('test.csv', header=False, index=False)
    df.to_excel('{}.xlsx'.format(file_name))

    # Print statistics
    reading_period(df, "time")


    del cp
    del k

if __name__ == "__main__":
    main()
