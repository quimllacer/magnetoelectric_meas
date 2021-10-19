from osensapy import osensapy
import time
from datetime import datetime
import numpy as np
import pandas as pd
import xlsxwriter
import sys
import os

sys.path.append(".")
from cpx400sp import CPX400SP

def main():
	#Set variables
	sample_ID = "iotd-02122020"
	capacitor  = 22
	voltage = 22.3
	burst_period = 1800*2
	read_period = 10
	acquisition_time = 1800*2
	init_temp = 26 


	#Set parameters    
	cpx = CPX400SP('192.168.1.131', 9221)
	transmitter = osensapy.Transmitter("COM3", 247)
	print(cpx.get_identification())
	current = 20

	#Adjust initial temperature to 26 degrees.
	temp = round(transmitter.read_channel_temp("A"), 3)
	if temp <= init_temp + 0.01:
		temp = round(transmitter.read_channel_temp("A"), 3)
		cpx.set_current(current)
		cpx.set_voltage(voltage)
		cpx.set_output(1)
	while temp <= init_temp + 0.01:
		temp = round(transmitter.read_channel_temp("A"), 3)
		print("wait to heat up, temp: {}".format(temp))
	if temp >= init_temp:
		temp = round(transmitter.read_channel_temp("A"), 3)
		cpx.set_voltage(0)
		cpx.set_output(0)
		cpx.set_output(0)
	while temp >= init_temp:
		temp = round(transmitter.read_channel_temp("A"), 3)
		print("wait to cool down, temp: {}".format(temp))


	cpx.set_current(current)
	cpx.set_output(1)
	
	#Loop
	total_elapsed_time = 0
	temp_zero_time = 0
	volt_zero_time = 0
	start_time = time.time()
	temp_hist = []
	burst_itercount = 0

	while total_elapsed_time <= acquisition_time:
		total_elapsed_time = time.time() - start_time
		temp_elapsed_time = time.time() - temp_zero_time
		volt_elapsed_time = time.time() - volt_zero_time

		if temp_elapsed_time >= read_period:
			temp = round(transmitter.read_channel_temp("A"), 3)
			data = [round(total_elapsed_time, 3), temp, float(cpx.get_voltage()[:-2]), float(cpx.get_current()[:-2])]
			temp_hist.append(data)
			print(data)
			temp_zero_time = time.time()

		if volt_elapsed_time >= burst_period/2:
			if (burst_itercount % 2):
				cpx.set_voltage(0)
				volt_zero_time = time.time()
				burst_itercount = burst_itercount + 1
			else:
				cpx.set_voltage(voltage)
				volt_zero_time = time.time()
				burst_itercount = burst_itercount + 1


	cpx.set_voltage(0)
	cpx.set_output(0)
	transmitter.close()

	foldername = "../data/" + str(datetime.now().strftime("%Y%m%d"))
	os.makedirs(foldername, exist_ok = True)
	filepath = "{}/{}_{}_C{}_burst.xlsx".format(foldername, datetime.now().strftime("%Hh%Mmin"), sample_ID, capacitor)
	#np.savetxt(filepath, temp_hist, delimiter = ",")
	df = pd.DataFrame(temp_hist)
	columns = ["time", "temp", "voltage", "current"]
	df.to_excel(filepath, index = False, header = False, startcol = 1, engine = "xlsxwriter")


	del cpx

if __name__ == "__main__":
	main()