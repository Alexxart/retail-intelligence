from pathlib import Path
import pandas as pd, numpy as np, sqlite3, re, hashlib
import nbformat as nb
from nbclient import NotebookClient
R=Path(__file__).resolve().parents[1]; O=R/'data/processed'; D=R/'data/raw'
# Preserve original builder for legacy queries; this script extends the accepted snapshot.
con=sqlite3.connect(':memory:'); con.execute('PRAGMA foreign_keys=ON'); con.executescript((R/'sql/schema.sql').read_text())
for line in (R/'sql/import.psql').read_text().splitlines():
 t,path=re.match(r"\\copy (\w+) FROM '([^']+)'",line).groups(); pd.read_csv(R/path).to_sql(t,con,if_exists='append',index=False)
con.executescript((R/'sql/view.sql').read_text())
q={22:('Складские KPI по годам', '''WITH s AS (SELECT year,SUM(cogs) cogs FROM sales GROUP BY year), i AS (SELECT substr(month,1,4) year,SUM(stock_unit_days*p.unit_cost*CASE WHEN substr(month,1,4)='2025' THEN 1.045 ELSE 1 END) value_days,SUM(stockout_days) shortage,SUM(unmet_demand) unmet,SUM(sales) units FROM inventory JOIN products p USING(product_id) GROUP BY substr(month,1,4)), a AS (SELECT i.*,s.cogs,CASE WHEN i.year='2024' THEN 366 ELSE 365 END days FROM i JOIN s USING(year)) SELECT year,value_days/days avg_inventory,cogs/(value_days/days) turnover,value_days/cogs dio,1.0*shortage/(days*1800) stockout_rate,1.0*unmet/(units+unmet) unmet_rate FROM a ORDER BY year'''),23:('ABC XYZ по годам', '''WITH months AS (SELECT DISTINCT substr(day,1,7) month FROM calendar), m AS (SELECT product_id,month,SUM(quantity) units,SUM(net) net FROM sales GROUP BY product_id,month), grid AS (SELECT p.product_id,substr(t.month,1,4) year,COALESCE(m.units,0) units,COALESCE(m.net,0) net FROM products p CROSS JOIN months t LEFT JOIN m ON m.product_id=p.product_id AND m.month=t.month), a AS (SELECT year,product_id,SUM(net) net,AVG(1.0*units) mu,AVG(1.0*units*units) m2 FROM grid GROUP BY year,product_id), b AS (SELECT *, (SUM(net) OVER(PARTITION BY year ORDER BY net DESC,product_id ROWS UNBOUNDED PRECEDING)-net)/SUM(net) OVER(PARTITION BY year) prior_share,(m2-mu*mu)/NULLIF(mu*mu,0) cv2 FROM a) SELECT year,product_id,net,CASE WHEN prior_share<0.8 THEN 'A' WHEN prior_share<0.95 THEN 'B' ELSE 'C' END abc,CASE WHEN cv2<=0.0625 THEN 'X' WHEN cv2<=0.25 THEN 'Y' ELSE 'Z' END xyz FROM b ORDER BY year,product_id'''),24:('Когорты по месяцу первой наблюдаемой покупки', '''WITH a AS (SELECT DISTINCT customer_id,month FROM sales), b AS (SELECT customer_id,MIN(month) cohort FROM a GROUP BY customer_id), c AS (SELECT cohort,COUNT(*) cohort_size FROM b GROUP BY cohort) SELECT b.cohort,a.month,COUNT(*) active,c.cohort_size,1.0*COUNT(*)/c.cohort_size retention FROM a JOIN b USING(customer_id) JOIN c ON b.cohort=c.cohort GROUP BY b.cohort,a.month,c.cohort_size ORDER BY b.cohort,a.month'''),25:('Повторные покупки по годам', '''WITH c AS (SELECT year,customer_id,COUNT(DISTINCT order_id) n FROM sales GROUP BY year,customer_id) SELECT year,COUNT(*) buyers,SUM(CASE WHEN n>1 THEN 1 ELSE 0 END) repeat_buyers,AVG(CASE WHEN n>1 THEN 1.0 ELSE 0.0 END) repeat_rate FROM c GROUP BY year ORDER BY year'''),26:('Клиентские сегменты', '''WITH c AS (SELECT customer_id,MAX(day) last_day,COUNT(DISTINCT order_id) frequency,SUM(net) monetary FROM sales GROUP BY customer_id), s AS (SELECT *,CASE WHEN frequency>=4 AND last_day>='2025-10-03' THEN 'active_repeat' WHEN frequency=1 THEN 'one_time' ELSE 'other' END segment FROM c) SELECT segment,COUNT(*) buyers,SUM(monetary) net FROM s GROUP BY segment ORDER BY segment'''),27:('Убыточные SKU по годам', '''SELECT year,product_id,SUM(net) net,SUM(net-cogs) profit FROM sales GROUP BY year,product_id HAVING SUM(net-cogs)<0 ORDER BY year,profit'''),28:('Складской баланс и непрерывность', '''WITH a AS (SELECT *,LAG(stock_end) OVER(PARTITION BY warehouse_id,product_id ORDER BY month) previous_end FROM inventory) SELECT COUNT(*) records,SUM(CASE WHEN stock_start+receipts+emergency_receipts+restocked-sales<>stock_end THEN 1 ELSE 0 END) balance_errors,SUM(CASE WHEN previous_end<>stock_start THEN 1 ELSE 0 END) continuity_errors FROM a'''),29:('Доставка по годам без размножения строк', '''SELECT substr(o.day,1,4) year,o.channel,COUNT(*) orders,SUM(d.delivery_cost) cost,AVG(1.0*d.delivery_cost) cost_per_order,AVG(CASE WHEN actual_days>promised_days THEN 1.0 ELSE 0.0 END) late_rate FROM deliveries d JOIN orders o USING(order_id) WHERE o.status='completed' GROUP BY substr(o.day,1,4),o.channel ORDER BY year,channel''')}
base=(R/'sql/analysis.sql').read_text().split('-- 22.')[0].rstrip(); (R/'sql/analysis.sql').write_text(base+'\n\n'+'\n\n'.join(f'-- {j}. {name}\n{sql};' for j,(name,sql) in q.items()))
for j,(name,sql) in q.items(): pd.read_sql_query(sql,con).to_csv(O/f'sql_{j:02}.csv',index=False)
assert not con.execute('PRAGMA foreign_key_check').fetchall()
# PostgreSQL-specific DDL/view, separate from verified SQLite dialect.
(R/'sql/schema_postgresql.sql').write_text(re.sub(r'\b(day|return_day|month) TEXT',r'\1 DATE',(R/'sql/schema.sql').read_text()))
(R/'sql/view_postgresql.sql').write_text((R/'sql/view.sql').read_text().replace('substr(o.day,','substr(CAST(o.day AS TEXT),'))
(R/'sql/analysis_postgresql.sql').write_text((R/'sql/analysis.sql').read_text().replace('substr(month,','substr(CAST(month AS TEXT),').replace('substr(day,','substr(CAST(day AS TEXT),').replace('substr(o.day,','substr(CAST(o.day AS TEXT),'))
# Notebook cells are independently readable and execute against unchanged source files.
cells=[]
def add(title, prose, code):
 cells.extend([nb.v4.new_markdown_cell('## '+title+'\n'+prose),nb.v4.new_code_cell(code)])
