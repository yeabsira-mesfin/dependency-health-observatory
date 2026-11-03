"""Recompute descriptive maintenance-signal summaries from a shared snapshot (no network)."""
import argparse,json
from collections import Counter
from pathlib import Path

def analyze(data):
    if data.get('schema_version')!=1 or not isinstance(data.get('packages'),list): raise ValueError('Unsupported snapshot')
    packages=data['packages'];downstream=data.get('downstream',[])
    names={p['name'] for p in packages}
    by_signal=[]
    for signal in sorted({p['maintenance_signal'] for p in packages}):
        rows=[p for p in packages if p['maintenance_signal']==signal]
        known=[p for p in rows if p['advisories_for_latest'] is not None]
        exposed=sum(p['advisories_for_latest']>0 for p in known)
        by_signal.append({'signal':signal,'packages':len(rows),'advisory_status_known':len(known),'latest_versions_with_advisories':exposed,'observed_advisory_fraction':exposed/len(known) if known else None})
    return {'packages':len(packages),'maintenance_signal_counts':dict(Counter(p['maintenance_signal'] for p in packages)),'by_signal_and_advisories':by_signal,'downstream_outcomes':dict(Counter(d['outcome'] for d in downstream)),'downstream_packages_with_health_observations':sum(d['package'] in names for d in downstream),'interpretation':'Descriptive convenience sample. No causal or predictive risk claim.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('input',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]/'public/data/observatory.json');args=p.parse_args();print(json.dumps(analyze(json.loads(args.input.read_text())),indent=2))
if __name__=='__main__':main()
