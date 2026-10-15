# Bike Share Rebalancing Planner

A trip-flow planner that converts station departures/arrivals into capped, explainable vehicle redistribution suggestions.

> **Portfolio prototype.** Code is provided; no benchmark results are claimed until you run it on the cited data and record the output.

## Use case

A trip-flow planner that converts station departures/arrivals into capped, explainable vehicle redistribution suggestions. The command below reads a local data export, applies a transparent baseline, writes holdout or decision-support outputs, and saves the fitted model where applicable.

## Data and provenance

[Citi Bike public trip data](https://citibikenyc.com/system-data). A Citi Bike trip CSV with start/end station names. Trips estimate relative flow only; provide current dock inventory and capacity for operational deployment. Dataset files are not bundled. Respect the source terms and cite the dataset when publishing results.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Download/prepare the source data locally, then run:
python main.py --input data/trips.csv --start start_station_name --end end_station_name --capacity 25 --out outputs
```

## Outputs

The `outputs/` directory contains the model-specific results (metrics and/or ranked CSV) and a serialized estimator where applicable. Outputs are reproducible with the same input, package versions, and random seed. The repository intentionally excludes downloaded data and generated artifacts.

## Evaluation and operating notes

Trip net flow is not live inventory, truck capacity, travel time, or a route optimization. Treat suggestions as a planning baseline, not dispatch instructions.

For a production review, preserve a time-based, untouched holdout; compare against a simple business baseline; inspect calibration and subgroup error; document data lineage; and monitor drift. The included baseline is not a production service.

## License

Code: MIT. Third-party datasets remain subject to their original terms.
