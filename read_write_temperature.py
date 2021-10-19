from osensapy import osensapy
import time
from datetime import datetime
import numpy as np
import pandas as pd
import xlsxwriter
import sys
import os

print("ports: ", osensapy.serial_get_portlist())

transmitter = osensapy.Transmitter("COM3", 247)
print("serial no: ", transmitter.read_serial_number())
print("device id: ",transmitter.read_device_id())

#Set variables
experiment_ID = "Rhb_pyrocatalysis"
read_period = 0.5
save_period = 5


foldername = "../data/" + str(datetime.now().strftime("%Y%m%d"))
os.makedirs(foldername, exist_ok = True)
filepath = "{}/{}_{}_tempread.xlsx".format(foldername, datetime.now().strftime("%Hh%Mmin"), experiment_ID)

total_elapsed_time = 0
temp_zero_time_read = 0
temp_zero_time_save = 0
start_time = time.time()
temp_hist = []
n = 0

while True:

	temp = round(transmitter.read_channel_temp("A"), 3)
	print("Temperature is: ", temp)

	total_elapsed_time = time.time() - start_time
	temp_elapsed_time_read = time.time() - temp_zero_time_read
	temp_elapsed_time_save = time.time() - temp_zero_time_save

	if temp_elapsed_time_read >= read_period:
		temp = round(transmitter.read_channel_temp("A"), 3)
		data = [round(total_elapsed_time, 3), temp]
		temp_hist.append(data)
		temp_zero_time_read = time.time()

	if temp_elapsed_time_save >= save_period:

		df = pd.DataFrame(temp_hist)
		df.to_excel(filepath, index = False, header = False, startcol = 1, engine = "xlsxwriter")
		temp_zero_time_save = time.time()

transmitter.close()