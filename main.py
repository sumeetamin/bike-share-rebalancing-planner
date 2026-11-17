"""Plan station-to-station bike transfers from a live GBFS snapshot."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from pathlib import Path


def distance_m(lat_a, lon_a, lat_b, lon_b):
    """Haversine straight-line distance in metres."""
    lat_a, lon_a, lat_b, lon_b = map(radians, (lat_a, lon_a, lat_b, lon_b))
    dlat, dlon = lat_b - lat_a, lon_b - lon_a
    value = sin(dlat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(dlon / 2) ** 2
    return 6_371_000 * 2 * asin(sqrt(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/citibike_station_snapshot.json")
    parser.add_argument("--target-fill", type=float, default=0.5)
    parser.add_argument("--low-fill", type=float, default=0.2)
    parser.add_argument("--high-fill", type=float, default=0.8)
    parser.add_argument("--max-age-minutes", type=float, default=10)
    parser.add_argument("--max-distance-m", type=float, default=2500)
    parser.add_argument("--out", default="outputs")
    args = parser.parse_args()
    if not 0 <= args.low_fill < args.target_fill < args.high_fill <= 1:
        raise SystemExit("Require 0 <= low-fill < target-fill < high-fill <= 1.")

    input_path = Path(args.input)
    snapshot = json.loads(input_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    updated = datetime.fromtimestamp(snapshot["station_status_last_updated"], timezone.utc)
    age_minutes = (now - updated).total_seconds() / 60
    if age_minutes < -5 or age_minutes > args.max_age_minutes:
        raise SystemExit(f"Station status feed is stale or future-dated ({age_minutes:.1f} minutes old).")

    active = []
    for station in snapshot["stations"]:
        capacity = int(station.get("capacity") or 0)
        bikes = int(station.get("num_bikes_available") or 0)
        if capacity <= 0 or station.get("is_installed") != 1:
            continue
        if bikes < 0 or bikes > capacity:
            continue
        active.append({**station, "capacity": capacity, "bikes": bikes})

    donors, receivers = [], []
    for station in active:
        target = round(station["capacity"] * args.target_fill)
        fraction = station["bikes"] / station["capacity"]
        if fraction >= args.high_fill and station.get("is_renting"):
            donors.append({**station, "surplus": max(0, station["bikes"] - target)})
        elif fraction <= args.low_fill and station.get("is_returning"):
            receivers.append({**station, "deficit": max(0, target - station["bikes"])})

    candidates = []
    for donor_index, donor in enumerate(donors):
        for receiver_index, receiver in enumerate(receivers):
            distance = distance_m(donor["lat"], donor["lon"], receiver["lat"], receiver["lon"])
            if distance <= args.max_distance_m:
                candidates.append((distance, donor_index, receiver_index))

    donor_left = [row["surplus"] for row in donors]
    receiver_left = [row["deficit"] for row in receivers]
    moves = []
    for distance, donor_index, receiver_index in sorted(candidates):
        quantity = min(donor_left[donor_index], receiver_left[receiver_index])
        if quantity <= 0:
            continue
        moves.append({
            "from_station_id": str(donors[donor_index]["station_id"]),
            "from_station_name": donors[donor_index].get("name", ""),
            "to_station_id": str(receivers[receiver_index]["station_id"]),
            "to_station_name": receivers[receiver_index].get("name", ""),
            "bikes_to_move": int(quantity),
            "straight_line_distance_m": round(distance, 1),
        })
        donor_left[donor_index] -= quantity
        receiver_left[receiver_index] -= quantity

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    (output / "rebalancing_moves.json").write_text(json.dumps(moves, indent=2))
    summary = {
        "source": "Citi Bike live GBFS station information and station status",
        "source_sha256": snapshot.get("source_sha256") or hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "snapshot_fetched_at": snapshot["fetched_at"],
        "station_status_last_updated": updated.isoformat(),
        "station_status_age_minutes_at_run": round(age_minutes, 2),
        "stations_in_snapshot": int(len(snapshot["stations"])),
        "active_stations_used": int(len(active)),
        "donor_stations": int(len(donors)),
        "receiver_stations": int(len(receivers)),
        "transfer_pairs": int(len(moves)),
        "bikes_to_move": int(sum(row["bikes_to_move"] for row in moves)),
        "total_straight_line_distance_m": round(
            sum(row["bikes_to_move"] * row["straight_line_distance_m"] for row in moves), 1
        ),
        "unmatched_donor_bikes": int(sum(donor_left)),
        "unmatched_receiver_need": int(sum(receiver_left)),
        "policy": "Move stocks above 80% capacity toward stations below 20%, aiming for 50% capacity; greedily pair nearest donor and receiver within 2.5 km.",
        "limitations": "Single live snapshot heuristic. Straight-line distance is not road distance or truck routing; no trip forecasts, vehicle/truck capacity, labor, time, or counterfactual outcomes are modeled. Recheck station status before any operational decision.",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
