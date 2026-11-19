class GenerateFrequency():
    def __init__(self, simulation_time, frequency, resolution, noise_amplitude) -> None:
        # Frequency generation
        self.simulation_time = simulation_time
        self.frequency = frequency
        self.resolution = resolution * simulation_time
        self.noise_amplitude = noise_amplitude
        # Generate signals
        self.time = np.linspace(0, self.simulation_time, self.resolution)
        self.f_base = self.generate_base_frequenct()
        self.white_noise = self.generate_whitenoise()
        self.harmonics = self.generate_harmonics()
        self.frequency_signal = self.f_base + self.white_noise + self.harmonics

    def generate_base_frequenct(self):
        f_base = np.full_like(self.time, self.frequency) # base frequency of 50hz
        #f_base = np.sin(2 * np.pi * self.frequency * self.time)
        return f_base

    def generate_whitenoise(self):
        white_noise = np.random.normal(0, self.noise_amplitude, self.resolution)
        return white_noise
    def generate_harmonics(self):
        harmonic_frequencies = [0.01, 0.1, 1, 2, 3, 4, 5]
        harmonic_amplitudes = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]

        harmonics = [
        (harmonic_amplitudes[len(harmonic_amplitudes)-1-i] * np.sin(2 * np.pi * harmonic_frequencies[i] * self.time)) 
        for i in range(len(harmonic_amplitudes))
        ]
        return sum(harmonics)

    def plot_amplitude(self, time):
        mask = self.time <= time
        plt.plot(self.time[mask], self.frequency_signal[mask])
        plt.title("Simulated Grid Frequency with White Noise and Harmonics")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.show()
    
    def filter(self,cutoff_freq = 50, order = 4):
        #Getting the sampling frequency
        dt = self.time[1] - self.time[0]
        fs = 1.0 / dt

        b, a = scipy.signal.butter(order, cutoff_freq, btype='low', fs=fs)

        filtered = scipy.signal.filtfilt(b, a, self.frequency_signal)
        return filtered

    #def plot_spectrum(self):LEGACY
        # # 2. Determine sample spacing (dt) and number of samples (N)
        # # This assumes self.simulation_time is a numpy array of evenly spaced time steps
        # dt = 1 / self.simulation_time
        # N = len(self.time)
        
        # # 3. Compute the FFT
        # fft_values = np.fft.fft(self.frequency_signal)
        # fft_freqs = np.fft.fftfreq(N, dt)
        
        # # 4. Extract only the positive frequencies
        # pos_mask = fft_freqs > 0
        # freqs = fft_freqs[pos_mask]
        
        # # 5. Calculate amplitude (normalize by N and multiply by 2 for the single-sided spectrum)
        # amplitudes = (2.0 / N) * np.abs(fft_values[pos_mask])
        
        # # Optional: Calculate power (amplitude squared)
        # power = amplitudes ** 2
        
        # # 6. Plot the results
        # plt.figure(figsize=(10, 5))
        
        # # Plotting Amplitude vs Frequency (you can swap 'amplitudes' with 'power' if preferred)
        # plt.plot(freqs, amplitudes, marker='o', linestyle='-', color='b')
        
        # # Format the plot
        # plt.title('Frequency Spectrum of Generated Signal')
        # plt.xlabel('Frequency (Hz)')
        # plt.ylabel('Amplitude')
        
        # # Limit x-axis to slightly above your max frequency (5 Hz) for a clear view
        # plt.xlim(0, 100) 
        # plt.grid(True)
        # plt.show()
    #def plot_frequency(self): LEGACY
        # analytic_signal = scipy.signal.hilbert(self.frequency_signal)
        # instantaneous_phase = np.unwrap(np.angle(analytic_signal))

        # dt = 1 / self.simulation_time
        # freq_t = np.gradient(instantaneous_phase, dt) / (2.0 * np.pi)
        # print(dt)
        # plt.figure(figsize=(10, 5))

        # # Plot magnitude in dB scale (10 * log10(Sxx)) for better visual contrast
        # plt.plot(self.time, freq_t)
        # plt.xlabel('Time [s]')
        # plt.ylabel('Frequency [Hz]')
        # plt.title('Spectrogram (Frequency vs. Time)')
        # plt.show()
