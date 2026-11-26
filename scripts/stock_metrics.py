from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1]; O=R/'data/processed'; raw=R/'data/raw'
f=pd.read_csv(O/'sales_fact.csv'); inv=pd.read_csv(raw/'inventory.csv').merge(pd.read_csv(raw/'products.csv'),on='product_id').merge(pd.read_csv(raw/'categories.csv'),on='category_id'); inv['year']=inv.month.str[:4].astype(int); inv['days']=pd.to_datetime(inv.month).dt.days_in_month; inv['value_days']=inv.stock_unit_days*inv.unit_cost*np.where(inv.year==2025,1.045,1); inv['stock_value']=inv.stock_end*inv.unit_cost*np.where(inv.year==2025,1.045,1)
# Annual average inventory at standard year cost; COGS net of returns attributed to sale cohort.
for name,keys in [('inventory_summary',['year','category']),('inventory_annual',['year'])]:
 a=inv.groupby(keys).agg(value_days=('value_days','sum'),stockout_days=('stockout_days','sum'),exposure=('days','sum'),sales=('sales','sum'),unmet=('unmet_demand','sum'),emergency=('emergency_receipts','sum')).reset_index(); a=a.merge(f.groupby(keys).cogs.sum().reset_index(),on=keys); a['period_days']=np.where(a.year==2024,366,365); a['avg_inventory']=a.value_days/a.period_days; a['turnover']=a.cogs/a.avg_inventory; a['dio']=a.period_days/a.turnover; a['stockout_rate']=a.stockout_days/a.exposure; a['unmet_rate']=a.unmet/(a.sales+a.unmet); a.to_csv(O/f'{name}.csv',index=False)
# ABC on net revenue; XYZ on monthly gross fulfilled units, including zero months.
rows=[]
for year,g in f.groupby('year'):
 m=g.groupby(['product_id','month']).quantity.sum().unstack(fill_value=0).reindex(index=range(1,601),columns=[f'{year}-{i:02}' for i in range(1,13)],fill_value=0); a=g.groupby('product_id').net.sum().reindex(range(1,601),fill_value=0).rename('net').reset_index().sort_values(['net','product_id'],ascending=[False,True]); a['prior_share']=(a.net.cumsum()-a.net)/a.net.sum(); a['abc']=np.select([a.prior_share<.8,a.prior_share<.95],['A','B'],default='C'); cv=m.std(axis=1,ddof=0)/m.mean(axis=1).replace(0,np.nan); a['cv']=a.product_id.map(cv); a['xyz']=np.select([a.cv<=.25,a.cv<=.5],['X','Y'],default='Z'); a['year']=year; rows.append(a)
pd.concat(rows).to_csv(O/'abc_xyz.csv',index=False)
print(pd.read_csv(O/'inventory_annual.csv').to_string(index=False))
