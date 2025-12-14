# econ8320-bls-dashboard

## Overview
This project is an automated U.S. labor market dashboard created for **ECON 8320 – Tools for Data Analysis**.  
The dashboard uses data from the U.S. Bureau of Labor Statistics (BLS) to visualize key labor market indicators and updates automatically as new data are released.

## Data Sources
Data are collected using the **BLS Public API**, including:
- Total Nonfarm Employment
- Unemployment Rate
- Labor Force Participation Rate
- Total Nonfarm Job Openings (JOLTS)

## Automation
Data collection is handled through a **GitHub Actions workflow** that runs monthly when new BLS data are released.  
The workflow appends the most recent data to the existing dataset and commits the updated file back to the repository.

The Streamlit dashboard reads from this version-controlled dataset and updates automatically after each successful workflow run.

## Live Dashboard
🔗 https://econ8320-labor-dashboard.streamlit.app