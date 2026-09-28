#!/usr/bin/env python3
"""Overall records from KPreps' district standings, for the live week only.

Reads the live week (meta/settings.currentWeek) and whether it's released from Firestore, reads
the nine class pages at kpreps.com/kansas/districts/, and writes every school's overall record into
kprecords.json under that week. Earlier weeks in the file are never touched, and a released week is
left alone (pass --force to fill it anyway), so a week's records stay as they were when it went public.
The site shows these only where no record was typed in the admin panel.
"""
import json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'kprecords.json'
FS = 'https://firestore.googleapis.com/v1/projects/ks-football-poll/databases/(default)/documents'
KEY = 'AIzaSyBTiNraruWtESR_ioYAEM4QaxkqBYY3ZAg'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'}
KP_CLASSES = {'6A': '6A', '5A': '5A', '4A': '4A', '3A': '3A', '2A': '2A', '1A': '1A',
              '8M-I': '8-Man I', '8M-II': '8-Man II', '6M': '6-Man'}

# The site's name -> KPreps' name, where they differ.
ALIASES = {
    'Campus': 'Haysville Campus', 'BV Northwest': 'Blue Valley Northwest', 'BV West': 'Blue Valley West',
    'JC Harmon': 'KC Harmon', 'Seaman': 'Topeka Seaman', 'Eisenhower': 'Goddard-Eisenhower',
    'Highland Park': 'Topeka Highland Park', 'Circle': 'Towanda-Circle', 'Field Kindley': 'Coffeyville',
    'Hayden': 'Topeka Hayden', 'Perry-Lecompton/Bishop Seabury': 'Perry-Lecompton',
    'KC Bishop Ward': 'Bishop Ward', 'Wichita Trinity Academy': 'Wichita Trinity',
    'Remington': 'Whitewater-Remington', 'Plainville/Natoma': 'Plainville', 'Bluestem': 'Leon-Bluestem',
    'Thomas More Prep-Marian': 'Thomas More Prep', 'Jefferson County North': 'Jefferson Co. North',
    'Hutch Trinity': 'Hutchinson Trinity',
    'South Sumner County': 'South Sumner Co.', 'West Elk/Elk Valley': 'West Elk', 'Elkhart/Rolla': 'Elkhart',
    'Rawlins County': 'Atwood-Rawlins Co.', 'Wichita County': 'Leoti-Wichita Co.',
    'Oberlin-Decatur': 'Oberlin-Decatur Co.', 'Rock Hills': 'Mankato-Rock Hills', 'St. John-Hudson': 'St. John',
    'Attica/Argonia': 'Argonia-Attica', 'Madison/Hamilton': 'Madison', 'Greeley County': 'Tribune-Greeley Co.',
    "St. John's/Tipton Catholic": 'Beloit St. Johns-Tipton', 'BV Randolph': 'Blue Valley Randolph',
    'Hutch Central Christian': 'Hutchinson Central Christian', 'Wallace County': 'Sharon Springs-Wallace Co.',
    'Centre': 'Centre-Lost Springs', 'Southern Coffey County': 'Southern Coffey Co.',
}


def get(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read().decode('utf-8', 'replace')
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 + 2 * i)


def fs_doc(path):
    try:
        return json.loads(get(f'{FS}/{urllib.parse.quote(path)}?key={KEY}')).get('fields', {})
    except Exception:
        return {}


def site_classes():
    src = (ROOT / 'index.html').read_text(encoding='utf-8')
    body = re.search(r'const CLASSES = (\{.*?\n  \});', src, re.S).group(1)
    return {m.group(1): re.findall(r'"([^"]+)"', m.group(2)) for m in re.finditer(r'"([^"]+)":\s*\[(.*?)\]', body, re.S)}


def cell_text(s):
    return unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s))).strip()


def kp_records():
    # Some classes list a District record before Overall, so find the Overall column by its header.
    out = {}
    for kp, cls in KP_CLASSES.items():
        html = get(f'https://kpreps.com/kansas/districts/?class={kp}')
        recs = {}
        for table in re.findall(r'<table[^>]*class="display"[^>]*>(.*?)</table>', html, re.S):
            heads = [cell_text(h) for h in re.findall(r'<th[^>]*>(.*?)</th>', table, re.S)]
            if 'Overall' not in heads:
                continue
            col = heads.index('Overall')
            for row in re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.S):
                cells = [cell_text(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]
                if len(cells) > col and re.fullmatch(r'\d+-\d+(?:-\d+)?', cells[col]) and cells[0]:
                    recs[cells[0]] = cells[col]
        if not recs:
            raise SystemExit(f'No records found on the KPreps {kp} page; its layout may have changed.')
        out[cls] = recs
        time.sleep(1)
    return out


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def main():
    force = '--force' in sys.argv
    week = fs_doc('meta/settings').get('currentWeek', {}).get('stringValue')
    if not week:
        raise SystemExit('Could not read the live week from Firestore.')
    released = fs_doc(f'releases/{week}').get('released', {}).get('booleanValue', False)
    if released and not force:
        print(f'{week} is already released; leaving its records as they are.')
        return

    kp = kp_records()
    everywhere = {norm(n): rec for recs in kp.values() for n, rec in recs.items()}
    week_out, missing = {}, []
    for cls, schools in site_classes().items():
        here = {norm(n): rec for n, rec in kp.get(cls, {}).items()}
        got = {}
        for school in schools:
            k = norm(ALIASES.get(school, school))
            rec = here.get(k) or everywhere.get(k)
            if rec:
                got[school] = rec
            else:
                missing.append(f'{school} ({cls})')
        week_out[cls] = got

    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    weeks = data.get('weeks', {})
    if weeks.get(week) == week_out:
        print(f'{week}: no record changes.')
        return
    weeks[week] = week_out
    OUT.write_text(json.dumps({
        'source': 'KPreps district standings, kpreps.com/kansas/districts/',
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'weeks': weeks,
    }, indent=1, ensure_ascii=False) + '\n')
    print(f'{week}: wrote {sum(len(v) for v in week_out.values())} records.')
    if missing:
        print('No KPreps record for: ' + ', '.join(missing))


if __name__ == '__main__':
    main()
