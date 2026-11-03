"""Small npm maintenance-signal study. No abandonment verdict or vulnerability inference."""
import argparse, base64, json, re, statistics
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote,urlparse
from .common import JsonClient,CollectionError,instant,write_outputs

ROOT=Path(__file__).resolve().parents[1]
PACKAGE_PATTERN=r'(?:@[a-z0-9_.-]+/)?[a-z0-9][a-z0-9_.-]*'

def valid_package(name):
    if not isinstance(name,str) or len(name)>214 or not re.fullmatch(PACKAGE_PATTERN,name): raise ValueError('Invalid npm package name')
    return name

def signals(metadata,observed_at,archived=None,advisory_count=None):
    if not isinstance(metadata,dict) or not isinstance(metadata.get('versions'),dict): raise ValueError('Package versions are missing')
    name=valid_package(metadata.get('name'))
    latest=metadata.get('dist-tags',{}).get('latest')
    version=metadata['versions'].get(latest)
    if not isinstance(version,dict): raise ValueError('Latest version metadata is missing')
    times=metadata.get('time',{})
    releases=sorted(instant(t) for v,t in times.items() if v in metadata['versions'] and isinstance(t,str))
    last=times.get(latest)
    age=max(0,(instant(observed_at)-instant(last)).days) if last else None
    gaps=[(b-a).total_seconds()/86400 for a,b in zip(releases,releases[1:])]
    deprecated=version.get('deprecated') or None
    status='explicitly deprecated' if deprecated else 'archived' if archived else 'possibly inactive' if age is not None and age>730 else 'infrequent releases' if age is not None and age>365 else 'recent release observed' if age is not None else 'unknown'
    return {'name':name,'latest_version':latest,'last_release':last,'days_since_release':age,'median_release_gap_days':round(statistics.median(gaps),1) if gaps else None,'releases_observed':len(releases),'deprecated':deprecated,'archived':archived,'maintainer_count':len(metadata.get('maintainers',[])),'direct_dependency_count':len(version.get('dependencies',{})),'dependency_ranges':version.get('dependencies',{}),'advisories_for_latest':advisory_count,'maintenance_signal':status,'replacement_recommendation':deprecated if deprecated and re.search(r'\b(use|replace|migrate|instead)\b',deprecated,re.I) else None,'releases_last_year':sum(0 <= (instant(observed_at)-r).days <=365 for r in releases),'observed_at':observed_at}

def github_repository(value):
    url=value.get('url','') if isinstance(value,dict) else value or ''
    match=re.search(r'github\.com[/:]([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)',url)
    return match.group(1).removesuffix('.git') if match else None

def downstream_change(before,after,package,from_date=None,to_date=None,signal_date=None):
    # None is an unavailable manifest; never turn it into an empty manifest.
    if before is None or after is None:
        return {'package':package,'outcome':'unknown','before_range':None,'after_range':None,'resolved_version':None,'right_censored':None,'response_days_upper_bound':None}
    def deps(m):
        result={}
        for section in ('dependencies','devDependencies','optionalDependencies','peerDependencies'): result.update(m.get(section,{}) or {})
        return result
    old,new=deps(before).get(package),deps(after).get(package)
    outcome='removed' if old is not None and new is None else 'added' if old is None and new is not None else 'range updated' if old is not None and old!=new else 'retained' if old is not None else 'not present'
    bound=None
    if signal_date and to_date and from_date and instant(signal_date)<=instant(from_date) and outcome in ('removed','range updated'):
        bound=max(0,(instant(to_date)-instant(signal_date)).days)
    return {'package':package,'outcome':outcome,'before_range':old,'after_range':new,'resolved_version':None,'right_censored':outcome=='retained','response_days_upper_bound':bound}

def manifest(client,repo,ref,path='package.json'):
    url=f'https://api.github.com/repos/{repo}/contents/{path}?ref={quote(ref,safe="")}'
    data=client.get(url)
    if not isinstance(data,dict) or data.get('encoding')!='base64' or not data.get('content'): raise CollectionError('Manifest unavailable')
    value=json.loads(base64.b64decode(data['content']))
    if not isinstance(value,dict): raise ValueError('Manifest must be an object')
    return value

