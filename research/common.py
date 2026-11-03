"""Bounded public JSON transport; credential-free by default, disk cache is local only."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler

ALLOWED_HOSTS={'registry.npmjs.org','api.npmjs.org','api.github.com','raw.githubusercontent.com','api.osv.dev'}
MAX_BYTES=24*1024*1024

class CollectionError(RuntimeError): pass

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old,new=urlparse(req.full_url),urlparse(newurl)
        if new.scheme!='https' or new.hostname not in ALLOWED_HOSTS or new.hostname!=old.hostname:
            raise CollectionError('Cross-host redirect refused')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

class JsonClient:
    def __init__(self, cache='.cache', refresh=False, max_requests=80, offline=False):
        self.cache=Path(cache); self.cache.mkdir(parents=True,exist_ok=True)
        self.refresh=refresh; self.max_requests=max_requests; self.requests=0; self.offline=offline
        self.sources=[]; self.opener=build_opener(SafeRedirect())
    def get(self,url,payload=None):
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in (None,443):
            raise CollectionError('Only approved HTTPS public API hosts are supported')
        # Prevent authenticated/private response caches or publication: token use is deliberately absent.
        body=json.dumps(payload,sort_keys=True).encode() if payload is not None else None
        key=hashlib.sha256(url.encode()+(body or b'')).hexdigest()
        path=self.cache/(key+'.json')
        if path.exists() and not self.refresh:
            cached=json.loads(path.read_text())
            self.sources.append({**cached['provenance'],'cache_hit':True})
            return cached['data']
        if self.offline: raise CollectionError('Offline cache miss')
        headers={'User-Agent':'research-portfolio/1.0 (bounded public study)', 'Accept':'application/json'}
        if parsed.hostname=='api.github.com': headers['X-GitHub-Api-Version']='2022-11-28'
        if body: headers['Content-Type']='application/json'
        for attempt in range(3):
            if self.requests>=self.max_requests: raise CollectionError('Request budget exhausted')
            self.requests+=1
            try:
                with self.opener.open(Request(url,data=body,headers=headers),timeout=15) as response:
                    raw=response.read(MAX_BYTES+1)
                    if len(raw)>MAX_BYTES: raise CollectionError('Response exceeds size limit')
                    data=json.loads(raw)
                    meta={'url':url,'observed_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest(),'status':response.status,'request_body':payload,'etag':response.headers.get('ETag')}
                    path.write_text(json.dumps({'data':data,'provenance':meta}))
                    self.sources.append({**meta,'cache_hit':False})
                    return data
            except HTTPError as error:
                if error.code not in (429,500,502,503,504):
                    raise CollectionError(f'HTTP {error.code} at {parsed.hostname}; unavailable, not negative evidence') from None
                delay=float(error.headers.get('Retry-After','0')) if str(error.headers.get('Retry-After','')).isdigit() else 2**attempt
                if delay>10: raise CollectionError('Rate limit requires a later retry') from None
                if attempt==2: raise CollectionError(f'HTTP {error.code} after bounded retries') from None
                time.sleep(max(delay,2**attempt))
            except (URLError,TimeoutError) as error:
                if attempt==2: raise CollectionError('Transport unavailable after bounded retries') from None
                time.sleep(2**attempt)
        raise CollectionError('Request failed')
    def pages(self,url,max_pages=2,per_page=100):
        rows=[]
        for page in range(1,max_pages+1):
            separator='&' if '?' in url else '?'
            data=self.get(f'{url}{separator}per_page={per_page}&page={page}')
            if not isinstance(data,list): raise CollectionError('Expected a JSON array')
            rows.extend(data)
            if len(data)<per_page: return rows,True
        return rows,False

def instant(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None: raise ValueError('Timezone required')
    return result

def csv_cell(value):
    text='' if value is None else str(value)
    return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) else text

def write_outputs(output, rows, dataset, table):
    import csv,sqlite3
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(dataset,indent=2)+'\n')
    if rows:
        with output.with_suffix('.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader()
            writer.writerows({k:csv_cell(v) for k,v in row.items()} for row in rows)
    if not re.fullmatch(r'[a-z_]+',table): raise ValueError('Invalid table')
    with sqlite3.connect(output.with_suffix('.sqlite')) as db:
        db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, observation TEXT NOT NULL)')
        for index,row in enumerate(rows): db.execute(f'INSERT OR REPLACE INTO {table} VALUES (?,?)',(dataset['generated_at']+':'+str(index),json.dumps(row)))
