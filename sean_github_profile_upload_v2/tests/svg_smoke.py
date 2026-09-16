from pathlib import Path
import importlib.util,json,base64,io,os,shutil
from playwright.sync_api import sync_playwright
from PIL import Image,ImageChops
r=Path(__file__).resolve().parents[1]
(r/'tests/artifacts').mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('r',r/'scripts/generate_contribution_rhythm.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads((r/'docs/demo-data.js').read_text(encoding='utf-8').split(' = ',1)[1].rstrip(';\n'))
svg=m.svg(d,'dark')
uri='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
still='data:image/svg+xml;base64,'+base64.b64encode(m.svg(d,'dark',still=True).encode()).decode()
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH') or shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
    p=b.new_page(viewport={'width':980,'height':320})
    p.set_content(f'<html><body style="margin:20px;background:#0d1117"><picture><source media="(prefers-reduced-motion: reduce)" srcset="{still}"><img id="s" width="900" src="{uri}"></picture></body></html>')
    p.wait_for_function('document.getElementById("s").complete')
    p.wait_for_timeout(300);a=p.locator('#s').screenshot();p.wait_for_timeout(1800);z=p.locator('#s').screenshot()
    diff=ImageChops.difference(Image.open(io.BytesIO(a)).convert('RGB'),Image.open(io.BytesIO(z)).convert('RGB'))
    assert diff.getbbox() is not None,'SVG did not animate as an img resource'
    p.emulate_media(reduced_motion='reduce');p.wait_for_function('(u)=>document.getElementById("s").currentSrc===u',arg=still);p.wait_for_timeout(200);a=p.locator('#s').screenshot();p.wait_for_timeout(1100);z=p.locator('#s').screenshot()
    diff=ImageChops.difference(Image.open(io.BytesIO(a)).convert('RGB'),Image.open(io.BytesIO(z)).convert('RGB'))
    assert diff.getbbox() is None,'Reduced motion SVG is still moving'
    p.screenshot(path=str(r/'tests/artifacts/readme-svg-demo.png'))
    b.close()
print('SVG in img context: animated frames differ; reduced-motion frames are identical.')
