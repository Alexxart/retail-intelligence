from pathlib import Path
import pandas as pd
import numpy as np
import json
ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'data/processed'; out.mkdir(exist_ok=True)
def load(n): return pd.read_csv(ROOT/'data/raw'/f'{n}.csv')
o=load('orders'); p=load('products'); i=load('order_items'); raw_n=len(i); i=i.drop_duplicates(); missing=int(i.unit_price.isna().sum()); i=i.merge(p[['product_id','list_price']],on='product_id',validate='many_to_one'); i.unit_price=i.unit_price.fillna(i.list_price); i=i.drop(columns='list_price'); i.to_csv(out/'order_items.csv',index=False)
r=load('returns').groupby('item_id').quantity.sum(); f=i.merge(o,on='order_id',validate='many_to_one').merge(p[['product_id','category_id']],on='product_id').merge(load('categories'),on='category_id').merge(load('promotions'),on='promotion_id').merge(load('stores'),on='store_id'); f=f[f.status=='completed'].copy(); f['returned']=f.item_id.map(r).fillna(0).astype(int); f['gross']=f.quantity*f.unit_price; f['net']=np.floor((f.quantity-f.returned)*f.unit_price*(1-f.discount)*100+0.50000001)/100; f['cogs']=((f.quantity-f.returned)*f.unit_cost).round(2); f['profit']=f.net-f.cogs; f['year']=f.day.str[:4]; f['month']=f.day.str[:7]; f.to_csv(out/'sales_fact.csv',index=False)
def summary(g):
 return pd.Series(dict(gross=g.gross.sum(),net=g.net.sum(),profit=g.profit.sum(),cogs=g.cogs.sum(),orders=g.order_id.nunique(),units=g.quantity.sum(),returned=g.returned.sum(),margin=g.profit.sum()/g.net.sum(),aov=g.net.sum()/g.order_id.nunique(),return_rate=g.returned.sum()/g.quantity.sum()))
for name,keys in [('annual',['year']),('monthly',['month']),('categories',['year','category']),('channels',['year','channel']),('discounts',['year','discount']),('sku',['product_id'])]:
 pd.DataFrame([dict(zip(keys, k if isinstance(k, tuple) else (k,)), **summary(g).to_dict()) for k,g in f.groupby(keys[0] if len(keys)==1 else keys)]).to_csv(out/f'{name}.csv',index=False)
customer=f.groupby('customer_id').agg(last=('day','max'),frequency=('order_id','nunique'),monetary=('net','sum')); customer['recency']=(pd.Timestamp('2026-01-01')-pd.to_datetime(customer['last'])).dt.days; customer['segment']=np.where((customer.frequency>=4)&(customer.recency<=90),'active_repeat',np.where(customer.frequency==1,'one_time','other')); customer.to_csv(out/'rfm.csv'); delivery=load('deliveries').merge(o,on='order_id'); delivery['late']=delivery.actual_days>delivery.promised_days; delivery.groupby('channel').agg(cost=('delivery_cost','mean'),late=('late','mean')).to_csv(out/'delivery_summary.csv');
assert i.item_id.is_unique and o.order_id.is_unique and f.returned.le(f.quantity).all() and f.net.ge(0).all() and set(i.order_id)<=set(o.order_id) and set(i.product_id)<=set(p.product_id)
assert np.isclose(f.net.sum()-f.cogs.sum(),f.profit.sum()); qa=dict(raw_rows=raw_n,duplicates=raw_n-len(i),missing_prices_repaired=missing,completed_orders=int(f.order_id.nunique()),repeat_rate=float((customer.frequency>1).mean())); (out/'qa.json').write_text(json.dumps(qa,indent=2)); print(pd.read_csv(out/'annual.csv').to_string(index=False)); print(qa)

import stock_metrics
