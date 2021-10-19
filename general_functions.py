import os
import numpy as np
import pandas as pd
from datetime import datetime
import time

def new_datefolder(path):
	# Create data folder with date as name IF it does not exist
	date = datetime.now().strftime('%Y%m%d')
	directory = os.getcwd()+"/{}/{}".format(path, date)
	if not os.path.exists(directory):
	    os.makedirs(directory)
	return directory
