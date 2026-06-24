# Hydro-Climate Diagnostic: Tracking the 2026 ENSO Phase & Rain Distribution

An interactive, production-grade Python Streamlit web application designed for real-time climate monitoring. The system ingests live, gridded datasets directly from NOAA's Thredds OPeNDAP data servers to calculate area-weighted sea surface temperature (SST) anomalies, track the development vector of the 2026 ENSO phase, and map synchronous global terrestrial precipitation anomalies.

---

## 🚀 Live Deployment
The application is deployed and available to the public via the **Streamlit Community Cloud Platform**. 
👉 **[Access the Live Dashboard Here](https://elnino-56ewzkpczgzdgrno8snsoc.streamlit.app/)** 

---

## ✨ Key Features
* **Real-Time Data Streams:** Utilizes lazy loading (`xarray` OPeNDAP connection) to fetch spatial matrices from NOAA without high local memory overhead.
* **Dynamic Niño 3.4 Tracking:** Computes daily area-weighted (cosine of latitude correction) SST anomalies inside the primary ENSO monitoring zone ($5^\circ\text{N} - 5^\circ\text{S}, 170^\circ\text{W} - 120^\circ\text{W}$).
* **Dual Spatial Diagnostics:** * A Pacific-centered Global SST Anomaly Map (*Robinson* projection) highlighting the developing Super El Niño envelope.
  * A Global Terrestrial Precipitation Map (*PlateCarree* projection) isolating real-time moisture distribution anomalies.
* **Automated Meteorological Synopsis:** Uses rule-based logical engines to generate daily text summaries analyzing ocean thermal states and regional teleconnection responses.

---

## 📊 Data Lineage & Science Framework
* **Ocean Surface Temperatures:** NOAA Daily Optimum Interpolation SST (OISST) v2.1 High-Resolution ($0.25^\circ \times 0.25^\circ$ grid).
* **Terrestrial Rainfall:** NOAA Climate Prediction Center (CPC) Global Unified Gauge-Based Precipitation ($0.5^\circ \times 0.5^\circ$ grid).
* **Climatology Baseline:** Long-Term Mean (LTM) calculated over a 30-year climate window (1991–2020).

---

## 💻 Local Installation & Setup

Follow these steps to clone the repository and run the application locally on your machine.

### Prerequisites
Ensure you have **Python 3.10** installed. It is highly recommended to run this inside an isolated virtual environment.

### Step 1: Clone the Repository
```bash
git clone [https://github.com/AntonyJosephy/elnino.git]
cd elnino
```
### Step 2: Set Up a Virtual Environment
#### Create an environment called py310
```python -m venv py310```

#### Activate the environment
# On Windows:
```py310\Scripts\activate```

#### On macOS/Linux:
```source py310/bin/activate```

### Step 3: Install Required Dependencies
Upgrade pip and install the geospatial and analytical dependencies compiled for your architecture:
```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
### Step 4: Run the Streamlit Application
To safely isolate environment paths on local systems, invoke the application using the Python module flag:
```
python -m streamlit run nino_tracker.py
```
The application will spin up a local server, automatically opening your default web browser to ```http://localhost:8501```
The dashboard takes a while to load during the first run because the pipeline fetches data and performs calculations.
