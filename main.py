"""Turn trip-level station flows into interpretable rebalancing moves."""
import argparse
from pathlib import Path
import pandas as pd
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--input",required=True);p.add_argument("--start",default="start_station_name");p.add_argument("--end",default="end_station_name");p.add_argument("--capacity",type=int,default=20);p.add_argument("--target-fill",type=float,default=.5);p.add_argument("--out",default="outputs");a=p.parse_args()
 d=pd.read_csv(a.input,usecols=[a.start,a.end]).dropna();outflows=d[a.start].value_counts();inflows=d[a.end].value_counts();stations=sorted(set(outflows.index)|set(inflows.index))
 net=pd.DataFrame({"station":stations,"departures":[int(outflows.get(s,0)) for s in stations],"arrivals":[int(inflows.get(s,0)) for s in stations]})
 net["net_flow"]=net.arrivals-net.departures
 # A trip sample has no true dock inventory; this translates net-flow ranks into capped planning suggestions.
 net["estimated_delta"]=net.net_flow.clip(-a.capacity,a.capacity);target=round(a.capacity*a.target_fill)
 net["suggested_bikes"]= (target-net.estimated_delta).clip(-a.capacity,a.capacity).astype(int)
 net["action"]=net.suggested_bikes.map(lambda n:"deliver" if n>0 else ("collect" if n<0 else "none"))
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True);net.sort_values("suggested_bikes",ascending=False).to_csv(out/"station_rebalance_plan.csv",index=False)
 print(f"Processed {len(d):,} trips across {len(net):,} stations; wrote {out/'station_rebalance_plan.csv'}. Estimates are relative flows, not observed dock stock.")
if __name__=="__main__":main()
