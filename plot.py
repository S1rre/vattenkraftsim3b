import numpy as np
import matplotlib.pyplot as plt


class Plot:
    _TIME_SCALES = {
        "s": (1.0, "Time (s)"),
        "min": (60.0, "Time (min)"),
        "h": (3600.0, "Time (h)"),
    }

    def __init__(self, simulation, time_unit="h"):
        self.sim = simulation
        if time_unit not in self._TIME_SCALES:
            raise ValueError(f"time_unit must be one of {list(self._TIME_SCALES)}")
        self.time_unit = time_unit

    def _apply_mask(self, *arrays, mask=None, time_unit=None):
        """Filters time and data arrays using a mask, scaling time to the active unit."""
        unit = time_unit or self.time_unit
        scale, xlabel = self._TIME_SCALES[unit]
        t = np.asarray(self.sim.time) / scale

        if isinstance(mask, tuple) and len(mask) == 2:
            idx = (t >= mask[0]) & (t <= mask[1])
        elif mask is not None:
            idx = mask
        else:
            idx = slice(None)

        return t[idx], xlabel, *(np.asarray(arr)[idx] for arr in arrays)

    def _finish(self, fig, title=None, save_path=None):
        """Applies final layout, optional file export, and displays the figure."""
        if title:
            fig.suptitle(title, fontsize=14, fontweight="bold")
        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.show()

    def _overlay_frequency(self, ax, t, freq, primary_label):
        """Overlays grid frequency on a twin y-axis on the given subplot."""
        ax_freq = ax.twinx()
        freq_color = "#7f7f7f"

        line_freq, = ax_freq.plot(
            t, freq, color=freq_color, linestyle=":", linewidth=1.2, alpha=0.85,
            label="Grid Frequency (Hz)",
        )
        ax_freq.axhline(50.0, color=freq_color, linestyle="--", linewidth=0.7, alpha=0.4)
        ax_freq.set_ylabel("Frequency (Hz)", color=freq_color)
        ax_freq.tick_params(axis="y", labelcolor=freq_color)

        # Combine primary and twin legends cleanly
        primary_lines = ax.get_lines()
        if primary_lines:
            primary_lines[0].set_label(primary_label)
            ax.legend(
                [primary_lines[0], line_freq],
                [primary_label, "Grid Frequency (Hz)"],
                loc="upper right",
                frameon=True,
                fontsize=9,
            )

    def _plot_panels(
        self, t, xlabel, panels, suptitle, zero_axes=(), freq_overlay=None, save_path=None
    ):
        """Renders stacked subplots sharing a common time axis.

        freq_overlay: optional tuple (ax_index, freq_array, primary_label)
        """
        fig, axes = plt.subplots(
            len(panels), 1, figsize=(12, 2.7 * len(panels)), sharex=True
        )
        axes = np.atleast_1d(axes)

        for ax, (data, title, ylabel, color, ls) in zip(axes, panels):
            ax.plot(t, data, color=color, linestyle=ls, linewidth=1.1)
            ax.set_title(title, loc="left", fontweight="bold", fontsize=11)
            ax.set_ylabel(ylabel)
            ax.grid(True, linestyle="--", alpha=0.5)

        for idx in zero_axes:
            axes[idx].axhline(0, color="black", linewidth=0.8, alpha=0.5)

        if freq_overlay is not None:
            ax_idx, freq, primary_label = freq_overlay
            self._overlay_frequency(axes[ax_idx], t, freq, primary_label)

        axes[-1].set_xlabel(xlabel)
        self._finish(fig, title=suptitle, save_path=save_path)

    def frequency(self, mask=None, time_unit=None, save_path=None):
        t, xlabel, freq = self._apply_mask(
            self.sim.frequencies, mask=mask, time_unit=time_unit
        )
        fig, ax = plt.subplots(figsize=(12, 4.5))

        ax.plot(t, freq, color="#1f77b4", linewidth=1.0, alpha=0.9, label="Grid Frequency")
        ax.axhline(50.0, color="black", linewidth=1.2, label="Nominal (50.0 Hz)")
        ax.axhline(
            50.1, color="#d62728", linestyle="--", linewidth=1.0, alpha=0.7,
            label="Normal Band (±0.1 Hz)",
        )
        ax.axhline(49.9, color="#d62728", linestyle="--", linewidth=1.0, alpha=0.7)
        ax.axhspan(49.9, 50.1, color="#2ca02c", alpha=0.08)

        ax.set_title("Grid Frequency Over Time", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Frequency (Hz)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper right", frameon=True)
        self._finish(fig, save_path=save_path)

    def price(self, mask=None, time_unit=None, save_path=None):
        t, xlabel, prices = self._apply_mask(
            self.sim.prices, mask=mask, time_unit=time_unit
        )
        fig, ax = plt.subplots(figsize=(12, 4.5))

        ax.plot(t, prices, color="#9467bd", linewidth=1.2)
        ax.set_title("Spot Price Over Time", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Price (EUR/MWh)")
        ax.grid(True, linestyle="--", alpha=0.5)
        self._finish(fig, save_path=save_path)

    def battery(self, mask=None, time_unit=None, overlay_freq=True, save_path=None):
        t, xlabel, charge, power, signal, freq = self._apply_mask(
            self.sim.batteryCharge,
            self.sim.batteryPower,
            self.sim.batterySignal,
            self.sim.frequencies,
            mask=mask,
            time_unit=time_unit,
        )
        panels = [
            (charge, "Battery Charge", "Charge (%)", "#1f77b4", "-"),
            (power / 1e3, "Battery Power", "Power (kW)", "#ff7f0e", "-"),
            (signal / 1e3, "Battery Control Signal", "Signal (kW)", "#2ca02c", "--"),
        ]
        overlay = (0, freq, "Battery Charge (%)") if overlay_freq else None
        self._plot_panels(
            t, xlabel, panels, "Battery Simulation Overview",
            zero_axes=(1, 2), freq_overlay=overlay, save_path=save_path,
        )

    def guideVane(self, mask=None, time_unit=None, save_path=None):
        t, xlabel, angle, change, signal = self._apply_mask(
            self.sim.guideVaneAngle,
            self.sim.guideVaneChange,
            self.sim.guideVaneSignal,
            mask=mask,
            time_unit=time_unit,
        )
        panels = [
            (angle * 100, "Guide Vane Opening", "Opening (%)", "#1f77b4", "-"),
            (change * 100, "Guide Vane Rate of Change", "Rate (%/s)", "#ff7f0e", "-"),
            (signal, "Guide Vane Control Signal", "Signal", "#2ca02c", "--"),
        ]
        self._plot_panels(
            t, xlabel, panels, "Guide Vane Simulation Overview",
            zero_axes=(1, 2), save_path=save_path,
        )

    def generatorPower(self, mask=None, time_unit=None, overlay_freq=True, save_path=None):
        t, xlabel, power, freq = self._apply_mask(
            self.sim.guideVanePower,
            self.sim.frequencies,
            mask=mask,
            time_unit=time_unit,
        )
        panels = [
            (power / 1e6, "Hydroelectric Power", "Power (MW)", "#1f77b4", "-"),
        ]
        overlay = (0, freq, "Hydroelectric Power (MW)") if overlay_freq else None
        self._plot_panels(
            t, xlabel, panels, "Power & Wear Simulation Overview",
            freq_overlay=overlay, save_path=save_path,
        )