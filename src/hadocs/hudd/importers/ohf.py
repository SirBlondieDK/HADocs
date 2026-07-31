#!/usr/bin/env python3
"""Lossless staging importer for an OHF Device Database JSON export.
It deliberately stores raw records first. Field mapping into HUDD devices is added only
when the preview's actual export/API contract has been inspected and versioned.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path

def records_from(value):
    if isinstance(value, list): return value
    if isinstance(value, dict):
        for key in ('devices','items','results','data'):
            if isinstance(value.get(key), list): return value[key]
        return [value]
    raise ValueError('JSON root must be an object or array')

def main():
    p=argparse.ArgumentParser(); p.add_argument('json_file'); p.add_argument('database'); p.add_argument('--version',default='preview-unknown')
    a=p.parse_args(); data=json.loads(Path(a.json_file).read_text(encoding='utf-8')); rows=records_from(data)
    con=sqlite3.connect(a.database); con.execute('PRAGMA foreign_keys=ON')
    con.execute("INSERT OR IGNORE INTO sources(name,url,version,retrieved_at) VALUES(?,?,?,datetime('now'))",('Open Home Foundation Device Database Preview','https://device-database-preview.openhomefoundation.org',a.version))
    sid=con.execute('SELECT id FROM sources WHERE name=? AND version=?',('Open Home Foundation Device Database Preview',a.version)).fetchone()[0]
    count=0
    for r in rows:
        raw=json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        h=hashlib.sha256(raw.encode()).hexdigest()
        ext=None; name=None
        if isinstance(r,dict):
            ext=next((str(r[k]) for k in ('id','device_id','uuid','slug') if r.get(k) is not None),None)
            name=next((str(r[k]) for k in ('name','product_name','model') if r.get(k) is not None),None)
        before=con.total_changes
        con.execute('INSERT OR IGNORE INTO source_records(source_id,record_type,external_id,raw_name,raw_payload,payload_hash) VALUES(?,?,?,?,?,?)',(sid,'ohf_device_raw',ext,name,raw,h))
        count += con.total_changes-before
    con.commit(); print(f'Staged {count} new OHF records ({len(rows)} examined).')
if __name__=='__main__': main()