def collect(config,client):
    observed=datetime.now(timezone.utc).isoformat(); packages=[]; errors=[]
    for name in config['packages']:
        valid_package(name)
        try:
            meta=client.get('https://registry.npmjs.org/'+quote(name,safe=''))
            source_time=client.sources[-1]['observed_at']
            repo=github_repository(meta.get('repository'))
            archived=None; pushed_at=None
            if repo:
                try:
                    repo_meta=client.get('https://api.github.com/repos/'+repo)
                    archived=repo_meta.get('archived'); pushed_at=repo_meta.get('pushed_at')
                except CollectionError as e: errors.append({'package':name,'signal':'repository','error':str(e)})
            advisories=None
            latest=meta.get('dist-tags',{}).get('latest')
            try:
                osv=client.get('https://api.osv.dev/v1/query',{'package':{'ecosystem':'npm','name':name},'version':latest})
                # Incomplete paginated OSV results are unknown, not a complete count.
                advisories=len(osv.get('vulns',[])) if not osv.get('next_page_token') else None
                if osv.get('next_page_token'): errors.append({'package':name,'signal':'advisories','error':'OSV pagination truncated; count unknown'})
            except CollectionError as e: errors.append({'package':name,'signal':'advisories','error':str(e)})
            row=signals(meta,source_time,archived,advisories)
            row.update({'repository':repo,'repository_pushed_at':pushed_at,'downloads':None,'download_period':None,'source':'https://registry.npmjs.org/'+quote(name,safe='')})
            try:
                counts=client.get('https://api.npmjs.org/downloads/point/last-week/'+quote(name,safe=''))
                row.update(downloads=counts.get('downloads'),download_period={'start':counts.get('start'),'end':counts.get('end')})
            except CollectionError as e: errors.append({'package':name,'signal':'downloads','error':str(e)})
            packages.append(row)
        except (CollectionError,ValueError,KeyError) as e: errors.append({'package':name,'signal':'metadata','error':str(e)})
    downstream=[]
    for sample in config['downstream']:
        before=after=None; commits={}
        for point in ('before','after'):
            try:
                commit=client.get(f'https://api.github.com/repos/{sample["repository"]}/commits/{quote(sample[point],safe="")}')
                commits[point]={'sha':commit['sha'],'date':commit['commit']['committer']['date']}
                value=manifest(client,sample['repository'],commit['sha'])
                if point=='before': before=value
                else: after=value
            except (CollectionError,ValueError,KeyError) as e: errors.append({'repository':sample['repository'],'point':point,'error':str(e)})
        for package in sample['packages']:
            row=downstream_change(before,after,package,commits.get('before',{}).get('date'),commits.get('after',{}).get('date'))
            row.update(repository=sample['repository'],before_ref=sample['before'],after_ref=sample['after'],commits=commits,dependency_kind='declared direct range; lockfile not observed',attribution='Manifest difference only; no inferred causal response or replacement')
            downstream.append(row)
    return {'schema_version':1,'project':'Dependency Health Observatory','data_kind':'public API observations','generated_at':observed,'config':config,'packages':packages,'downstream':downstream,'errors':errors,'sources':client.sources,'request_count':client.requests,'limitations':['Convenience sample; not representative of npm.','Release recency alone does not establish abandonment.','Security query covers only latest exact versions, not downstream ranges.','No deprecation onset date: response-time inference is unavailable.','Two pinned manifests detect range changes, not causal migration or precise event timing.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'sample-config.json');p.add_argument('--output',type=Path,default=ROOT/'public/data/observatory.json');p.add_argument('--cache',default=str(ROOT/'.cache'));p.add_argument('--refresh',action='store_true');p.add_argument('--offline',action='store_true');args=p.parse_args()
    config=json.loads(args.config.read_text())
    if len(config['packages'])>10 or len(config['downstream'])>5: p.error('Sample cap: 10 packages / 5 downstream repositories')
    data=collect(config,JsonClient(args.cache,args.refresh,offline=args.offline))
    rows=[{k:r.get(k) for k in ('name','latest_version','days_since_release','maintenance_signal','archived','advisories_for_latest','downloads','observed_at')} for r in data['packages']]
    write_outputs(args.output,rows,data,'package_observations')
    print(json.dumps({'packages':len(rows),'downstream':len(data['downstream']),'errors':data['errors'],'output':str(args.output)},indent=2))
    if not rows: raise SystemExit(1)

if __name__=='__main__': main()
