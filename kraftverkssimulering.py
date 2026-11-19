# %%
import control as ct
import matplotlib.pyplot as plt
import numpy as np
import scipy
from plot import Plot

# %%
def guideVaneToPower(guideOpening, maxPower):
   #Non normalized -195.158x^{2}+430.96564x-82.45085
   #Itll be normalized using the max power in dataset and to get correct scale multiplied by max power of simulated hydropowerplant. From dataset this is 154.5MW
   maxPowerInDataset=154.5
   return maxPower*(-195.158*guideOpening**2+430.96564*guideOpening-82.45085)/maxPowerInDataset


# %%

class GenerateFrequency():
    def __init__(self, simulation_time, frequency, resolution, noise_amplitude) -> None:
        self.simulation_time = simulation_time
        self.frequency = frequency
        # Ensure resolution is an integer (NumPy requires ints for array sizes)
        self.resolution = int(resolution * simulation_time)
        self.noise_amplitude = noise_amplitude
        
        # Generate signals
        self.time = np.linspace(0, self.simulation_time, self.resolution)
        self.dt = self.time[1] - self.time[0]
        # Calculate signal (avoids storing intermediate base/noise/harmonic arrays as class attributes if not needed)
        self.frequency_signal = (
            self.generate_base_frequency() + 
            self.generate_whitenoise() + 
            self.generate_harmonics()
        )

    def generate_base_frequency(self):
        # np.full is slightly faster than np.full_like since we know the exact shape
        return np.full(self.resolution, self.frequency)

    def generate_whitenoise(self):
        return np.random.normal(0, self.noise_amplitude, self.resolution)

    def generate_harmonics(self):
        # Use NumPy arrays and reshape them for broadcasting
        harmonic_frequencies = np.array([0.01, 0.1, 1, 2, 3, 4, 5]).reshape(-1, 1)
        
        # Original code reversed the amplitudes array, so we can just write it reversed here
        harmonic_amplitudes = np.array([0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02]).reshape(-1, 1)

        # Vectorized calculation:
        # Frequencies (7, 1) * Time (N) -> creates a (7, N) matrix instantly
        harmonics_matrix = harmonic_amplitudes * np.sin(2 * np.pi * harmonic_frequencies * self.time)
        
        # np.sum adds them all up at the C-level along the column axis
        return np.sum(harmonics_matrix, axis=0)

    def plot_amplitude(self, stoptime=None, time=None, amplitude=None):
        time = self.time if time is None else time
        amplitude = self.frequency_signal if amplitude is None else amplitude
        stoptime = len(time) if stoptime is None else stoptime

        mask = time <= stoptime
        plt.plot(time[mask], amplitude[mask])
        plt.title("Simulated Grid Frequency with White Noise and Harmonics")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.show()
    
    def filter(self, cutoff_freq=50, order=4, type='low'):
        fs = 1.0 / self.dt
        b, a = scipy.signal.butter(order, cutoff_freq, btype=type, fs=fs)
        filtered = scipy.signal.filtfilt(b, a, self.frequency_signal)
        return filtered
    
    def plot_spectrum(self):
        # 2. Determine sample spacing (dt) and number of samples (N)
        # This assumes self.simulation_time is a numpy array of evenly spaced time steps
        dt = 1 / self.simulation_time
        N = len(self.time)
        
        # 3. Compute the FFT
        fft_values = np.fft.fft(self.frequency_signal)
        fft_freqs = np.fft.fftfreq(N, dt)
        
        # 4. Extract only the positive frequencies
        pos_mask = fft_freqs > 0
        freqs = fft_freqs[pos_mask]
        
        # 5. Calculate amplitude (normalize by N and multiply by 2 for the single-sided spectrum)
        amplitudes = (2.0 / N) * np.abs(fft_values[pos_mask])
        
        # Optional: Calculate power (amplitude squared)
        power = amplitudes ** 2
        
        # 6. Plot the results
        plt.figure(figsize=(10, 5))
        
        # Plotting Amplitude vs Frequency (you can swap 'amplitudes' with 'power' if preferred)
        plt.plot(freqs, amplitudes, marker='o', linestyle='-', color='b')
        
        # Format the plot
        plt.title('Frequency Spectrum of Generated Signal')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude')
        
        # Limit x-axis to slightly above your max frequency (5 Hz) for a clear view
        plt.xlim(0, 1) 
        plt.grid(True)
        plt.show()
