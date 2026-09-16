#!/usr/bin/env python3
"""Bundle the static activity page into one self-contained HTML file.

python scripts/build_preview.py --demo --output profile-preview.html
No network or Node installation is required. Demo values remain prominently labeled.
"""
from pathlib import Path
import argparse
import base64
ROOT=Path(__file__).resolve().parents[1]

def assemble(start_demo=False):
    p=ROOT/'docs'
    s=(p/'index.html').read_text(encoding='utf-8')
    css=(p/'style.css').read_text(encoding='utf-8')
    data=base64.b64encode((p/'assets/night-city.jpg').read_bytes()).decode('ascii')
    css=css.replace("url('assets/night-city.jpg')",f"url('data:image/jpeg;base64,{data}')")
    s=s.replace('<link rel="stylesheet" href="style.css">',f'<style>{css}</style>')
    for name in ['data.js','demo-data.js','app.js']:
        s=s.replace(f'<script src="{name}"></script>','<script>\n'+(p/name).read_text(encoding='utf-8')+'\n</script>')
    if start_demo:
        s=s.replace('</body>', '<script>document.getElementById("demoButton").click();</script>\n</body>')
    return s

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('profile-preview.html'))
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(assemble(args.demo),encoding='utf-8')
    print(f'Wrote {args.output} ({"explicit demo" if args.demo else "production snapshot"})')
