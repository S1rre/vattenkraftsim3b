temp = '''
    # %% REAL DEAL
    #Signal
    signal   = GenerateFrequency(60*60, 50, 500, 0.02)
    CUTOFF   = 2 # Hz
    ORDER    = 4 # 
    lowpass  = signal.filter(CUTOFF, ORDER, 'low')
    highpass = signal.filter(CUTOFF, ORDER, 'high')
    # Powerplant
    POWERPLANTEFFECT = 100e6
    # %%
    # Simulate the generator

    #p, i, setpoint, timestep, error_deadzone, maxi, mini
    generatorController = PIController(0.4, 0.04, 50, signal.dt, 0.01, -1, 1)

    generatorSignal = np.empty_like(lowpass)
    for i, f in enumerate(lowpass):
    generatorSignal[i] = generatorController.update(f)

    # %%
    #Simulate the Battery part
    # charge, maxCharge, maxPowerCharge, maxPowerDischarge
    battery = Battery(5e5, 1e6, 1e6, 1e6)

    #p, i, setpoint, timestep, error_deadzone, maxi, mini
    batteryController = PIController(1e9, 1e5, 0, signal.dt, 0, -5e5, 5e5)

    batterySignal = np.empty_like(highpass)
    for i, f in enumerate(highpass):
    batterySignal[i] = batteryController.update(f)

    batteryPower = np.empty_like(highpass)
    batteryCharge = np.empty_like(highpass)
    for i, s in enumerate(batterySignal):
    batteryPower[i] = battery.update(s, signal.dt)
    batteryCharge[i] = battery.charge / battery.maxCharge * 100 # Show in percentage



    # %%
    mask = signal.time <= 3
    plt.plot(signal.time[mask], batteryPower[mask])
    plt.show()
    plt.plot(signal.time[mask], batteryCharge[mask])
    plt.show()
    plt.plot(signal.time[mask], generatorSignal[mask])
    # plt.plot(signal.time, )
    plt.title("Title HERE")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.show()
    # %%
'''