# %%
class Battery():
  #Charge in joule
  #maxPowerCharge positive in watt  | in joule*
  #maxPowerCharge should be positive
  #maxPowerDischarge should be positive
  def __init__(self, charge, maxCharge, maxPowerCharge, maxPowerDischarge):
    # handle wrong inputs.
    if charge < maxCharge:
       self.charge=charge
    else:
       self.charge = maxCharge
       
    self.maxCharge=maxCharge
    self.maxPowerCharge=-abs(maxPowerCharge)
    self.maxPowerDischarge=abs(maxPowerDischarge)
  
  def update(self, deltaPower, time):
    #if deltapower>0 battery is discharging
    #If deltapower<0 battery is charging
    if(deltaPower>self.maxPowerDischarge): ##handles power out of bounds
      deltaPower=self.maxPowerDischarge
      if(self.charge<=0): ##handles battery empty
        deltaPower=0

    elif(deltaPower<0 and deltaPower<self.maxPowerCharge): #Handles power out of bounds
      deltaPower=self.maxPowerCharge
      if(self.charge>self.maxCharge): #handles battery full
        deltaPower=0

    #Checks if the battery goes above max or below 0 and makes sure it doesnt
    if(self.charge-deltaPower*time>self.maxCharge):
      deltaPower=(self.charge-self.maxCharge)/time
    elif(self.charge-deltaPower*time<0):
      deltaPower=(self.charge-0)/time
    
    #default case
    self.charge-=deltaPower*time
    return deltaPower  ##If battery is discharging => positive if battery is charging => negative    

#%%
class GuideVane():
  #Charge in joule
  #maxPowerCharge positive in watt 
  #maxPowerCharge should be positive
  #maxPowerDischarge should be positive
    def __init__(self, angle, maxAngle, minAngle, maxAngleChange, time, PK, K_direct):
        self.angle=angle
        self.maxAngle=maxAngle
        self.minAngle=minAngle
        self.maxAngleChange=maxAngleChange
        self.time = time
        self.PK = PK
        self.K_direct=K_direct
        self.lastChange=0
        self.guideWear=0
    
    def _guideVaneWear(self, change , time):
        #formula wear=Distance[m] * constant[m^2/N] * load [N/m^2] #We see load and the constant as constant PK
        #distance=change*time
        if(change*self.lastChange>0): ##same sign so no change punishment
            self.guideWear+=abs(change*time*self.PK)
        elif(change*self.lastChange<0): ##Different sign directional change has occured
            self.guideWear+=abs(change*time*self.PK)+self.K_direct
        else:
            self.guideWear+=abs(change*time*self.PK)
        if change != 0: # needs to add this because it never changes at the first entry 0<0 is false
            self.lastChange=change


    def update(self, change, time):
        #if deltapower>0 battery is discharging
        #If deltapower<0 battery is charging

        if(change>self.maxAngleChange): #handles change out of bounds
            change=self.maxAngleChange
        elif(change<-self.maxAngleChange):
            change=-self.maxAngleChange   ##If change negative

        #Checks if guide wane change will make it go out of bounds and makes sure it doesnt
        if(self.angle+change*time>self.maxAngle):
            change=(self.maxAngle-self.angle)/time
        elif(self.angle+change*time<self.minAngle):
            change=(self.minAngle-self.angle)/time

        self._guideVaneWear(change,time)
        #default case
        self.angle+=change*time
        return change  
