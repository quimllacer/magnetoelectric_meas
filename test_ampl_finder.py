import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import hilbert
from scipy.signal import correlate, correlation_lags, detrend

file = r"/Users/joaquinllacerwintle/OneDrive - ETH Zurich/data/20210909/13h30m27s_coronapoled_PVDF_1800s_TEMP_1a0.01f0.002s80o.xlsx"
df = pd.read_excel(file, engine = "openpyxl")[["time", "current", "ext_temp"]][0:2000] # Skip intital rows

t = np.array(df["time"])
A = df["ext_temp"]
B = df["current"]

A_h = detrend(hilbert(A))

plt.plot(t, detrend(A))
plt.plot(t, A_h)
plt.show()


