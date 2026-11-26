"""Daily stock ledger conditional on observed completed sales; independent seed."""
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]; raw=R/'data/raw'; out=R/'data/processed'
def load(n): return pd.read_csv(raw/f'{n}.csv')
def generate():
    rng=np.random.default_rng(2026)
    orders=load('orders'); items=load('order_items').drop_duplicates('item_id').merge(orders,on='order_id'); items=items[items.status=='completed']
    dates=pd.date_range('2024-01-01','2025-12-31'); n=len(dates); shape=(n,3,600)
    def cube(df,date):
        a=np.zeros(shape,dtype=np.int32); d=(pd.to_datetime(df[date])-dates[0]).dt.days.to_numpy(); ok=(d>=0)&(d<n)
        np.add.at(a,(d[ok],df.warehouse_id.to_numpy()[ok]-1,df.product_id.to_numpy()[ok]-1),df.quantity.to_numpy()[ok]); return a
    sold=cube(items,'day'); ret=cube(load('returns').merge(items[['item_id','warehouse_id','product_id']],on='item_id',validate='many_to_one'),'return_day')
    # Forecast from category-independent prior rate, seasonal multiplier and rolling observed sales.
    lead=np.broadcast_to(np.where(np.arange(600)%10==1,14,7),(3,600)); target=np.broadcast_to(np.where(np.arange(600)%10==0,25,5),(3,600)); stock=target.copy(); pending=np.zeros((n+15,3,600),dtype=np.int32); pipeline=np.zeros((3,600),dtype=np.int32); history=[]; frames=[]
    cost=load('products').unit_cost.to_numpy(); avg_rate=np.full((3,600),.075)
    for t,day in enumerate(dates):
        opening=stock.copy(); regular=pending[t]; pipeline-=regular; available=opening+regular+ret[t]
        # Emergency same-day transfer preserves original fulfilled sales; extra demand is explicitly simulated.
        extra=rng.poisson(avg_rate*.18*(1.4 if day.month in (11,12) else 1)); emergency=np.maximum(sold[t]-available,0); unmet=np.maximum(extra-np.maximum(available-sold[t],0),0)
        stock=available+emergency-sold[t]; shortage=(emergency>0)|(unmet>0)|(stock==0)
        avg_rate=.95*avg_rate+.05*sold[t]; desired=np.ceil(avg_rate*(lead+14)*(1.4 if day.month in (10,11,12) else 1)).astype(int)+target
        ordered=np.where(stock+pipeline<desired//2,np.maximum(desired-stock-pipeline,0),0); pipeline+=ordered
        for l in (7,14): pending[t+l]+=np.where(lead==l,ordered,0)
        frames.append(pd.DataFrame(dict(day=day.strftime('%Y-%m-%d'),warehouse_id=np.repeat(np.arange(1,4),600),product_id=np.tile(np.arange(1,601),3),stock_start=opening.ravel(),receipts=regular.ravel(),emergency_receipts=emergency.ravel(),sales=sold[t].ravel(),restocked=ret[t].ravel(),stock_end=stock.ravel(),unmet_demand=unmet.ravel(),stockout=shortage.astype(int).ravel(),ordered=ordered.ravel(),lead_days=lead.ravel())))
    ledger=pd.concat(frames,ignore_index=True); ledger.to_csv(raw/'inventory_daily.csv.gz',index=False,compression={'method':'gzip','mtime':0}); ledger['month']=ledger.day.str[:7]+'-01'; monthly=ledger.groupby(['month','warehouse_id','product_id'],sort=True).agg(stock_start=('stock_start','first'),receipts=('receipts','sum'),emergency_receipts=('emergency_receipts','sum'),sales=('sales','sum'),restocked=('restocked','sum'),stock_end=('stock_end','last'),stockout_days=('stockout','sum'),unmet_demand=('unmet_demand','sum'),ordered=('ordered','sum'),lead_days=('lead_days','first'),stock_unit_days=('stock_end','sum')).reset_index(); monthly.to_csv(raw/'inventory.csv',index=False)
    assert (ledger.stock_start+ledger.receipts+ledger.emergency_receipts+ledger.restocked-ledger.sales==ledger.stock_end).all(); assert (ledger.stock_end>=0).all(); assert ledger.sales.sum()==items.quantity.sum(); assert ledger.restocked.sum()==ret.sum()
if __name__=='__main__': generate()
