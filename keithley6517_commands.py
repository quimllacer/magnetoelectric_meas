import os
import numpy as np
import pandas as pd
import pyvisa as visa
from datetime import datetime
import time


class KEITHLEY6517:
    def __init__(self, resource, baud_rate, sleep):
        try:
            self.sleep = sleep # Delay allowed for communication
            rm = visa.ResourceManager()
            print("Resource list: {}".format(rm.list_resources()))
            self.keithley6517 = rm.open_resource(resource, read_termination='\r')
            time.sleep(self.sleep) # Wait
            self.keithley6517.baud_rate = baud_rate # Set baud rate according to equipment settings 
            time.sleep(self.sleep) # Wait
            print('Communication with keithley6517 established at resource {}'.format(resource))
            print(self.keithley6517.query('*idn?'))  # Ask for identification
            time.sleep(self.sleep) # Wait

        except:
            print('Failed to communicate with keithley6517 at resource {}').format(resource)

    def __del__(self):
        self.keithley6517.write("output1 OFF") #Disable V-source output, for safety.
        time.sleep(self.sleep) # Wait
        self.keithley6517.write('*RST') # Reset device
        time.sleep(self.sleep) # Wait
        self.keithley6517.write('*CLS') # Reset device
        del self.keithley6517
        print("Safely stopped communication: vsource OFF, device RESET, registers CLEAR.")

    # Status
    def status_queue_clear(self):
        self.keithley6517.write('status:queue:clear') # Clears all messages from Error Queue
        time.sleep(self.sleep) # Wait

    # Calibartion
    def system_zcheck(self, state):
        self.keithley6517.write('system:zcheck {}'.format(state)) # Set ON or OFF Zero Check
        time.sleep(self.sleep) # Wait
    def system_zcorrect(self, state):
        self.keithley6517.write('system:zcorrect {}'.format(state)) # Set ON or OFF zero correct
        time.sleep(self.sleep) # Wait

    # Measurement type
    def sense_function(self, function):
        self.keithley6517.write('sense:function {}'.format(function)) # Select measurement function e.g. "VOLT", "CURR"
        time.sleep(self.sleep) # Wait
    def current_range(self, crange):
        self.keithley6517.write('current:range {}'.format(crange)) #Select current range upper limit
        time.sleep(self.sleep) # Wait

    # Voltage source
    def vsource_limit_state(self, state):
        self.keithley6517.write('source:voltage:limit:state {}'.format(state)) # Set ON or OFF V-source voltatge limit, for safety.
        time.sleep(self.sleep) # Wait
    def vsource_limit(self, limit):
        self.keithley6517.write('source:voltage:limit {}'.format(limit)) # Specify V-source voltage limit, for safety.
        time.sleep(self.sleep) # Wait
    def vsource_output_state(self, state):
        self.keithley6517.write('output1 {}'.format(state)) #Set ON or OFF V-source output
        time.sleep(self.sleep) # Wait
    def vsource(self, voltage):
        self.keithley6517.write('source:voltage {}'.format(voltage)) # Set the amplitude of the V-source
        time.sleep(self.sleep) # Wait
    def vsource_mconnect(self, state):
        self.keithley6517.write('source:voltage:mconnect {}'.format(state)) # Connect V-source LO to Ammeter LO to allow current measurment
                                                                    # while applying V-source.
        time.sleep(self.sleep) # Wait
    # Signal integration
    def current_nplcycles(self, nplcycles):
        self.keithley6517.write('current:nplcycles {}'.format(nplcycles)) #Integration period based on power line frequency (0.01-10)
        time.sleep(self.sleep) # Wait
    def system_pwrlinesync(self, state):
        self.keithley6517.write('system:lsync:state {}'.format(state)) # Enables power line synchronisation.
        time.sleep(self.sleep) # Wait

    # Average filter
    def current_average_state(self, state):
        self.keithley6517.write('current:average:state {}'.format(state)) #Switch ON or OFF the filter
        time.sleep(self.sleep) # Wait
    def current_average_type(self, typ):
        self.keithley6517.write('current:average:type {}'.format(typ)) # Set average filter type: none, scalar or advanced
        time.sleep(self.sleep) # Wait
    def current_average_tcontrol(self, tcontrol):
        self.keithley6517.write('current:average:tcontrol {}'.format(tcontrol)) # Set average filter type: moving or repeat
        time.sleep(self.sleep) # Wait
    def current_average_count(self, count):
        self.keithley6517.write('current:average:count {}'.format(count)) # Set average filter window: 1-100
        time.sleep(self.sleep) # Wait

    # Median filter
    def current_median_state(self, state):
        self.keithley6517.write('current:median:state {}'.format(state)) #Switch ON or OFF the filter
        time.sleep(self.sleep) # Wait
    def current_median_rank(self, rank):
        self.keithley6517.write('current:median:rank {}'.format(rank)) # Set average filter type: none, scalar or advanced
        time.sleep(self.sleep) # Wait

    # Resolution
    def current_digits(self, digits):
        self.keithley6517.write('current:digits {}'.format(digits)) # Specify n of digits shown from 4 to 7
        time.sleep(self.sleep) # Wait

    # Configure timestamp
    def system_tstamp_type(self, typ = "relative"):
        self.keithley6517.write('system:tstamp:type {}'.format(typ))
        time.sleep(self.sleep) # Wait
    def system_tstamp_relative_reset(self):
        self.keithley6517.write('system:tstamp:relative:reset') # Reset timestamp
        time.sleep(self.sleep) # Wait
    def system_tstamp_format(self, typ = "absolute"):
        self.keithley6517.write('data:tstamp:format {}'.format(typ)) # Relative timestamp set to absolute
        time.sleep(self.sleep) # Wait
    def buffer_format_tstamp(self, typ = "absolute"): #READing,TSTamp, ETEMperature and VSOurce
        self.keithley6517.write('trace:tstamp:format {}'.format(typ))
        time.sleep(self.sleep) # Wait

    # External temperature reading via K-type thermocouple connected to the back of the device
    def system_tscontrol(self, state):
        self.keithley6517.write('system:tscontrol {}'.format(state))

    # Data format
    def format_elements(self, elements = "tstamp, reading, vsource"): #READing,TSTamp, ETEMperature and VSOurce
        self.keithley6517.write('format:elements {}'.format(elements))
        time.sleep(self.sleep) # Wait
    def buffer_format_elements(self, elements = "tstamp, vsource"): #READing,TSTamp, ETEMperature and VSOurce
        self.keithley6517.write('trace:elements {}'.format(elements))
        time.sleep(self.sleep) # Wait

    # Buffer set-up
    def trigger_count(self, count):
        self.keithley6517.write('trigger:count {}'.format(count)) # Set measure count 1-99999
        time.sleep(self.sleep) # Wait
    def trigger_delay(self, delay):
        self.keithley6517.write('trigger:delay {}'.format(delay)) # Set delay between measurements
        time.sleep(self.sleep) # Wait
    def trace_clear(self):
        self.keithley6517.write('trace:clear') # Clear readings from buffer
        time.sleep(self.sleep) # Wait
    def trace_points(self, points):
        self.keithley6517.write('trace:points {}'.format(points)) # Specify size of buffer (maximum is 8566)
        time.sleep(self.sleep) # Wait
    def trace_feed_control(self, control = "next"):
        self.keithley6517.write('trace:feed:control {}'.format(control)) # Select buffer control mode
        time.sleep(self.sleep) # Wait

    # Reset
    def reset(self):
        self.keithley6517.write('*RST') # Reset device
    def clear_reg(self):
        self.keithley6517.write('*CLS') # Clear registers

    #Start measurement
    def initate_measurement(self):
        self.keithley6517.write('initiate; *WAI') # Initiate reading, save into buffer and wait until finished
        time.sleep(self.sleep) # Wait

    # Query data
    def status_queue_next(self, header):
        reading = self.keithley6517.query('status:queue:next?') # Read the most recent error messsage.
        time.sleep(self.sleep) # Wait
        print("{} error in:    {}".format(reading.replace("\n", ""), header))
    def read_latest(self):
        reading = self.keithley6517.query('read?') # Initialize and return latest reading
        return list(np.fromstring(reading, sep=','))
    def get_latest(self):
        reading = self.keithley6517.query('fetch?') # Initialize and return latest reading
        return list(np.fromstring(reading, sep=','))
    def measure(self):
        reading = self.keithley6517.query('measure?') # Initialize and return latest reading
        return list(np.fromstring(reading, sep=','))
    def read_buffer(self, n_columns):
        reading = self.keithley6517.query('trace:data?') # Read all readings stored in the buffer
        time.sleep(self.sleep) # Wait
        # return reading
        return np.fromstring(reading, sep=',').reshape(-1, n_columns)
    def buffer_status(self):
        buffer_status = self.keithley6517.query('trace:free?') # Return buffer memory status
        return np.fromstring(buffer_status, sep=',')
    def status_measurement_event(self):
        print(self.keithley6517.query('status:measurement:event?'))
        time.sleep(self.sleep) # Wait
    def pyvisa_timeout(self, delay = None):
        self.keithley6517.timeout = delay # Remove pyVISA timeout because data reading and transfer is slow (especially the buffer).
        time.sleep(self.sleep) # Wait

