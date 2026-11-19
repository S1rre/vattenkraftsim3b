import streamlit as st
import matplotlib.pyplot as plt
from runner import load_signal, run_simulation

st.set_page_config(page_title="Hybrid Hydropower Simulator", layout="wide")

@st.cache_data
def get_signal():
    return load_signal()

signal = get_signal()

st.sidebar.header("Battery & Filter")
batt_mwh = st.sidebar.slider("Battery Capacity (MWh)", 0.0, 30.0, 5.0, 0.5)
batt_mw = st.sidebar.slider("Battery Max Power (MW)", 0.0, 20.0, 5.0, 0.5)
cutoff_freq = st.sidebar.number_input("Cutoff Frequency (Hz)", 0.0005, 2.0, 0.005, format="%.4f")
filter_order = st.sidebar.selectbox("Filter Order", [1, 2, 3, 4], index=1)

st.sidebar.header("PI Controllers")
batt_p = st.sidebar.slider("Battery P (MW/Hz)", 0.0, 100.0, 25.0, 1.0) * 1e6
hydro_p = st.sidebar.slider("Hydro P", 0.0, 0.2, 0.03, 0.005)
hydro_i = st.sidebar.number_input("Hydro I", 0.0, 0.01, 0.00005, format="%.6f")
deadzone = st.sidebar.number_input("Deadzone (Hz)", 0.0, 0.05, 0.005, format="%.4f")

st.sidebar.header("Display & Market")
hours = st.sidebar.slider("Plot Window (hours)", 0, 168, (0, 24))
fcr_share = st.sidebar.slider("FCR Share", 0.0, 1.0, 0.5, 0.05)

sim, rev = run_simulation(
    signal,
    batt_mwh=batt_mwh,
    batt_mw=batt_mw,
    cutoff_freq=cutoff_freq,
    filter_order=filter_order,
    batt_p=batt_p,
    hydro_p=hydro_p,
    hydro_i=hydro_i,
    deadzone=deadzone,
    fcr_share=fcr_share,
)

# KPI Summary Row
col1, col2, col3 = st.columns(3)
col1.metric("Guide Vane Wear", f"{sim.guideVane.guideWear:,.1f}")
col2.metric("Total Revenue", f"{rev['total'] * 11.15:,.0f} kr".replace(",", " "))
col3.metric("FCR Battery Revenue", f"{rev['FCR_battery'] * 11.15:,.0f} kr".replace(",", " "))

# Render plots (assumes your Plot methods draw on the active matplotlib figure)
for plot_fn in [sim.plot.frequency, sim.plot.battery, sim.plot.guideVane, sim.plot.generatorPower]:
    plt.figure()
    plot_fn(hours)
    st.pyplot(plt.gcf())
    plt.close()