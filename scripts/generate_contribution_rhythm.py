#!/usr/bin/env python3
"""Fetch one honest GitHub snapshot; generate README SVGs and an offline-readable site.

GH_TOKEN=... python scripts/generate_contribution_rhythm.py --user takagibit18
python scripts/generate_contribution_rhythm.py --render-existing
Only Python's standard library is required. No token is written into any output.
"""
from __future__ import annotations
import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LEVELS = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2,
          'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}
PALETTES = {
    'dark': dict(bg='#11161c', ink='#e8ece8', muted='#9da9b1', line='#2d363d',
                 cells=['#232c30', '#394e45', '#58755c', '#81966d', '#b8c99a']),
    'light': dict(bg='#f7f8f4', ink='#202b28', muted='#586862', line='#d5ddd4',
                  cells=['#e5e9e1', '#c1d0b1', '#99b586', '#6f925e', '#426337'])}
QUERY = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}'''


def day(value: str) -> dt.date:
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Expected a date in YYYY-MM-DD format')
    return dt.date.fromisoformat(value)


def validate(data: dict, *, allow_demo: bool = False) -> dict:
    if data.get('schemaVersion') != 1:
        raise ValueError('Unsupported snapshot schema')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', data.get('username', '')):
        raise ValueError('Invalid GitHub username')
    state = data.get('status')
    if state not in ('ready', 'unavailable', 'demo'):
        raise ValueError('Invalid data state')
    if state == 'demo' and not allow_demo:
        raise ValueError('Refusing to publish demonstration data')
    first, last = day(data['period']['from']), day(data['period']['to'])
    if not 1 <= (last-first).days+1 <= 366:
        raise ValueError('Invalid snapshot window')
    rows = data.get('days')
    if not isinstance(rows, list):
        raise ValueError('Days must be an array')
    if state == 'unavailable':
        if rows or data.get('totalContributions') is not None:
            raise ValueError('Unavailable data must not imply zero or estimated activity')
        return data
    if len(rows) != (last-first).days+1:
        raise ValueError('Incomplete date coverage; do not fill missing days with zeros')
    for i, row in enumerate(rows):
        if day(row['date']) != first+dt.timedelta(days=i):
            raise ValueError('Dates must be unique, sorted, and contiguous')
        count, level = row.get('count'), row.get('level')
        if type(count) is not int or count < 0 or type(level) is not int or not 0 <= level <= 4:
            raise ValueError('Invalid contribution count or level')
        if (count == 0) != (level == 0):
            raise ValueError('Zero contributions and NONE level must agree')
    if sum(r['count'] for r in rows) != data.get('totalContributions'):
        raise ValueError('Aggregate does not reconcile to daily counts')
    return data


def normalize(payload: dict, user: str, start: dt.date, end: dt.date,
              fetched_at: str) -> dict:
    if payload.get('errors'):
        raise ValueError('GitHub GraphQL returned errors; previous snapshot is preserved')
    u = payload.get('data', {}).get('user')
    if not u:
        raise ValueError('GitHub user data is missing')
    cal = u['contributionsCollection']['contributionCalendar']
    rows = []
    for week in cal['weeks']:
        for item in week['contributionDays']:
            d = day(item['date'])
            if start <= d <= end:
                rows.append({'date': item['date'], 'count': item['contributionCount'],
                             'level': LEVELS[item['contributionLevel']]})
    rows.sort(key=lambda r: r['date'])
    return validate({'schemaVersion': 1, 'username': user, 'status': 'ready',
        'period': {'from': start.isoformat(), 'to': end.isoformat()},
        'fetchedAt': fetched_at, 'timezone': 'UTC',
        'totalContributions': cal['totalContributions'], 'days': rows,
        'source': {'kind': 'github-graphql', 'url': f'https://github.com/{user}',
        'note': 'Contribution calendar visible to the workflow token. Not a commit-only count. '
                'The final day may be partial. May differ from the owner-signed-in view.'}})


def fetch(user: str, token: str) -> dict:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    end, start = now.date(), now.date()-dt.timedelta(days=364)
    stamp = now.isoformat().replace('+00:00', 'Z')
    body = json.dumps({'query': QUERY, 'variables': {'login': user,
        'from': start.isoformat()+'T00:00:00Z', 'to': stamp}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'Accept': 'application/vnd.github+json', 'User-Agent': 'sean-profile-rhythm'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                payload = json.load(response)
            return normalize(payload, user, start, end, stamp)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f'GitHub request failed (HTTP {exc.code}); prior data kept') from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError('GitHub network request failed; prior data kept') from None
        time.sleep(2**attempt)
    raise RuntimeError('No GitHub response')


def grid_position(date: str, first: str) -> tuple[int, int]:
    d, f = day(date), day(first)
    monday = f-dt.timedelta(days=f.weekday())
    return (d-monday).days//7, d.weekday()


def svg(data: dict, theme: str, mobile: bool = False, still: bool = False) -> str:
    validate(data, allow_demo=True)
    p = PALETTES[theme]
    first, last = day(data['period']['from']), day(data['period']['to'])
    monday = first-dt.timedelta(days=first.weekday())
    count_weeks = (last-monday).days//7+1
    width = 430 if mobile else 900
    sections = [(0, min(27, count_weeks)), (27, count_weeks)] if mobile else [(0, count_weeks)]
    sections = [s for s in sections if s[0] < s[1]]
    height = 82+len(sections)*147+31 if mobile else 236
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">',
           '<title id="t">Contribution rhythm</title>',
           '<desc id="d">'+html.escape(('DEMO DATA. ' if data['status']=='demo' else '')+
           (f"{data['totalContributions']} contributions, " if data['status']!='unavailable' else 'Awaiting first sync. No contribution counts loaded. ')+
           f"{first.isoformat()} to {last.isoformat()}. The animation does not change the counts.")+'</desc>',
           f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="10" fill="{p["bg"]}" stroke="{p["line"]}"/>',
           f'<style>text{{font-family:Arial,Helvetica,sans-serif;fill:{p["muted"]};font-size:13px}}',
           '.fx{pointer-events:none}.trace{opacity:0;animation:trace .9s ease-out both}.pulse{animation:pulse 5s ease-in-out infinite}',
           '@keyframes trace{0%,100%{opacity:0}40%{opacity:.8}}@keyframes pulse{0%,100%{opacity:.2}50%{opacity:.95}}',
           '@media(prefers-reduced-motion:reduce){.fx{display:none!important}}',
           ('.fx{display:none}' if still else ''), '</style>']
    total = 'Awaiting first sync' if data['status']=='unavailable' else f'{data["totalContributions"]:,} contributions'
    if data['status'] == 'demo': total = 'DEMO DATA · '+total
    out += [f'<text x="22" y="30" style="font-size:16px;font-weight:600;fill:{p["ink"]}">{html.escape(total)}</text>',
            f'<text x="{22 if mobile else width-22}" y="{51 if mobile else 30}" text-anchor="{ "start" if mobile else "end"}">{first.isoformat()} — {last.isoformat()}</text>']
    mapping = {row['date']: row for row in data['days']}
    positives = [row['date'] for row in data['days'] if row['count']>0]
    latest = positives[-1] if positives else None
    for section, (left, right) in enumerate(sections):
        x0, top = 36, (86+section*147 if mobile else 75)
        step = min(16, (width-x0-18)/(right-left))
        cell = step-3
        for row, label in [(0,'M'),(2,'W'),(4,'F')]:
            out.append(f'<text x="17" y="{top+row*16+cell-1}">{label}</text>')
        previous_month, previous_x = None, -100
        for col in range(left, right):
            dates = [monday+dt.timedelta(days=col*7+r) for r in range(7)]
            actual = [d for d in dates if first <= d <= last]
            if not actual: continue
            month = actual[0].strftime('%b')
            x = x0+(col-left)*step
            if month != previous_month and x-previous_x>=33 and x<width-36:
                out.append(f'<text x="{x:.2f}" y="{top-12}">{month}</text>')
                previous_x = x
            previous_month = month
            for row, d in enumerate(dates):
                if not first <= d <= last: continue
                y=top+row*16; item=mapping.get(d.isoformat())
                fill=p['cells'][item['level']] if item else p['cells'][0]
                opacity='1' if item else '.35'
                out.append(f'<rect data-date="{d.isoformat()}" x="{x:.2f}" y="{y}" width="{cell:.2f}" height="{cell:.2f}" rx="2.5" fill="{fill}" opacity="{opacity}"/>')
                if item and item['count']>0:
                    out.append(f'<rect class="fx trace" x="{x:.2f}" y="{y}" width="{cell:.2f}" height="{cell:.2f}" rx="2.5" fill="none" stroke="{p["ink"]}" style="animation-delay:{col*.018:.3f}s"/>')
                if d.isoformat()==latest:
                    out.append(f'<rect class="fx pulse" x="{x-1:.2f}" y="{y-1}" width="{cell+2:.2f}" height="{cell+2:.2f}" rx="3" fill="none" stroke="{p["ink"]}" stroke-width="1.2"/>')
    bottom=height-17
    note = 'No data loaded · run the update workflow' if data['status']=='unavailable' else 'Quiet work, consistently.'
    out.append(f'<text x="22" y="{bottom}" style="font-size:12px">{note}</text>')
    if not mobile:
        lx=width-170
        out.append(f'<text x="{lx-34}" y="{bottom}">Less</text>')
        for i,color in enumerate(p['cells']):
            out.append(f'<rect x="{lx+i*18}" y="{bottom-11}" width="12" height="12" rx="2.5" fill="{color}"/>')
        out.append(f'<text x="{lx+98}" y="{bottom}">More</text>')
    out.append('</svg>')
    return ''.join(out)


def safe_js(data: dict) -> str:
    # Avoid </script>, Unicode line separators and raw HTML if used in a standalone preview.
    text=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    return 'window.PROFILE_DATA = '+text.replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')+';\n'


def publish(data: dict, root: Path = ROOT) -> None:
    validate(data)  # No demo snapshots may be published by the production path.
    outputs = {root/'docs/contributions.json': json.dumps(data,indent=2,ensure_ascii=False)+'\n',
               root/'docs/data.js': safe_js(data)}
    for theme in PALETTES:
        for mobile in (False,True):
            suffix='-mobile' if mobile else ''
            outputs[root/f'assets/contribution-rhythm-{theme}{suffix}.svg']=svg(data,theme,mobile)
            outputs[root/f'assets/contribution-rhythm-{theme}{suffix}-still.svg']=svg(data,theme,mobile,still=True)
        outputs[root/f'docs/assets/contribution-rhythm-{theme}.svg']=svg(data,theme,still=True)
    # Prepare all outputs before replacing any. A failed fetch/validation never changes a snapshot.
    staged=[]
    try:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
                f.write(content); staged.append((Path(f.name),path))
        for temp,path in staged: temp.replace(path)
    finally:
        for temp,_ in staged: temp.unlink(missing_ok=True)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user',default='takagibit18')
    parser.add_argument('--render-existing',action='store_true')
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}',args.user):
        parser.error('Invalid username')
    if args.render_existing:
        data=json.loads((ROOT/'docs/contributions.json').read_text(encoding='utf-8'))
    else:
        token=os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
        if not token: parser.error('Set GH_TOKEN or GITHUB_TOKEN, or use --render-existing')
        data=fetch(args.user,token)
    publish(data)
    print(f'Wrote {data["status"]} snapshot and SVGs. No credentials were included.')

if __name__=='__main__':
    main()
