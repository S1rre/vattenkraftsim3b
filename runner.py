import numpy as np
from kraftverkssimulering import Simulation

def load_signal(filepath="./DataKod/grid_data.npz"):
    data = np.load(filepath)
    f = data["frequencies"]
    time = np.arange(len(f)) * data["time"][1] / 1000.0

    valid = f != 0
    idx = np.arange(len(f))
    f_clean = np.interp(idx, idx[valid], f[valid])

    return {
        "frequencies": f_clean,
        "time": time,
        "prices": (
            np.asarray(data["dailyPrice"], dtype=float),
            np.asarray(data["aFRR"], dtype=float),
            np.asarray(data["FCR"], dtype=float),
        ),
    }

def run_simulation(
    signal,
    batt_mwh=5.0,
    batt_mw=5.0,
    soc_init=0.5,
    cutoff_freq=1/200,
    filter_order=2,
    batt_p=25e6,
    batt_i=0.0,
    hydro_p=0.03,
    hydro_i=0.00005,
    deadzone=0.005,
    max_power_mw=100.0,
    pk=0.0001,
    k_direct=300.0,
    fcr_share=0.5,
):
    batt_wh = batt_mwh * 1e6
    batt_w = batt_mw * 1e6

    battery = (batt_wh * soc_init, batt_wh, batt_w, batt_w)
    guide_vane = (0.65, 0.02, 0.5, 0.8)

    battery_ctrl = (batt_p, batt_i, 0.0, deadzone, -batt_w, batt_w)
    hydro_ctrl = (hydro_p, hydro_i, 50.0, deadzone, -0.02, 0.02)

    lowpass = (cutoff_freq, filter_order)
    highpass = (cutoff_freq, filter_order)

    sim = Simulation(
        signal, battery, guide_vane,
        hydro_ctrl, battery_ctrl,
        lowpass, highpass,
        max_power_mw * 1e6, pk, k_direct
    )
    sim.run()
    rev = sim.calculateRevenue(fcr_share=fcr_share)
    return sim, rev