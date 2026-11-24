# %%
from kraftverkssimulering import GenerateFrequency, Simulation
import numpy as np

# %%
n=60*10*2000  ##Mste vara time (s)*samples/s
dailyPrice = 22.3
aFRRPrice = 27
FCRPrice = 22
tempSignal = GenerateFrequency(60 * 10, 50, 2000, 0.02)
signal = {
    "frequencies": tempSignal.frequency_signal,
    "time": tempSignal.time,
    "prices": [np.full(n,dailyPrice), np.full(n,aFRRPrice), np.full(n,FCRPrice)],  # daily, aFRR, FCR
}

# %%
# Format: (p, i, setpoint, error_deadzone, mini, maxi)
batteryController = (
    25e6,
    0.0,
    0.0,
    0.005,
    -5e6,
    5e6,
)

guideVaneController = (
    2,
    0.2,
    50.0,
    0.005,
    0.5,
    0.8,
)

# chargeWh, maxChargeWh, maxPowerChargeW, maxPowerDischargeW
battery = (2.5e6, 5e6, 5e6, 5e6)

# angle, maxAngleChange (rad/s or deg/s per second), minAngle, maxAngle
guideVane = (0.65, 0.02, 0.5, 0.8)

# cutoff frequency (Hz), filter order
for i in range(1,31):
    Ts=i
    frequencyCutoff = 1 / Ts
    lowpass = (frequencyCutoff, 2)
    highpass = (frequencyCutoff, 2)

    maxPower = 100e6
    PK = 24
    k_direct = 6

    # %%
    mySim = Simulation(
        signal,
        battery,
        guideVane,
        guideVaneController,
        batteryController,
        lowpass,
        highpass,
        maxPower,
        PK,
        k_direct,
    )

    mySim.run()
    mySim.calculateRevenue()

    # %%
    # mask = (0, 1/6)
    # mySim.plot.frequency(mask=mask)
    # mySim.plot.battery(mask=mask)
    # mySim.plot.guideVane(mask=mask)
    # mySim.plot.generatorPower(mask=mask)
    # mySim.plot.generatorPower(mask=mask, overlay_freq=True)

    print("Ts=", Ts, " Cost of guide vane wear: ",np.round(mySim.guideVane.guideWear,0), " SEK     Income:", f"{np.round(mySim.revenue['total'] * 11.15,0):,.2f} kr".replace(",", " ") )