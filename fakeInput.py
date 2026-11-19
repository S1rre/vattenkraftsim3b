#%%
# import libraries and our code
from kraftverkssimulering import Simulation, GenerateFrequency
import numpy as np


# %%
# Generate our constants
tempSignal = GenerateFrequency(60*60, 50, 500, 0.02)
signal = {
'frequencies' : tempSignal.frequency_signal,
'time' : tempSignal.time,
'prices' : [] 
}

#%%
# Format: (p, i, setpoint, error_deadzone, mini, maxi)

# Battery handles the HIGH-PASS (fast) frequency fluctuations (±5 MW)
# High P to react instantly to spikes; I = 0 (or very small) because the highpass filter already removes steady-state offset
batteryController = (
    25e6,  # p: 25 MW/Hz -> reaches full 5 MW output at a 0.2 Hz frequency deviation (5e6 / 0.2)
    0.0,  # i: Keep at 0 when fed by a highpass filter (or small, e.g., 1e5, if fed raw error)
    0.0,  # setpoint: 0.0 if input is already highpass-filtered deviation; 50.0 if input is raw Hz
    0.005,  # error_deadzone: ±0.005 Hz deadband to prevent constant micro-cycling
    -5e6,  # mini: -5 MW (matches maxPowerCharge)
    5e6,  # maxi: +5 MW (matches maxPowerDischarge)
)

# Generator handles the LOW-PASS (slow) frequency trends (e.g., 0 to 10 MW)
# Lower P, higher I to smoothly restore grid frequency over tens of seconds/minutes
guideVaneController = (
    1,  # p: 
    0.2,  # i: 
    50.0,  # setpoint: 50.0 Hz nominal grid frequency
    0.00,  # error_deadzone: 
    0,  # mini:
    1,  # maxi:
)

# chargeInWatt (or Joules/Wh), maxCharge, maxPowerCharge, maxPowerDischarge
# Note: Check if chargeInWatt is > maxCharge in your code (10e6 vs 5e6)!
battery = (2.5e6, 5e6, 5e6, 5e6)
# angle, maxAngleChange, minAngle, maxAngle
guideVane = (0.65, 0.02, 0.5, 0.8)
# cutoff frequency (Hz), filter order
# Note: Must be less than half your sampling rate (Nyquist limit)!
lowpass = (0.05, 2)  # Passes slow changes (> 20 second period) to the generator
highpass = (0.05, 2)  # Passes fast changes (< 20 second period) to the battery

maxPower = 100e6 # Max power of power plant
PK = 1 # some constant for the wear

# %%
mySim = Simulation(
    signal, battery, guideVane,
    guideVaneController, batteryController, 
    lowpass, highpass,
    maxPower, PK)

mySim.run()


# %%

mySim.plot.frequency(mask=(100,300))
mySim.plot.batterySimulation(mask=(100,300))
mySim.plot.guideVaneSimulation(mask=(100,300))
mySim.plot.powerSimulation(mask=(100,300))

# %%