#%%

class PIController():
    def __init__(self, p, i, setpoint, timestep, error_deadzone, mini, maxi):
        self.p=p
        self.i=i
        self.setpoint=setpoint
        self.timestep=timestep
        self.integral=0.0
        self.error_deadzone = error_deadzone
        self.output=0
        self.maxi=maxi
        self.mini=mini
        self.prev_error = 0

    # def oldupdate(self,value):
    #     #potentially add floating deadzone by doing nothing if error<constant
    #     error=(self.setpoint-value)
    #     if(abs(error)<self.error_deadzone): #Make sure this it above where output is changed
    #        return self.output
    #     tempoutput=self.output
        
    #     #Both windup limit and makes sure that its not out of bounds
    #     tempoutput+=self.i*error*self.timestep+self.output * self.p*error
    #     if(tempoutput<=self.mini):
    #        self.output=self.mini
    #     elif(tempoutput>=self.maxi):
    #        self.output=self.maxi
    #     else:
    #        self.integral=self.i*error*self.timestep
    #        self.output=tempoutput

    #     return self.output
    
    def update(self, value):
        error = self.setpoint - value

        if abs(error) < self.error_deadzone:
            error = 0.0

        delta_p = self.p * (error - self.prev_error)
        delta_i = self.i * error * self.timestep

        self.output = max(self.mini, min(self.maxi, self.output + delta_p + delta_i))
        self.prev_error = error

        return self.output

