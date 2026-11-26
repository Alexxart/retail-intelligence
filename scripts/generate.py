from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; raw=ROOT/'data/raw'; raw.mkdir(parents=True,exist_ok=True)
r=np.random.default_rng(42)
def save(name,df): df.to_csv(raw/f'{name}.csv',index=False); return df
cats=save('categories',pd.DataFrame({'category_id':range(1,7),'category':['Диваны','Кровати','Шкафы','Кухни','Текстиль','Освещение']}))
p=600; c=np.repeat(np.arange(1,7),100); price=np.round(np.array([45000,28000,35000,65000,2200,6500])[c-1]*r.lognormal(0,.35,p),2); cost=np.round(price*np.array([.59,.57,.60,.67,.43,.48])[c-1],2)
products=save('products',pd.DataFrame(dict(product_id=np.arange(1,p+1),category_id=c,list_price=price,unit_cost=cost)))
customers=save('customers',pd.DataFrame(dict(customer_id=np.arange(1,18001),loyalty=r.choice(['standard','plus'],18000,p=[.7,.3]))))
stores=save('stores',pd.DataFrame(dict(store_id=range(1,7),region=['Москва','Москва','Казань','Казань','Екатеринбург','Екатеринбург'])))
wh=save('warehouses',pd.DataFrame(dict(warehouse_id=[1,2,3],region=['Москва','Казань','Екатеринбург'])))
calendar=save('calendar',pd.DataFrame({'day':pd.date_range('2024-01-01','2025-12-31').strftime('%Y-%m-%d')}))
channels=save('marketing_channels',pd.DataFrame({'marketing_id':[1,2,3,4],'source':['organic','paid','crm','direct']}))
promos=save('promotions',pd.DataFrame({'promotion_id':[1,2,3,4],'discount':[0,.10,.20,.30]}))
n=72000; days=pd.to_datetime(calendar.day); weights=np.where(days.dt.year==2025,1.18,1)*np.where(days.dt.month.isin([11,12]),1.45,1); d=pd.Series(r.choice(days,n,p=weights/weights.sum())).sort_values().reset_index(drop=True); y=d.dt.year.to_numpy()==2025
s=r.integers(1,7,n); channel=np.where(r.random(n)<np.where(y,.45,.32),'online','store'); customer=r.choice(customers.customer_id,n,p=(w:=r.lognormal(0,.85,len(customers)))/w.sum()); status=np.where(r.random(n)<.045,'cancelled','completed')
orders=save('orders',pd.DataFrame(dict(order_id=np.arange(1,n+1),day=d.dt.strftime('%Y-%m-%d'),customer_id=customer,store_id=s,warehouse_id=(s+1)//2,channel=channel,marketing_id=r.integers(1,5,n),status=status)))
ix=np.repeat(np.arange(n),r.choice([1,2,3],n,p=[.65,.28,.07])); k=len(ix); yy=y[ix]; category=np.array([r.choice(6,p=[.20,.16,.15,.19,.20,.10] if a else [.20,.19,.17,.12,.22,.10]) for a in yy]); prod=category*100+r.integers(0,100,k); promo=np.array([r.choice(4,p=[.20,.30,.32,.18] if a else [.40,.35,.20,.05]) for a in yy]); qty=np.where(category>=4,r.integers(1,4,k),1); unitcost=np.round(cost[prod]*np.where(yy,1.045,1),2)
items=pd.DataFrame(dict(item_id=np.arange(1,k+1),order_id=ix+1,product_id=prod+1,promotion_id=promo+1,quantity=qty,unit_price=price[prod],unit_cost=unitcost)); dirty=pd.concat([items,items.iloc[:80]],ignore_index=True); dirty.loc[100:129,'unit_price']=np.nan; save('order_items',dirty)
completed=status[ix]=='completed'; delivered=d.iloc[ix].reset_index(drop=True)+pd.to_timedelta(5,unit='D'); ret=(r.random(k)<(.035+.045*(channel[ix]=='online')+.035*(category==3)))&completed; retday=delivered+pd.to_timedelta(r.integers(1,25,k),unit='D'); ret &= retday<=pd.Timestamp('2026-01-31'); ri=np.flatnonzero(ret); save('returns',pd.DataFrame(dict(return_id=np.arange(1,len(ri)+1),item_id=ri+1,return_day=retday.iloc[ri].dt.strftime('%Y-%m-%d').to_numpy(),quantity=r.integers(1,qty[ri]+1),reason=r.choice(['damage','fit','changed_mind'],len(ri)))))
valid=np.flatnonzero(status=='completed'); late=r.random(len(valid))<np.where(channel[valid]=='online',.17,.08); save('deliveries',pd.DataFrame(dict(order_id=valid+1,promised_days=5,actual_days=np.where(late,r.integers(6,12,len(valid)),r.integers(1,6,len(valid))),delivery_cost=np.where(channel[valid]=='online',r.integers(700,2400,len(valid)),r.integers(0,500,len(valid))))))
from inventory import generate as generate_inventory
generate_inventory()
