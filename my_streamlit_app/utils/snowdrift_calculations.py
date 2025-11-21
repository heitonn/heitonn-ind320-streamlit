"""
Snow drift calculations based on Tabler (2003).
Adapted from Snow_drift.py for Streamlit integration.
"""

import numpy as np
import pandas as pd


def compute_Qupot(hourly_wind_speeds, dt=3600):
    """
    Compute the potential wind-driven snow transport (Qupot) [kg/m]
    by summing hourly contributions using u^3.8.
    
    Formula:
       Qupot = sum((u^3.8) * dt) / 233847
    """
    total = sum((u ** 3.8) * dt for u in hourly_wind_speeds) / 233847
    return total


def sector_index(direction):
    """
    Given a wind direction in degrees, returns the index (0-15)
    corresponding to a 16-sector division.
    """
    # Center the bin by adding 11.25° then modulo 360 and divide by 22.5°
    return int(((direction + 11.25) % 360) // 22.5)


def compute_sector_transport(hourly_wind_speeds, hourly_wind_dirs, dt=3600):
    """
    Compute the cumulative transport for each of 16 wind sectors.
    
    Parameters:
      hourly_wind_speeds: list of wind speeds [m/s]
      hourly_wind_dirs: list of wind directions [degrees]
      dt: time step in seconds
      
    Returns:
      A list of 16 transport values (kg/m) corresponding to the sectors.
    """
    sectors = [0.0] * 16
    for u, d in zip(hourly_wind_speeds, hourly_wind_dirs):
        idx = sector_index(d)
        sectors[idx] += ((u ** 3.8) * dt) / 233847
    return sectors


def compute_snow_transport(T, F, theta, Swe, hourly_wind_speeds, dt=3600):
    """
    Compute various components of the snow drifting transport according to Tabler (2003).
    
    Parameters:
      T: Maximum transport distance (m)
      F: Fetch distance (m)
      theta: Relocation coefficient
      Swe: Total snowfall water equivalent (mm)
      hourly_wind_speeds: list of wind speeds [m/s]
      dt: time step in seconds
      
    Returns:
      A dictionary containing:
         Qupot (kg/m): Potential wind-driven transport.
         Qspot (kg/m): Snowfall-limited transport.
         Srwe (mm): Relocated water equivalent.
         Qinf (kg/m): The controlling transport value.
         Qt (kg/m): Mean annual snow transport.
         Control: Process controlling the transport (wind or snowfall).
    """
    Qupot = compute_Qupot(hourly_wind_speeds, dt)
    Qspot = 0.5 * T * Swe  # Snowfall-limited transport [kg/m]
    Srwe = theta * Swe    # Relocated water equivalent [mm]
    
    if Qupot > Qspot:
        Qinf = 0.5 * T * Srwe
        control = "Snowfall controlled"
    else:
        Qinf = Qupot
        control = "Wind controlled"
    
    Qt = Qinf * (1 - 0.14 ** (F / T))
    
    return {
        "Qupot (kg/m)": Qupot,
        "Qspot (kg/m)": Qspot,
        "Srwe (mm)": Srwe,
        "Qinf (kg/m)": Qinf,
        "Qt (kg/m)": Qt,
        "Control": control
    }


def compute_yearly_results(df, T, F, theta):
    """
    Compute the yearly (seasonal) snow transport parameters for every season in the data.
    The season is defined as July 1 of a given year to June 30 of the next year.
    
    Returns a DataFrame with one row per season.
    """
    seasons = sorted(df['season'].unique())
    results_list = []
    for s in seasons:
        season_start = pd.Timestamp(year=s, month=7, day=1)
        season_end = pd.Timestamp(year=s+1, month=6, day=30, hour=23, minute=59, second=59)
        df_season = df[(df['time'] >= season_start) & (df['time'] <= season_end)]
        if df_season.empty:
            continue
        # Calculate hourly Swe: precipitation counts when temperature < +1°C.
        df_season = df_season.copy()  # avoid SettingWithCopyWarning
        df_season['Swe_hourly'] = df_season.apply(
            lambda row: row['precipitation'] if row['temperature_2m'] < 1 else 0, axis=1)
        total_Swe = df_season['Swe_hourly'].sum()
        wind_speeds = df_season["wind_speed_10m"].tolist()
        result = compute_snow_transport(T, F, theta, total_Swe, wind_speeds)
        result["season"] = f"{s}-{s+1}"
        result["start_year"] = s
        results_list.append(result)
    return pd.DataFrame(results_list)


def compute_average_sector(df):
    """
    Compute the average directional breakdown (sectors) over all seasons.
    The function groups the data by season and computes the sector contributions
    for each season, then returns the mean across seasons.
    """
    sectors_list = []
    for s, group in df.groupby('season'):
        group = group.copy()
        group['Swe_hourly'] = group.apply(
            lambda row: row['precipitation'] if row['temperature_2m'] < 1 else 0, axis=1)
        ws = group["wind_speed_10m"].tolist()
        wdir = group["wind_direction_10m"].tolist()
        sectors = compute_sector_transport(ws, wdir)
        sectors_list.append(sectors)
    avg_sectors = np.mean(sectors_list, axis=0)
    return avg_sectors


def compute_fence_height(Qt, fence_type):
    """
    Calculate the necessary effective fence height (H) for storing a given snow drift.
    
    Parameters:
      Qt : float
           The calculated mean annual snow transport (drift) in kg/m.
      fence_type : str
           The fence type. Supported types are:
           "Wyoming", "Slat-and-wire", and "Solid".
    
    Returns:
      H : float
          The necessary effective fence height (in meters).
    
    Calculation:
      1. Convert Qt from kg/m to tonnes/m (divide by 1000).
      2. Use the storage capacity factor for the selected fence type:
             - Wyoming: 8.5
             - Slat-and-wire: 7.7
             - Solid: 2.9
      3. Calculate H = ( (Qt_tonnes) / (factor) )^(1/2.2)
    """
    Qt_tonnes = Qt / 1000.0
    if fence_type.lower() == "wyoming":
        factor = 8.5
    elif fence_type.lower() in ["slat-and-wire", "slat and wire"]:
        factor = 7.7
    elif fence_type.lower() == "solid":
        factor = 2.9
    else:
        raise ValueError("Unsupported fence type. Choose 'Wyoming', 'Slat-and-wire', or 'Solid'.")
    
    H = (Qt_tonnes / factor) ** (1 / 2.2)
    return H
