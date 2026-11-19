import pandas as pd
from runner import run_simulation, load_signal

signal = load_signal()
results = []
for mwh in [0, 2, 5, 10, 20]:
    for fc in [1/500, 1/200, 1/60, 1/10]:
        sim, rev = run_simulation(signal, batt_mwh=mwh, batt_mw=mwh, cutoff_freq=fc)
        results.append({
            "batt_mwh": mwh,
            "cutoff_hz": fc,
            "wear": sim.guideVane.guideWear,
            "revenue_kr": rev["total"] * 11.15,
        })

df = pd.DataFrame(results)
print(df.sort_values("wear"))