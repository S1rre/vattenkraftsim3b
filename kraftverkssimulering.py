import control as ct
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal
from plot import Plot


def guideVaneToPower(guideOpening, maxPower):
    # Non-normalized quadratic fit scaled against dataset max power (154.5 MW)
    maxPowerInDataset = 154.5
    raw_power = (
        -195.158 * guideOpening**2
        + 430.96564 * guideOpening
        - 82.45085
    )
    return maxPower * (raw_power / maxPowerInDataset)


class GenerateFrequency:
    def __init__(self, simulation_time, frequency, resolution, noise_amplitude) -> None:
        self.simulation_time = simulation_time
        self.frequency = frequency
        self.resolution = int(resolution * simulation_time)
        self.noise_amplitude = noise_amplitude

        self.time = np.linspace(0, self.simulation_time, self.resolution)
        self.dt = self.time[1] - self.time[0]
        self.frequency_signal = (
            self.generate_base_frequency()
            + self.generate_whitenoise()
            + self.generate_harmonics()
        )

    def generate_base_frequency(self):
        return np.full(self.resolution, self.frequency)

    def generate_whitenoise(self):
        return np.random.normal(0, self.noise_amplitude, self.resolution)

    def generate_harmonics(self):
        harmonic_frequencies = np.array([0.01, 0.1, 1, 2, 3, 4, 5]).reshape(-1, 1)
        harmonic_amplitudes = np.array([0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02]).reshape(-1, 1)
        harmonics_matrix = harmonic_amplitudes * np.sin(2 * np.pi * harmonic_frequencies * self.time)
        return np.sum(harmonics_matrix, axis=0)

    def plot_amplitude(self, stoptime=None, time=None, amplitude=None):
        time = self.time if time is None else time
        amplitude = self.frequency_signal if amplitude is None else amplitude
        stoptime = time[-1] if stoptime is None else stoptime

        mask = time <= stoptime
        plt.plot(time[mask], amplitude[mask])
        plt.title("Simulated Grid Frequency with White Noise and Harmonics")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Amplitude (Hz)")
        plt.grid(True)
        plt.show()

    def filter(self, cutoff_freq=50, order=4, type="low"):
        fs = 1.0 / self.dt
        b, a = scipy.signal.butter(order, cutoff_freq, btype=type, fs=fs)
        return scipy.signal.filtfilt(b, a, self.frequency_signal)

    def plot_spectrum(self):
        N = len(self.time)
        fft_values = np.fft.fft(self.frequency_signal)
        fft_freqs = np.fft.fftfreq(N, self.dt)

        pos_mask = fft_freqs > 0
        freqs = fft_freqs[pos_mask]
        amplitudes = (2.0 / N) * np.abs(fft_values[pos_mask])

        plt.figure(figsize=(10, 5))
        plt.plot(freqs, amplitudes, marker="o", linestyle="-", color="b")
        plt.title("Frequency Spectrum of Generated Signal")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Amplitude")
        plt.xlim(0, 6)
        plt.grid(True)
        plt.show()


class Battery:
    def __init__(self, charge, maxCharge, maxPowerCharge, maxPowerDischarge):
        self.maxCharge = maxCharge
        self.charge = min(max(charge, 0.0), maxCharge)
        self.maxPowerCharge = -abs(maxPowerCharge)
        self.maxPowerDischarge = abs(maxPowerDischarge)

    def update(self, deltaPower, time):
        # Positive deltaPower = discharging (energy decreases), negative = charging (energy increases)
        if deltaPower > self.maxPowerDischarge:
            deltaPower = self.maxPowerDischarge
        elif deltaPower < self.maxPowerCharge:
            deltaPower = self.maxPowerCharge

        if self.charge <= 0.0 and deltaPower > 0.0:
            deltaPower = 0.0
        elif self.charge >= self.maxCharge and deltaPower < 0.0:
            deltaPower = 0.0

        projected_charge = self.charge - deltaPower * time
        if projected_charge > self.maxCharge:
            deltaPower = (self.charge - self.maxCharge) / time
        elif projected_charge < 0.0:
            deltaPower = self.charge / time

        self.charge -= deltaPower * time
        return deltaPower


class GuideVane:
    def __init__(self, angle, maxAngle, minAngle, maxAngleChange, time, PK, K_direct):
        self.angle = angle
        self.maxAngle = maxAngle
        self.minAngle = minAngle
        self.maxAngleChange = maxAngleChange
        self.time = time
        self.PK = PK
        self.K_direct = K_direct
        self.lastChange = 0.0
        self.guideWear = 0.0

    def _guideVaneWear(self, change, time):
        step_wear = abs(change * time * self.PK)
        if change * self.lastChange < 0:
            step_wear += self.K_direct
        self.guideWear += step_wear
        if change != 0:
            self.lastChange = change

    def update(self, change, time):
        change = max(-self.maxAngleChange, min(self.maxAngleChange, change))

        projected_angle = self.angle + change * time
        if projected_angle > self.maxAngle:
            change = (self.maxAngle - self.angle) / time
        elif projected_angle < self.minAngle:
            change = (self.minAngle - self.angle) / time

        self._guideVaneWear(change, time)
        self.angle += change * time
        return change


class PIController:
    def __init__(self, p, i, setpoint, timestep, error_deadzone, mini, maxi, initial_output=0.0):
        self.p = p
        self.i = i
        self.setpoint = setpoint
        self.timestep = timestep
        self.error_deadzone = error_deadzone
        self.output = initial_output
        self.maxi = maxi
        self.mini = mini
        self.prev_error = 0.0

    def update(self, value):
        error = self.setpoint - value
        if abs(error) < self.error_deadzone:
            error = 0.0

        delta_p = self.p * (error - self.prev_error)
        delta_i = self.i * error * self.timestep

        self.output = max(self.mini, min(self.maxi, self.output + delta_p + delta_i))
        self.prev_error = error
        return self.output


