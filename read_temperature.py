from osensapy import osensapy
import numpy as np

print("ports: ", osensapy.serial_get_portlist())

transmitter = osensapy.Transmitter("COM3", 247)
print("serial no: ", transmitter.read_serial_number())
print("device id: ",transmitter.read_device_id())

while True:
	temp = round(transmitter.read_channel_temp("A"), 3)
	print("Temperature is: ", temp)

transmitter.close()