"""Optional browser smoke test. Requires playwright and a Chromium installation.
Uses in-memory rendering, not an HTTP deployment. Test data is intentionally synthetic.
"""
from pathlib import Path
import os, shutil, sys, json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from build_preview import assemble
out=root/'tests/artifacts';out.mkdir(parents=True,exist_ok=True)
def fixture_html():
    data={"schemaVersion":1,"username":"takagibit18","status":"unavailable",
          "period":{"from":"2025-09-17","to":"2026-09-16"},"fetchedAt":None,
          "timezone":"UTC","totalContributions":None,"days":[],"source":{"note":"Unavailable test fixture."}}
    return assemble().replace((root/'docs/data.js').read_text(encoding='utf-8'),
                              'window.PROFILE_DATA = '+json.dumps(data)+';')
report=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get('CHROME_PATH') or shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1360,'height':1450},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(fixture_html());page.wait_for_function("document.body.dataset.ready==='true'")
    assert page.locator('.day-cell').count()==365
    assert page.locator('#totalValue').inner_text()=='—'
    assert page.locator('.day-cell:disabled').count()==365
    report.append('Unavailable data is shown as unknown, not zero; 365 disabled date cells.')
    page.screenshot(path=str(out/'production-waiting.png'),full_page=True)
    page.locator('#demoButton').click();page.wait_for_timeout(1700)
    assert page.locator('#dataBadge').inner_text()=='DEMO DATA'
    assert 'not Sean' in page.locator('#dataNotice').inner_text()
    assert page.locator('.day-cell:disabled').count()==0
    report.append('Demo mode explicitly labeled and isolated from real-data view.')
    target=page.locator('.day-cell[data-date="2026-09-08"]')
    expected=page.evaluate("window.PROFILE_DEMO.days.find(d=>d.date==='2026-09-08').count")
    target.hover();page.wait_for_timeout(100)
    assert page.locator('#tooltip').is_visible()
    assert str(expected) in page.locator('#tooltipCount').inner_text()
    report.append('Hover tooltip shows the selected date and exact fixture count.')
    page.screenshot(path=str(out/'desktop.png'))
    target.click();page.mouse.move(10,10)
    assert 'PINNED' in page.locator('#detailDate').inner_text()
    assert page.locator('#clearButton').is_visible()
    page.keyboard.press('Escape');assert not page.locator('#clearButton').is_visible()
    report.append('Pin, persistent detail panel, and Escape clear work.')
    target.focus();page.keyboard.press('ArrowLeft')
    assert page.locator(':focus').get_attribute('data-date')=='2026-09-01'
    page.keyboard.press('ArrowUp');assert page.locator(':focus').get_attribute('data-date')=='2026-08-31'
    page.keyboard.press('End');assert page.locator(':focus').get_attribute('data-date')=='2026-09-16'
    report.append('Roving keyboard navigation, previous week/day, and End are correct.')
    page.locator('#motionButton').click();assert 'is-paused' in page.locator('#dayGrid').get_attribute('class')
    page.locator('#replayButton').click();assert 'is-paused' not in page.locator('#dayGrid').get_attribute('class')
    report.append('Pause/resume and replay controls work.')
    page.locator('#themeButton').click();assert page.locator('html').get_attribute('data-theme')=='light'
    page.screenshot(path=str(out/'desktop-light.png'),full_page=True)
    report.append('Light theme renders and switches.')
    page.emulate_media(reduced_motion='reduce');page.wait_for_function("document.getElementById('motionButton').disabled");assert page.locator('#motionButton').is_disabled()
    assert page.locator('#replayButton').is_disabled()
    styles=page.locator('.day-cell.is-latest').evaluate("el=>getComputedStyle(el,'::before').animationName")
    assert styles=='none',styles
    report.append('Reduced-motion disables animations and replay.')
    page.locator('#demoButton').click();assert page.locator('#totalValue').inner_text()=='—'
    report.append('Leaving demo restores unavailable production state without fake numbers.')
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
    mobile.on('pageerror',lambda e:errors.append(str(e)))
    mobile.set_content(fixture_html());mobile.wait_for_function("document.body.dataset.ready==='true'")
    mobile.locator('#demoButton').tap();mobile.wait_for_timeout(1000)
    mobile.locator('.day-cell[data-date="2026-09-10"]').tap();
    assert 'PINNED' in mobile.locator('#detailDate').inner_text()
    assert 'Swipe' in mobile.locator('#interactionHint').inner_text()
    assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
    mobile.evaluate('window.scrollTo(0,0)')
    mobile.screenshot(path=str(out/'mobile.png'),full_page=True)
    report.append('390px mobile: tap-to-pin, readable cells, internal horizontal scroll, no body overflow.')
    assert not errors,errors
    report.append('No browser page errors in tested desktop and mobile states.')
    browser.close()
(out/'browser-report.json').write_text(json.dumps({'checks':report,'pageErrors':errors},indent=2))
print('\n'.join(report))
