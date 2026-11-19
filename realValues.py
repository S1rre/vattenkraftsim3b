#%%
# import libraries and our code
from kraftverkssimulering import Simulation, GenerateFrequency
import numpy as np
import matplotlib.pyplot as plt

# %%
# Load real values

data = np.load("./DataKod/grid_data.npz")

# aFRR = data["aFRR"] this also exist not implemented yet.
f = data["frequencies"]
time = np.arange(len(f)) * data["time"][1] / 1000

# Mask of valid (non-zero) values
valid = f != 0
n = np.diff(time)
print(max(n), min(n))
# Indices of all elements
idx = np.arange(len(f))

# Replace zeros with linear interpolation between valid neighbors
f_clean = np.interp(idx, idx[valid], f[valid])

a = np.asarray(data["dailyPrice"], dtype=float)
b = np.asarray(data["aFRR"], dtype=float)
c = np.asarray(data["FCR"], dtype=float)

signal = {
'frequencies' : f_clean,
'time' : time,
'prices' : (a,b,c)
}


# Format: (p, i, setpoint, error_deadzone, mini, maxi)
# Velocity PI controller 

# Battery handles the HIGH-PASS
batteryController = (
    25e6,   # p: 25 MW/Hz
    0.0,    # i: 
    0.0,    # setpoint: 
    0.005,  # error_deadzone: 
    -5e6,   # mini:
    5e6,    # maxi: 
)

# Generator handles the LOW-PASS
guideVaneController = (
    0.03,       # p: 
    0.00005,    # i: 
    50.0,       # setpoint
    0.005,      # error_deadzone: 
    -0.02,      # mini: 
    0.02,       # maxi:
)

# chargeInWatt (or Joules/Wh), maxCharge, maxPowerCharge, maxPowerDischarge
battery = (
    2.5e6,  # Stored charge in W
    5e6,    # Max charge in W
    5e6,    # Max Power Charge in W
    5e6     # Max Power Discharge
)

# angle, maxAngleChange, minAngle, maxAngle
guideVane = (0.65, 0.02, 0.5, 0.8)

# Cutoff frequency (Hz), filter order
# Note: Must be less than half your sampling rate (Nyquist limit)!

cutoffFrequency = 1/200 # 
filterOrder = 2 # 2 should be okay here

# Uses the same because: The cutoff freq should be the same because we dont have any penalty for unregulated
lowpass     = (cutoffFrequency, filterOrder)
highpass    = (cutoffFrequency, filterOrder)


maxPower = 100e6 # Max power of power plant
PK = 0.0001 # some constant for the wear? arbitrary value set right now
K_direct = 300 # constant for the wear? arbitrary value set right now

# %%
mySim = Simulation(
    signal, battery, guideVane,
    guideVaneController, batteryController, 
    lowpass, highpass,
    maxPower, PK, K_direct)

mySim.run()


# %%
m = (0, 24*1) # in hours
mySim.plot.frequency(m);
mySim.plot.battery(m);
mySim.plot.guideVane(m);
mySim.plot.generatorPower(m, overlay_freq=True);

# %%
# print(sum(np.abs(mySim.guideVaneWear)))
# %%

# %%
print(mySim.guideVane.guideWear)

# %%
s = mySim.calculateRevenue(fcr_share=0.5)
# %%

print(f"{s["total"] * 11.15:,.2f} kr".replace(",", " "))
# %%
