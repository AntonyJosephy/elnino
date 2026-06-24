import streamlit as st
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
from datetime import datetime

# Configure Streamlit page layout
st.set_page_config(
    page_title="Hydro-Climate Diagnostic: Tracking 2026 ENSO",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Hydro-Climate Diagnostic: Tracking the 2026 ENSO Phase & Rain Distribution")
st.markdown("---")

# -----------------------------------------------------------------------------
# Data Ingestion & Processing Layer (Cached to prevent redundant server hitting)
# -----------------------------------------------------------------------------

@st.cache_data(ttl=86400) # Cache expires daily
def load_and_process_data():
    """Fetches real-time SST, Climatology, and Precipitation data from NOAA."""
    current_year_url = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.2026.nc"
    climatology_url = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.ltm.1991-2020.nc"
    precip_url = "https://psl.noaa.gov/thredds/dodsC/Datasets/cpc_global_precip/precip.2026.nc"
    
    # Open OPeNDAP streams lazily
    ds_current = xr.open_dataset(current_year_url)
    ds_climo = xr.open_dataset(climatology_url, use_cftime=True)
    ds_precip = xr.open_dataset(precip_url)
    
    # Extract temporal dimensions
    times = ds_current['time'].values
    date_str = ds_current['time'].isel(time=-1).dt.strftime('%B %d, %Y').values.item()
    day_of_year = ds_current['time'].dt.dayofyear.values
    
    # --- 1. Compute Niño 3.4 Region Timeseries (0-360 E coordinates) ---
    nino34_cur = ds_current['sst'].sel(lat=slice(-5, 5), lon=slice(190, 240))
    nino34_cli = ds_climo['sst'].sel(lat=slice(-5, 5), lon=slice(190, 240))
    
    # Compute Area Weights
    weights = np.cos(np.deg2rad(nino34_cur.lat))
    
    # Compute Weighted Spatial Means
    sst_cur_mean = nino34_cur.weighted(weights).mean(dim=['lat', 'lon'])
    climo_vals = nino34_cli.isel(time=day_of_year - 1)
    sst_cli_mean = climo_vals.weighted(weights).mean(dim=['lat', 'lon'])
    
    # Raw values extraction to prevent coordinate collision during subtraction
    anomalies_ts = sst_cur_mean.values - sst_cli_mean.values
    
    # --- 2. Compute Latest Global SST Anomaly Map ---
    latest_sst = ds_current['sst'].isel(time=-1)
    latest_climo = ds_climo['sst'].isel(time=day_of_year[-1] - 1)
    global_sst_anom = latest_sst - latest_climo
    
    # Reindex 0-360 Lon map to standard -180 to 180 for Cartopy
    global_sst_anom = global_sst_anom.roll(lon=len(global_sst_anom.lon) // 2, roll_coords=True)
    new_lons_sst = global_sst_anom.lon.values
    new_lons_sst[new_lons_sst >= 180] -= 360
    global_sst_anom = global_sst_anom.assign_coords(lon=new_lons_sst).sortby('lon')
    
    # --- 3. Process Latest Precipitation Data ---
    latest_precip = ds_precip['precip'].isel(time=-1)
    latest_precip = latest_precip.roll(lon=len(latest_precip.lon) // 2, roll_coords=True)
    new_lons_pcp = latest_precip.lon.values
    new_lons_pcp[new_lons_pcp >= 180] -= 360
    latest_precip = latest_precip.assign_coords(lon=new_lons_pcp).sortby('lon')
    return times, anomalies_ts, global_sst_anom, latest_precip, date_str

# Run ingestion pipeline
try:
    times, anomalies_ts, sst_anom, precip, latest_date = load_and_process_data()
except Exception as e:
    st.error(f"Failed to fetch data from NOAA OPeNDAP servers: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# Sidebar Status Panel
# -----------------------------------------------------------------------------
st.sidebar.header("📊 System Diagnostics")
st.sidebar.metric(label="Data Current As Of", value=str(latest_date))

current_oni = anomalies_ts[-1]
st.sidebar.metric(
    label="Current Niño 3.4 Index", 
    value=f"{current_oni:+.2f} °C",
    delta="Super El Niño Threshold Active (> +2.0°C)" if current_oni >= 2.0 else "Developing State"
)

st.sidebar.markdown("""
**Data Lineage:**
* **Ocean:** NOAA OISST v2.1 High-Res ($0.25^\circ$)
* **Rainfall:** NOAA CPC Gauge-Based ($0.5^\circ$)
* **Climatology Baseline:** 1991-2020 LTM
""")

# -----------------------------------------------------------------------------
# Row 1: Niño 3.4 Evolution Timeseries
# -----------------------------------------------------------------------------
st.subheader("1. Niño 3.4 Regional SST Anomaly Timeseries Evolution")

fig_ts, ax_ts = plt.subplots(figsize=(15, 4.5))
ax_ts.axhline(0, color='gray', linestyle='--', linewidth=1)
ax_ts.axhline(0.5, color='orange', linestyle=':', linewidth=1.2, label='El Niño Threshold')
ax_ts.axhline(2.0, color='red', linestyle=':', linewidth=1.5, label='Super El Niño Threshold')

ax_ts.plot(times, anomalies_ts, color='black', linewidth=2, label='Observed Index')
ax_ts.fill_between(times, anomalies_ts, 0, where=(anomalies_ts >= 0), color='crimson', alpha=0.3)
ax_ts.fill_between(times, anomalies_ts, 0, where=(anomalies_ts < 0), color='royalblue', alpha=0.3)

ax_ts.xaxis.set_major_locator(mdates.MonthLocator(interval=1)) # Show tick marks for every month
ax_ts.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y')) # Format as 'Jan 2026'
fig_ts.autofmt_xdate() # Auto-rotate the date text slightly so they don't overlap

ax_ts.set_ylabel('SST Anomaly (°C)', fontweight='bold')
ax_ts.set_title(f"Niño 3.4 Index Track Vector — Updated {latest_date}", fontsize=12, fontweight='bold', pad=10)
ax_ts.grid(True, alpha=0.3, linestyle='--')
ax_ts.legend(loc='upper left')

st.pyplot(fig_ts)

st.markdown("---")

# -----------------------------------------------------------------------------
# Row 2: Spatial Diagnostics (SST Anomaly vs Precipitation Distributions)
# -----------------------------------------------------------------------------
st.subheader("2. Global Sea Surface Temperature Anomalies")
    
fig_sst = plt.figure(figsize=(10, 6))
ax_sst = plt.axes(projection=ccrs.Robinson(central_longitude=180))
    
ax_sst.add_feature(cfeature.LAND, facecolor='#d9d9d9', edgecolor='black', linewidth=0.5, zorder=1)
ax_sst.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=2)
# Custom asymmetric divergent scale for extreme event mapping
norm_sst = mcolors.TwoSlopeNorm(vmin=-3.0, vcenter=0.0, vmax=4.5)
    
mesh_sst = ax_sst.pcolormesh(
    sst_anom.lon, sst_anom.lat, sst_anom.values,
    transform=ccrs.PlateCarree(), cmap='RdBu_r', norm=norm_sst, shading='auto'
)
    
# Explicitly project and highlight the Niño 3.4 boundaries
ax_sst.plot(
    [-170, -120, -120, -170, -170], [-5, -5, 5, 5, -5],
    transform=ccrs.PlateCarree(), color='black', linewidth=2, linestyle='-', zorder=3
)
ax_sst.text(
    -145, 8, 'Niño 3.4', transform=ccrs.PlateCarree(),
    color='black', fontweight='bold', horizontalalignment='center', zorder=4
)
    
cbar_sst = plt.colorbar(mesh_sst, ax=ax_sst, orientation='horizontal', pad=0.05, shrink=0.8)
cbar_sst.set_label('SST Anomaly (°C)', fontweight='bold')
st.pyplot(fig_sst)

st.markdown("---")
st.subheader("3. Terrestrial Rain Distribution Map")
fig_pcp = plt.figure(figsize=(10, 6))
# PlateCarree preferred to preserve coordinate clarity for terrestrial gauge grids
ax_pcp = plt.axes(projection=ccrs.PlateCarree())
    
ax_pcp.add_feature(cfeature.LAND, facecolor='#f5f5f5', zorder=1)
ax_pcp.add_feature(cfeature.COASTLINE, linewidth=0.6, edgecolor='#404040', zorder=3)
ax_pcp.add_feature(cfeature.BORDERS, linewidth=0.4, linestyle=':', edgecolor='#737373', zorder=3)
    
# Mask dry grid points (< 0.1 mm) to allow pure basemap scannability
precip_masked = precip.where(precip > 0.1)
    
mesh_pcp = ax_pcp.pcolormesh(
    precip.lon, precip.lat, precip_masked.values,
    transform=ccrs.PlateCarree(), cmap='YlGnBu', vmin=0, vmax=60, shading='auto', zorder=2
)
cbar_pcp = plt.colorbar(mesh_pcp, ax=ax_pcp, orientation='horizontal', pad=0.05, shrink=0.8)
cbar_pcp.set_label('Daily Precipitation Accumulation (mm)', fontweight='bold')
st.pyplot(fig_pcp)

# -----------------------------------------------------------------------------
# Bottom Layer: Automated Diagnostic Summaries
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("Meteorological Synopsis")

def generate_automated_insights(oni_val, sst_grid, precip_grid):
    """Generates dynamic text summaries based on real-time data arrays."""
    
    # 1. ENSO Status Logic
    if oni_val >= 2.0:
        enso_status = f"🔴 **Super El Niño Active:** The Niño 3.4 index currently sits at **+{oni_val:.2f} °C**. Intense ocean-atmosphere coupling is driving major global weather disruptions and shifting the Walker Circulation."
    elif oni_val >= 0.5:
        enso_status = f"🟠 **El Niño Active:** The index is at **+{oni_val:.2f} °C**, indicating firmly established equatorial warming in the central Pacific."
    elif oni_val <= -0.5:
        enso_status = f"🔵 **La Niña Active:** The index is **{oni_val:.2f} °C**, showing anomalous cooling."
    else:
        enso_status = f"⚪ **ENSO Neutral:** The index is **{oni_val:.2f} °C**, remaining within normal baseline boundaries."

    # 2. Global SST Logic
    # Extract the absolute maximum positive anomaly from the global grid
    max_anom = float(sst_grid.max().values)
    sst_insight = f"🌡️ **Ocean Thermal State:** Peak sea surface temperature anomalies across the global grid are currently hitting maximums of **+{max_anom:.1f} °C**. The equatorial Pacific remains the primary thermodynamic driver."

    # 3. Regional Precipitation Logic
    # Using boolean masks safely extracts data regardless of xarray's ascending/descending coordinate orders
    # We focus on a classic teleconnection zone: East Africa (approx 5°S to 5°N, 34°E to 42°E)
    ea_lat_mask = (precip_grid.lat >= -5) & (precip_grid.lat <= 5)
    ea_lon_mask = (precip_grid.lon >= 34) & (precip_grid.lon <= 42)
    ea_precip = float(precip_grid.where(ea_lat_mask & ea_lon_mask).mean().values)
    
    precip_insight = f"🌧️ **Hydrological Impacts:** Convection patterns are heavily altered. Key teleconnection zones, such as the East African sector (including the Kenyan highlands and Rift Valley), are currently registering regional daily averages of **{ea_precip:.1f} mm**."

    return enso_status, sst_insight, precip_insight

# Fetch the automated text using the variables already calculated in the app
enso_text, sst_text, precip_text = generate_automated_insights(current_oni, sst_anom, precip)

# Display the insights side-by-side using Streamlit columns for a dashboard feel
sum_col1, sum_col2, sum_col3 = st.columns(3)

with sum_col1:
    st.info(enso_text)
with sum_col2:
    st.warning(sst_text)
with sum_col3:
    st.success(precip_text)
    
# -----------------------------------------------------------------------------
# App Metadata & Professional Sign-off
# -----------------------------------------------------------------------------
st.markdown("---")
st.info(f"""
💡 **El Nino Southern Oscillation Diagnostic System developed by:**
* **Ouma Antony:** Meteorologist & Data Scientist
* **Email Contact:** antony.ouma111@gmail.com
* **Professional Network:** [LinkedIn](https://linkedin.com/in/antony-ouma-2610906b/)
""")