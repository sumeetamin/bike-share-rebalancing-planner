"""Download and join the current Citi Bike GBFS station feeds."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


INDEX_URL = "https://gbfs.citibikenyc.com/gbfs/gbfs.json"


def get_json(url):
    request = Request(url, headers={"User-Agent": "bike-share-rebalancing-demo/1.0"})
    with urlopen(request, timeout=30) as response:
        body = response.read()
    return json.loads(body), body


def main():
    index, _ = get_json(INDEX_URL)
    feeds = {feed["name"]: feed["url"] for feed in index["data"]["en"]["feeds"]}
    information, info_body = get_json(feeds["station_information"])
    status, status_body = get_json(feeds["station_status"])
    status_by_id = {str(row["station_id"]): row for row in status["data"]["stations"]}
    stations = []
    for station in information["data"]["stations"]:
        current = status_by_id.get(str(station["station_id"]))
        if current:
            stations.append({**station, **current})

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "station_information_last_updated": information.get("last_updated"),
        "station_status_last_updated": status.get("last_updated"),
        "source_sha256": hashlib.sha256(info_body + b"\n" + status_body).hexdigest(),
        "source_urls": [feeds["station_information"], feeds["station_status"]],
        "stations": stations,
    }
    output = Path("data/citibike_station_snapshot.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2))
    print(f"Saved {len(stations):,} joined stations to {output}")


if __name__ == "__main__":
    main()
