from pathlib import Path
import pandas as pd, json, numpy as np
R=Path(__file__).resolve().parents[1]; P=R/'data/processed'; D=R/'data/raw'
f=pd.read_csv(P/'sales_fact.csv'); f['list']=f.quantity*f.unit_price; f['disc']=f['list']*f.discount; f['cost']=f.quantity*f.unit_cost; f['retprofit']=f.returned*(f.unit_price*(1-f.discount)-f.unit_cost)
cols=['month','region','channel','category','product_id','order_id','customer_id','day','discount','quantity','returned','net','profit','cogs','list','disc','cost','retprofit']
i=pd.read_csv(D/'inventory.csv').merge(pd.read_csv(D/'products.csv'),on='product_id').merge(pd.read_csv(D/'categories.csv'),on='category_id').merge(pd.read_csv(D/'warehouses.csv'),on='warehouse_id'); i['month']=i.month.str[:7]; i['days']=pd.to_datetime(i.month).dt.days_in_month; i['value_days']=i.stock_unit_days*i.unit_cost*np.where(i.month.str[:4]=='2025',1.045,1); i['value']=i.stock_end*i.unit_cost*np.where(i.month.str[:4]=='2025',1.045,1)
# Warehouse region is not store region; inventory uses network totals or category only.
a=i.groupby(['month','category'])[['days','value_days','value','stockout_days','unmet_demand','sales','emergency_receipts']].sum().reset_index()
l=pd.read_csv(D/'deliveries.csv').merge(pd.read_csv(D/'orders.csv'),on='order_id').merge(pd.read_csv(D/'stores.csv'),on='store_id'); l=l[l.status=='completed'].copy(); l['month']=l.day.str[:7]; l['late']=(l.actual_days>l.promised_days).astype(int); l['n']=1;l=l.groupby(['month','region','channel'])[['delivery_cost','late','n']].sum().reset_index()
def pack(df): return {'columns':list(df.columns),'rows':df.astype(object).where(pd.notna(df),None).values.tolist()}
data={'sales':pack(f[cols]),'stock':pack(a),'logistics':pack(l),'abc':pack(pd.read_csv(P/'abc_xyz.csv').merge(pd.read_csv(D/'products.csv'),on='product_id').merge(pd.read_csv(D/'categories.csv'),on='category_id')[['year','category','abc','xyz']]),'bridge':pack(pd.read_csv(P/'profit_bridge.csv')),'cohort':pack(pd.read_csv(P/'cohort_retention.csv'))}
html=(R/'docs/dashboard_template.html').read_text(); (R/'dashboard.html').write_text(html.replace('/*DATA*/',json.dumps(data,ensure_ascii=False,separators=(',',':'))),encoding='utf-8')