# %%
class Simulation():
    def __init__(self, 
        signal, battery, guideVane, 
        guideVaneController, batteryController,
        lowpass, highpass,
        maxPower, PK, K_direct
        ):
        
        self.signal = signal
        self.frequencies = signal['frequencies']
        self.dailyPrice, self.aFRR, self.FCR = signal['prices']
        self.time = signal['time']
        self.dt = self.time[1] - self.time[0]
        self.maxPower = maxPower # maxpower of hydropowerplant
        self.bidPower = guideVaneToPower(0.65, self.maxPower) # HERE IS A HARDCODED CONSTANT because...
        self.PK = PK # guidevane wear constant
        self.K_direct = K_direct
        #convert watt to joule
        chargeW, maxCharge, maxPowerCharge, maxPowerDischarge = battery
        self.battery = Battery(chargeW * 3600, maxCharge * 3600, maxPowerCharge, maxPowerDischarge)

        angle, maxAngleChange, minAngle, maxAngle = guideVane
        self.guideVane = GuideVane(angle, maxAngle, minAngle, maxAngleChange, self.dt, self.PK, self.K_direct)

        self.lowpass = self.filter(*lowpass, type='low')
        self.highpass = self.filter(*highpass, type='high')

        self.guideVaneSignal  = np.zeros_like( self.lowpass  )
        self.guideVaneChange  = np.zeros_like( self.lowpass  )
        self.guideVaneAngle   = np.zeros_like( self.lowpass  )
        self.guideVanePower   = np.zeros_like( self.lowpass  )
        # self.guideVaneWear    = np.zeros_like( self.lowpass  )

        self.batterySignal    = np.zeros_like( self.highpass )
        self.batteryPower     = np.zeros_like( self.highpass )
        self.batteryCharge    = np.zeros_like( self.highpass )

        # p, i, setpoint, timestep, error_deadzone, mini, maxi

        p, i, setpoint, error_deadzone, mini, maxi = guideVaneController
        self.guideVaneController = PIController(p, i, setpoint, self.dt, error_deadzone, mini, maxi)

        p, i, setpoint, error_deadzone, mini, maxi = batteryController
        self.batteryController = PIController(p, i, setpoint, self.dt, error_deadzone, mini, maxi)
        
        # Plotter helper
        self.plot = Plot(self)

    def filter(self, cutoff_freq=50, order=4, type='low'):
        fs = 1.0 / self.dt
        b, a = scipy.signal.butter(order, cutoff_freq, btype=type, fs=fs)
        filtered = scipy.signal.filtfilt(b, a, self.frequencies)
        return filtered

    # def calculateRevenue(self):
    #     dailyHydroRevenue = self.guideVanePower * self.dailyPrice * self.dt / 3600
    #     dailyBatteryRevenue = self.guideVanePower * self.dailyPrice * self.dt / 3600
    #     FRRHydroRevenue = np.abs(self.guideVanePower - self.bidPower) * self.FRR * self.dt / 3600 / 1e6
    #     FRRBatteryRevenue = np.abs(self.batteryPower - self.bidPower) * self.FRR * self.dt / 3600 / 1e6
    #     FCRHydroRevenue =  
    #     self.revenue 


    def calculateRevenue(self, fcr_share=0.5):
        dt_hours = self.dt / 3600.0

        # Convert powers from W to MW
        hydro_MW = self.guideVanePower / 1e6
        battery_MW = self.batteryPower / 1e6
        bid_MW = self.bidPower / 1e6
        max_hydro_MW = self.maxPower / 1e6

        dailyHydroRevenue = np.sum(hydro_MW * self.dailyPrice * dt_hours)
        dailyBatteryRevenue = np.sum(battery_MW * self.dailyPrice * dt_hours)

        min_hydro_MW = max(0.0, guideVaneToPower(self.guideVane.minAngle, max_hydro_MW))
        hydro_band_MW = max(0.0, min(max_hydro_MW - bid_MW, bid_MW - min_hydro_MW))

        batt_band_MW = min(abs(self.battery.maxPowerCharge), self.battery.maxPowerDischarge) / 1e6

        afrr_hydro_MW = (1.0 - fcr_share) * hydro_band_MW

        fcr_batt_MW = batt_band_MW
        afrr_batt_MW = (1.0 - fcr_share) * batt_band_MW

        FCRHydroRevenue = np.sum(0)
        FRRHydroRevenue = np.sum(afrr_hydro_MW * self.aFRR * dt_hours)

        FCRBatteryRevenue = np.sum(fcr_batt_MW * self.FCR * dt_hours)
        FRRBatteryRevenue = np.sum(afrr_batt_MW * self.aFRR * dt_hours)

        # 4. Total Revenue breakdown
        self.revenue = {
            "daily_hydro": dailyHydroRevenue,
            "daily_battery": dailyBatteryRevenue,
            "aFRR_hydro": FRRHydroRevenue,
            "aFRR_battery": FRRBatteryRevenue,
            "FCR_hydro": FCRHydroRevenue,
            "FCR_battery": FCRBatteryRevenue,
            "total": (
                dailyHydroRevenue + dailyBatteryRevenue +
                FRRHydroRevenue + FRRBatteryRevenue +
                FCRHydroRevenue + FCRBatteryRevenue
            )
        }
        return self.revenue

    def update(self, i):
        #Update battery using PIcontroller and battery class
        batterySignal = self.batteryController.update(self.highpass[i])
        self.batterySignal[i] = batterySignal
        self.batteryPower[i] = self.battery.update(batterySignal, self.dt)
        self.batteryCharge[i] = self.battery.charge / self.battery.maxCharge * 100 # Show in percentage

        #Update generator controll
        guideVaneSignal = self.guideVaneController.update(self.lowpass[i]) # PIconroller
        self.guideVaneSignal[i] = guideVaneSignal
        self.guideVaneChange[i] = self.guideVane.update(guideVaneSignal, self.dt) # 
        self.guideVaneAngle[i] = self.guideVane.angle
        
        #convert to power and wear
        #guideVaneToPower(guideOpening, maxPower):
        self.guideVanePower[i] = guideVaneToPower(self.guideVane.angle, self.maxPower)

    def run(self):
        steps = len(self.time)
        for i in range(steps):
            self.update(i)

           
