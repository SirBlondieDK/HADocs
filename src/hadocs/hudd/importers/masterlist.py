#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re, sqlite3, unicodedata
from pathlib import Path

SUPPORT_DESCRIPTIONS = {
 'HA-CORE':'Officiel integration inkluderet i Home Assistant Core.',
 'WWHA':'Works with Home Assistant-certificering; verificér præcis model.',
 'STANDARD':'Understøttes gennem åben eller industristandardiseret protokol.',
 'UPSTREAM':'Autoritativt eksternt projekt med Home Assistant-relevans.',
 'CUSTOM':'Typisk HACS/custom integration; ikke officiel Core-support.',
 'TUYA':'Tuya/Smart Life-baseret eller ofte solgt med Tuya-platform.',
 'OEM':'White-label/OEM; samme brand kan bruge flere platforme.',
 'GROUP':'Koncern eller moderbrand.',
 'SUBBRAND':'Underbrand, produktbrand eller regionalt brand.',
 'LEGACY':'Ældre, udfaset eller begrænset integrationsvej.',
 'CHECK':'Skal verificeres på modelniveau.'
}
PROTOCOLS = ['Matter','Thread','Zigbee','Z-Wave','Bluetooth','Wi-Fi','Ethernet','MQTT','HomeKit Device','Modbus','ONVIF','RTSP','REST','HTTP API','ESPHome','Tasmota']

def norm(s:str)->str:
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')

def clean_connection(v:str)->str:
    v=v.strip().upper().replace(' ','_')
    allowed={'LOKAL','CLOUD','BEGGE','STANDARD','VARIERER','UKENDT','LOKAL/BEGGE','CLOUD/BEGGE'}
    return v if v in allowed else v[:80]

def parse(path:Path):
    lines=path.read_text(encoding='utf-8').splitlines()
    category=None; records=[]; i=0
    while i < len(lines):
        line=lines[i].strip()
        mcat=re.match(r'^(\d+)\.\s+(.+)$',line)
        if mcat:
            category=(mcat.group(1),mcat.group(2).strip())
            i+=1; continue
        if line.startswith('Support:') or line.startswith('Forbindelse:'):
            # Find nearest meaningful heading above.
            j=i-1
            while j>=0 and (not lines[j].strip() or lines[j].startswith('=') or lines[j].lstrip().startswith('-')):
                j-=1
            name=lines[j].strip() if j>=0 else 'Ukendt'
            support=[]; connection='UKENDT'; notes=[]; bullets=[]
            start=j
            k=i
            while k < len(lines):
                cur=lines[k].strip()
                if k>i and (cur.startswith('Support:') or (cur.startswith('Forbindelse:') and connection!='UKENDT')):
                    break
                if cur.startswith('Support:'):
                    support=re.findall(r'\[([^\]]+)\]',cur)
                elif cur.startswith('Forbindelse:'):
                    connection=clean_connection(cur.split(':',1)[1])
                elif cur.startswith('Noter:'):
                    notes.append(cur.split(':',1)[1].strip())
                elif notes and cur and not cur.startswith('='):
                    # continuation until blank; avoid swallowing next record heading
                    if k+1<len(lines) and lines[k+1].strip().startswith(('Support:','Forbindelse:')):
                        pass
                    elif not re.match(r'^\d+\.\s+',cur): notes.append(cur)
                k+=1
                if k<len(lines) and not lines[k].strip() and (support or connection!='UKENDT'):
                    break
            raw='\n'.join(lines[start:k]).strip()
            records.append({'name':name,'support':support,'connection':connection,'notes':' '.join(notes).strip(),'category':category,'raw':raw})
            i=max(k,i+1); continue
        i+=1
    # dedupe exact names, preserving richest record
    merged={}
    for r in records:
        key=norm(r['name'])
        if not key or r['name'].startswith(('FORMÅL','FORBINDELSESTYPE','SUPPORTKODER')): continue
        old=merged.get(key)
        if not old or len(r['raw'])>len(old['raw']): merged[key]=r
    return list(merged.values())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('database'); ap.add_argument('--schema',default=str(Path(__file__).with_name('schema.sql')))
    a=ap.parse_args(); db=Path(a.database)
    con=sqlite3.connect(db); con.executescript(Path(a.schema).read_text())
    con.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version','1.0.0')")
    con.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('database_name','HUDD Core')")
    cur=con.execute("INSERT OR IGNORE INTO sources(name,version,retrieved_at) VALUES(?,?,datetime('now'))",('Home Assistant producent/brand masterliste','1.1'))
    source_id=con.execute("SELECT id FROM sources WHERE name=? AND version=?",('Home Assistant producent/brand masterliste','1.1')).fetchone()[0]
    for code,desc in SUPPORT_DESCRIPTIONS.items(): con.execute('INSERT OR IGNORE INTO support_codes(code,label,description) VALUES(?,?,?)',(code,code,desc))
    for p in PROTOCOLS: con.execute('INSERT OR IGNORE INTO protocols(slug,name) VALUES(?,?)',(norm(p),p))
    records=parse(Path(a.input))
    cats={}
    for r in records:
        if r['category']:
            code,name=r['category']; con.execute('INSERT OR IGNORE INTO categories(code,name) VALUES(?,?)',(code,name)); cats[code]=con.execute('SELECT id FROM categories WHERE code=?',(code,)).fetchone()[0]
    for n,r in enumerate(records,1):
        nname=norm(r['name']); etype='group' if any(x in r['support'] for x in ('GROUP',)) or 'group' in r['name'].lower() else 'brand'
        cat_id=cats.get(r['category'][0]) if r['category'] else None
        con.execute('''INSERT INTO organizations(hudd_id,canonical_name,normalized_name,entity_type,category_id,connection_class,notes,review_status)
          VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(normalized_name) DO UPDATE SET category_id=excluded.category_id,connection_class=excluded.connection_class,notes=excluded.notes''',
          (f'HUDD-ORG-{n:06d}',r['name'],nname,etype,cat_id,r['connection'],r['notes'],'seed'))
        oid=con.execute('SELECT id FROM organizations WHERE normalized_name=?',(nname,)).fetchone()[0]
        for rawcode in r['support']:
            base=rawcode.split('-',1)[0] if rawcode.startswith('WWHA-') else rawcode
            qualifier=None if base==rawcode else rawcode[len(base)+1:]
            if base not in SUPPORT_DESCRIPTIONS:
                con.execute('INSERT OR IGNORE INTO support_codes(code,label,description) VALUES(?,?,?)',(base,base,'Importeret supportkode; kræver gennemgang.'))
            sid=con.execute('SELECT id FROM support_codes WHERE code=?',(base,)).fetchone()[0]
            con.execute('INSERT OR IGNORE INTO organization_support(organization_id,support_code_id,qualifier,source_id) VALUES(?,?,?,?)',(oid,sid,qualifier,source_id))
        h=hashlib.sha256(r['raw'].encode()).hexdigest()
        con.execute('INSERT OR IGNORE INTO source_records(source_id,record_type,raw_name,raw_payload,payload_hash) VALUES(?,?,?,?,?)',(source_id,'organization_seed',r['name'],r['raw'],h))
    con.commit()
    print(f'Imported {len(records)} organization seed records into {db}')
    for row in con.execute("SELECT 'organizations',count(*) FROM organizations UNION ALL SELECT 'categories',count(*) FROM categories UNION ALL SELECT 'support links',count(*) FROM organization_support UNION ALL SELECT 'source records',count(*) FROM source_records"):
        print(f'{row[0]}: {row[1]}')
if __name__=='__main__': main()