add('01 / Источники и диагностика','Синтетическая сеть, 2024–2025. Hoff — отраслевой референс. Все суммы в рублях без НДС.', '''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from IPython.display import display, Image
R=Path.cwd(); O=R/'data/processed'; D=R/'data/raw'
def read(name): return pd.read_csv(O/f'{name}.csv')
def raw(name): return pd.read_csv(D/f'{name}.csv')
plt.rcParams.update({'figure.dpi':120,'axes.spines.top':False,'axes.spines.right':False,'axes.prop_cycle':plt.cycler(color=['#14243D','#BBA17A','#64748B'])})
pd.DataFrame([(p.name,len(pd.read_csv(p))) for p in sorted(D.glob('*.csv'))],columns=['table','rows'])''')
add('02 / Очистка и связи','Удаляем только полные дубли; пропуски цены восстанавливаем из справочника согласно генератору.', '''i=raw('order_items'); p=raw('products'); o=raw('orders'); r=raw('returns')
print('Дубли:',i.duplicated().sum(),'Пропуски:',i.unit_price.isna().sum())
i=i.drop_duplicates().merge(p[['product_id','list_price']],on='product_id',validate='many_to_one'); i.unit_price=i.unit_price.fillna(i.list_price); i=i.drop(columns='list_price')
assert i.item_id.is_unique and o.order_id.is_unique and r.return_id.is_unique
assert set(i.order_id)<=set(o.order_id) and set(r.item_id)<=set(i.item_id)
assert np.allclose(i.sort_values('item_id').unit_price,read('order_items').sort_values('item_id').unit_price)
f=read('sales_fact'); assert f.item_id.is_unique and f.returned.le(f.quantity).all()
assert np.allclose(f.net-f.cogs,f.profit)
assert np.allclose(f.net,np.floor((f.quantity-f.returned)*f.unit_price*(1-f.discount)*100+0.50000001)/100)
f.head(3)''')
add('03 / Финансовая динамика','Маржа — отношение сумм, заказы — уникальные идентификаторы. Возвраты относятся к когорте продажи.', '''a=f.groupby('year').agg(net=('net','sum'),cogs=('cogs','sum'),profit=('profit','sum'),orders=('order_id','nunique'),units=('quantity','sum'),returned=('returned','sum'))
a['margin']=a.profit/a.net; a['aov']=a.net/a.orders; a['return_rate']=a.returned/a.units
display(a); display(a.pct_change().iloc[-1].rename('YoY'))
m=f.groupby('month')[['net','profit']].sum(); m['margin']=m.profit/m.net
m[['net','profit']].div(1e6).plot(figsize=(10,3),ylabel='млн ₽'); plt.show()
m.margin.mul(100).plot(figsize=(10,3),ylabel='Маржа, %'); plt.show()''')
add('04 / Факторный мост','Цепные подстановки: объём, микс категорий, цена, скидка, себестоимость, возвраты. Взаимодействия зависят от порядка; среднее по 720 порядкам — Шепли.', '''b=read('profit_bridge'); s=read('factor_sensitivity'); assert abs(a.profit.diff().iloc[-1]-b.effect.sum())<.01
display(b); display(s); display(Image(filename=str(R/'images/profit_waterfall.png')))
display(read('return_factor_detail'))''')
add('05 / Скидки и себестоимость','H1: глубокие скидки связаны с меньшей маржой. Сравнение внутри категории и года снижает смешение, но не измеряет эластичность.', '''d=f.groupby(['year','category','discount'])[['net','profit']].sum(); d['margin']=d.profit/d.net
pivot=d.margin.unstack('discount'); display(pivot)
print('Доля групп, где маржа при максимальной скидке ниже нулевой:',(pivot.iloc[:,-1]<pivot.iloc[:,0]).mean())
f['cost_ratio']=f.unit_cost/f.unit_price
f.groupby('year').cost_ratio.mean().to_frame('mean_line_cost_ratio')''')
add('06 / Ассортимент','H2: смещение микса в менее маржинальные категории ухудшает прибыльность. Проверяем знак эффекта микса, а не только рейтинг выручки.', '''c=f.groupby(['year','category'])[['net','profit','quantity','returned']].sum(); c['margin']=c.profit/c.net; c['return_rate']=c.returned/c.quantity
c['unit_share']=c.quantity/c.groupby(level=0).quantity.transform('sum'); display(c)
c.margin.unstack(0).mul(100).plot.bar(figsize=(10,4),ylabel='Маржа, %'); plt.xticks(rotation=20); plt.show()
print('Эффект микса:',b.iloc[1].effect)''')
add('07 / Возвраты','H4: возвраты концентрируются в отдельных категориях. Положительный эффект в мосте означает изменение удельной потерянной прибыли, а не пользу возвратов.', '''f['lost_profit']=f.returned*(f.unit_price*(1-f.discount)-f.unit_cost)
ret=f.groupby(['year','category']).agg(units=('quantity','sum'),returned=('returned','sum'),lost_profit=('lost_profit','sum')); ret['rate']=ret.returned/ret.units; display(ret)
ret.rate.unstack(0).mul(100).plot.bar(figsize=(10,4),ylabel='Возвращено, %'); plt.xticks(rotation=20); plt.show()''')
add('08 / Клиенты','Сегменты по наблюдаемой частоте и давности; это не прогноз CLV. Когорты ограничены окном наблюдения.', '''cust=f.groupby('customer_id').agg(last=('day','max'),frequency=('order_id','nunique'),monetary=('net','sum')); cust['recency']=(pd.Timestamp('2026-01-01')-pd.to_datetime(cust['last'])).dt.days
cust['segment']=np.select([(cust.frequency>=4)&(cust.recency<=90),cust.frequency==1],['active_repeat','one_time'],default='other')
seg=cust.groupby('segment').agg(buyers=('frequency','size'),net=('monetary','sum')); display(seg)
cy=f.groupby(['year','customer_id']).order_id.nunique().rename('n').reset_index(); rep=cy.assign(repeat=cy.n>1).groupby('year').agg(buyers=('n','size'),repeat_buyers=('repeat','sum'),repeat_rate=('repeat','mean')); display(rep)
act=f[['customer_id','month']].drop_duplicates(); act['cohort']=act.groupby('customer_id').month.transform('min'); cohort=act.groupby(['cohort','month']).size().rename('active').reset_index(); cohort['cohort_size']=cohort.groupby('cohort').active.transform('first'); cohort['retention']=cohort.active/cohort.cohort_size
heat=cohort.pivot(index='cohort',columns='month',values='retention'); fig,ax=plt.subplots(figsize=(11,6)); im=ax.imshow(heat,aspect='auto',vmin=0,vmax=1,cmap='Blues'); ax.set_xticks(range(len(heat.columns)),heat.columns,rotation=90); ax.set_yticks(range(len(heat.index)),heat.index); fig.colorbar(im,ax=ax,label='Доля активных'); plt.tight_layout(); plt.show()''')
add('09 / Запасы','H5: сезонный спрос и неоднородность SKU создают риск дефицита и избытка. Остатки условны на продажах; срочное пополнение бесплатно в модели, возвраты пригодны к продаже.', '''inv=raw('inventory').merge(p,on='product_id',validate='many_to_one'); inv['year']=inv.month.str[:4].astype(int); inv['days']=pd.to_datetime(inv.month).dt.days_in_month; inv['value_days']=inv.stock_unit_days*inv.unit_cost*np.where(inv.year==2025,1.045,1)
assert (inv.stock_start+inv.receipts+inv.emergency_receipts+inv.restocked-inv.sales==inv.stock_end).all()
stock=inv.groupby('year').agg(value_days=('value_days','sum'),shortage=('stockout_days','sum'),exposure=('days','sum'),unmet=('unmet_demand','sum'),units=('sales','sum')); stock['avg_inventory']=stock.value_days/pd.Series({2024:366,2025:365}); stock['turnover']=a.cogs/stock.avg_inventory; stock['dio']=stock.value_days/a.cogs; stock['stockout_rate']=stock.shortage/stock.exposure; stock['unmet_rate']=stock.unmet/(stock.units+stock.unmet); display(stock)
stock[['turnover','dio']].plot.bar(subplots=True,figsize=(7,5),legend=False); plt.tight_layout(); plt.show()
monthly=inv.groupby('month')[['sales','stockout_days','unmet_demand']].sum(); display(monthly.corr(method='spearman'))
print('SKU-склад-месяцы с запасом и без продаж:',((inv.stock_end>0)&(inv.sales==0)).sum())
abc=read('abc_xyz'); display(pd.crosstab([abc.year,abc.abc],abc.xyz))''')
add('10 / Каналы и логистика','H3: рост онлайн-доли увеличивает общие расходы доставки. Расходы считаются на заказ, отдельно от валовой прибыли.', '''delivery=raw('deliveries').merge(o,on='order_id',validate='one_to_one'); delivery=delivery[delivery.status=='completed'].copy(); delivery['year']=delivery.day.str[:4].astype(int); delivery['late']=delivery.actual_days>delivery.promised_days
log=delivery.groupby(['year','channel']).agg(orders=('order_id','size'),cost=('delivery_cost','sum'),cost_per_order=('delivery_cost','mean'),late_rate=('late','mean')); display(log)
log.cost.unstack().div(1e6).plot.bar(figsize=(7,3),ylabel='млн ₽'); plt.xticks(rotation=0); plt.show()
print('Доля онлайн:',log.orders.unstack().online/log.orders.groupby(level=0).sum())''')
add('11 / Управленческий парадокс','Оборачиваемость = COGS / средний запас. DIO = дни / оборачиваемость. Рост COGS может одновременно ускорять оборот и снижать маржу. GMROI показывает валовую прибыль на рубль среднего запаса.', '''par=pd.DataFrame({'COGS':a.cogs,'avg_inventory':stock.avg_inventory,'gross_profit':a.profit,'GMROI':a.profit/stock.avg_inventory}); display(par); display(par.pct_change().iloc[-1])
par.GMROI.plot.bar(figsize=(6,3),ylabel='Валовая прибыль / запас'); plt.xticks(rotation=0); plt.show()''')
add('12 / Независимая сверка SQL и Python','Сравниваем ключи и значения, а не только число строк.', '''def compare(left,right,keys,cols):
 x=left.reset_index().merge(right,on=keys,validate='one_to_one',suffixes=('_py','_sql'),how='outer',indicator=True); assert x._merge.eq('both').all()
 for col in cols: assert np.allclose(x[col+'_py'],x[col+'_sql'],rtol=1e-9,atol=.01),col
compare(a,read('sql_01'),['year'],['net','profit','orders'])
compare(stock,read('sql_22'),['year'],['avg_inventory','turnover','dio','stockout_rate','unmet_rate'])
compare(rep,read('sql_25'),['year'],['buyers','repeat_buyers','repeat_rate'])
compare(seg,read('sql_26'),['segment'],['buyers','net'])
compare(cohort,read('sql_24'),['cohort','month'],['active','cohort_size','retention'])
compare(log,read('sql_29'),['year','channel'],['orders','cost','cost_per_order','late_rate'])
z=abc.merge(read('sql_23'),on=['year','product_id'],validate='one_to_one',suffixes=('_py','_sql')); assert len(z)==len(abc)==1200 and z.abc_py.eq(z.abc_sql).all() and z.xyz_py.eq(z.xyz_sql).all()
assert read('sql_28')[['balance_errors','continuity_errors']].eq(0).all().all()
print('8 сверок пройдены')''')
add('13 / Проверка гипотез и решения','Описательная проверка, без формальных p-value: зависимости заданы генератором, наблюдения не являются независимым экспериментом.', '''h=pd.DataFrame([['H1','Поддержана',f'{(pivot.iloc[:,-1]<pivot.iloc[:,0]).mean():.0%} групп: маржа ниже при максимальной скидке','Пилот ограничения скидок; контролировать прибыль и объём'],['H2','Не поддержана',f'Эффект микса {b.iloc[1].effect/1e6:+.2f} млн ₽','Не сокращать категории только по низкой марже'],['H3','Поддержана',f'Расходы доставки +{log.cost.groupby(level=0).sum().pct_change().iloc[-1]:.1%}','Контроль затрат на заказ и SLA'],['H4','Поддержана',f'Максимальная доля возвратов 2025: {ret.loc[2025].rate.max():.2%}','Проверка комплектации и причин возврата'],['H5','Частично поддержана',f'Запас без продаж: {((inv.stock_end>0)&(inv.sales==0)).sum()} SKU-склад-месяцев; дефицит {stock.stockout_rate.iloc[-1]:.3%}','Пилот пополнения по ABC/XYZ; проверить фактический спрос']],columns=['hypothesis','status','evidence','action']); display(h); h.to_csv(O/'hypotheses_stage3.csv',index=False)
par.to_csv(O/'inventory_profit_paradox.csv'); seg.to_csv(O/'customer_segments_stage3.csv'); rep.to_csv(O/'repeat_annual.csv'); cohort.to_csv(O/'cohort_retention.csv',index=False)''')
n=nb.v4.new_notebook(cells=cells); NotebookClient(n,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(R)}}).execute(); nb.write(n,R/'Retail_Analysis.ipynb')
print('Stage3 notebook executed')
