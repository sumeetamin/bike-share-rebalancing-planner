# Bike Share Rebalancing Planner

A live station snapshot tool that creates transparent donor-to-receiver transfer suggestions from Citi Bike's GBFS data.

## Current snapshot demonstration

The public [Citi Bike System Data](https://citibikenyc-marketing.lyft.net/system-data) page publishes trip histories and GBFS station feeds. This run joined 2,519 station records; 2,469 active stations passed the capacity and status checks. Under the configured rule (donors above 80% fill, receivers below 20%, target 50%, maximum 2.5 km straight-line pairing), the greedy nearest-pair heuristic produced 393 transfer pairs covering 2,538 bikes. It left 1,569 donor bikes and 3,926 receiver slots unmatched under the distance constraint.

This is one live snapshot, not a predictive backtest or operational dispatch plan. The result does not account for truck capacity, roads, traffic, labor, bike type, demand forecasts, or travel time. Recheck status before any operational use. The exact station-level move list is not published; only aggregate counts and feed fingerprint are in [\`reports/benchmark.json\`](reports/benchmark.json).

## Reproduce

\`\`\`bash
python -m pip install -r requirements.txt
python fetch_data.py
python main.py --target-fill 0.5 --low-fill 0.2 --high-fill 0.8 \\
  --max-age-minutes 10 --max-distance-m 2500 --out outputs
\`\`\`

The fetcher discovers the current station-information and station-status URLs from GBFS. The planner refuses snapshots older than the configured limit and writes individual moves only to the ignored local \`outputs/\` directory. Citi Bike's data use policy applies to its feeds.
