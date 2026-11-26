from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]; P=R/'data/processed'; f=pd.read_csv(P/'sales_fact.csv'); annual=pd.read_csv(P/'sql_01.csv'); errors=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']); page=b.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1); page.on('pageerror',lambda e:errors.append(str(e))); page.set_content((R/'dashboard.html').read_text()); page.wait_for_function('window.current !== undefined');
 def check(g):
  s=page.evaluate('window.current.s'); assert abs(s['net']-g.net.sum())<.01 and abs(s['profit']-g.profit.sum())<.01 and s['orders']==g.order_id.nunique()
 check(f)
 for y in [2024,2025]:
  page.select_option('#from',f'{y}-01');page.select_option('#to',f'{y}-12');check(f[f.year==y]); s=page.evaluate('window.current.s'); a=annual[annual.year==y].iloc[0];assert abs(s['net']-a.net)<.01 and abs(s['profit']-a.profit)<.01 and s['orders']==a.orders
 page.get_by_text('Сбросить',exact=True).click();page.select_option('#region','Москва');page.select_option('#channel','online');page.select_option('#category','Кухни');check(f[(f.region=='Москва')&(f.channel=='online')&(f.category=='Кухни')]);page.select_option('#from','2025-12');page.select_option('#to','2024-01');assert page.get_by_text('Начало периода позже окончания.').is_visible();page.get_by_text('Сбросить',exact=True).click();check(f)
 for j in range(4):
  page.locator('nav button').nth(j).click();page.screenshot(path=str(R/'images'/f'dashboard_{j+1}.png'),full_page=True);assert page.evaluate('window.current.tab')==j
 assert not errors,errors;b.close()
print('PASS: offline file, four tabs, annual SQL/Python reconciliation, combined filters, invalid period, reset, screenshots; no JS exceptions')