class Simulation:
    def __init__(
        self,
        signal,
        battery,
        guideVane,
        guideVaneController,
        batteryController,
        lowpass,
        highpass,
        maxPower,
        PK,
        K_direct,
    ):
        self.signal = signal
        self.frequencies = signal["frequencies"]
        self.dailyPrice, self.aFRR, self.FCR = signal["prices"]
        self.time = signal["time"]
        self.dt = self.time[1] - self.time[0]
        self.maxPower = maxPower
        self.PK = PK
        self.K_direct = K_direct

        chargeW, maxCharge, maxPowerCharge, maxPowerDischarge = battery
        self.battery = Battery(chargeW * 3600, maxCharge * 3600, maxPowerCharge, maxPowerDischarge)

        angle, maxAngleChange, minAngle, maxAngle = guideVane
        self.guideVane = GuideVane(angle, maxAngle, minAngle, maxAngleChange, self.dt, self.PK, self.K_direct)
        self.bidPower = guideVaneToPower(angle, self.maxPower)

        self.lowpass = self.filter(*lowpass, type="low")
        self.highpass = self.filter(*highpass, type="high")

        self.guideVaneSignal = np.zeros_like(self.lowpass)
        self.guideVaneChange = np.zeros_like(self.lowpass)
        self.guideVaneAngle = np.zeros_like(self.lowpass)
        self.guideVanePower = np.zeros_like(self.lowpass)

        self.batterySignal = np.zeros_like(self.highpass)
        self.batteryPower = np.zeros_like(self.highpass)
        self.batteryCharge = np.zeros_like(self.highpass)

        p, i, setpoint, error_deadzone, mini, maxi = guideVaneController
        self.guideVaneController = PIController(
            p, i, setpoint, self.dt, error_deadzone, mini, maxi, initial_output=angle
        )

        p, i, setpoint, error_deadzone, mini, maxi = batteryController
        self.batteryController = PIController(
            p, i, setpoint, self.dt, error_deadzone, mini, maxi, initial_output=0.0
        )

        self.plot = Plot(self)

    def filter(self, cutoff_freq=50, order=4, type="low"):
        fs = 1.0 / self.dt
        b, a = scipy.signal.butter(order, cutoff_freq, btype=type, fs=fs)
        return scipy.signal.filtfilt(b, a, self.frequencies)

    def calculateRevenue(self, fcr_share=0.5):
        dt_hours = self.dt / 3600.0

        hydro_MW = (self.guideVanePower) / (1e6)
        battery_MW = self.batteryPower / 1e6
        bid_MW = self.bidPower / 1e6
        max_hydro_MW = self.maxPower / 1e6

        dailyHydroRevenue = np.sum(hydro_MW * self.dailyPrice * dt_hours)
        dailyBatteryRevenue = np.sum(battery_MW * self.dailyPrice * dt_hours)

        min_hydro_MW = max(0.0, guideVaneToPower(self.guideVane.minAngle, max_hydro_MW))
        hydro_band_MW = max(0.0, min(max_hydro_MW - bid_MW, bid_MW - min_hydro_MW))
        #print("Hydro band MW: ", hydro_band_MW)

        batt_band_MW = min(abs(self.battery.maxPowerCharge), self.battery.maxPowerDischarge) / 1e6
        afrr_hydro_MW = (1.0) * hydro_band_MW
        fcr_batt_MW = (1.0 - fcr_share) * batt_band_MW
        afrr_batt_MW = (1.0 - fcr_share) * batt_band_MW


        FCRHydroRevenue = 0.0
        FRRHydroRevenue = np.sum(afrr_hydro_MW * self.aFRR * dt_hours)
        FCRBatteryRevenue = np.sum(fcr_batt_MW * self.FCR * dt_hours)
        FRRBatteryRevenue = np.sum(afrr_batt_MW * self.aFRR * dt_hours)

        self.revenue = {
            "daily_hydro": dailyHydroRevenue,
            "daily_battery": dailyBatteryRevenue,
            "aFRR_hydro": FRRHydroRevenue,
            "aFRR_battery": FRRBatteryRevenue,
            "FCR_hydro": FCRHydroRevenue,
            "FCR_battery": FCRBatteryRevenue,
            "total": (
                dailyHydroRevenue
                + dailyBatteryRevenue
                + FRRHydroRevenue
                + FRRBatteryRevenue
                + FCRHydroRevenue
                + FCRBatteryRevenue
            ),
        }
        return self.revenue

    def update(self, i):
        # High-pass signal is centered around 0 Hz
        batterySignal = self.batteryController.update(self.highpass[i])
        self.batterySignal[i] = batterySignal
        self.batteryPower[i] = self.battery.update(batterySignal, self.dt)
        self.batteryCharge[i] = (self.battery.charge / self.battery.maxCharge) * 100.0

        # Low-pass signal is centered around nominal 50 Hz; compute desired angle rate
        target_angle = self.guideVaneController.update(self.lowpass[i])
        desired_angle_rate = (target_angle - self.guideVane.angle) / self.dt
        self.guideVaneSignal[i] = desired_angle_rate
        self.guideVaneChange[i] = self.guideVane.update(desired_angle_rate, self.dt)
        self.guideVaneAngle[i] = self.guideVane.angle
        self.guideVanePower[i] = guideVaneToPower(self.guideVane.angle, self.maxPower)

    def run(self):
        for i in range(len(self.time)):
            self.update(i)