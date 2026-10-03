# Consumer-app comparison — unavailable

The user confirmed that a second-app scan is not feasible tonight. No app performance or beat/tie percentage is claimed. Do not substitute Stray pose/depth data for an independent consumer app's exported plan.

For a later comparison, add original exports for the kitchen and hall, name the app and version, and fill `dimensions.csv` with columns:

`room,dimension_id,truth_m,pipeline_m,app_m,app_name,app_version`

Dimensions must refer to the same physical wall/opening/height in both systems. Missing predictions remain missing and count as failures; do not retain only convenient shared dimensions. `scripts/compare_app.py` produces the dimension-by-dimension table once actual exports are available.
