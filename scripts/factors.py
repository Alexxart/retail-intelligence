from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; O=R/'data/processed'
f=pd.read_csv(O/'sales_fact.csv'); f['list_value']=f.quantity*f.unit_price; f['discount_value']=f.list_value*f.discount; f['cost_value']=f.quantity*f.unit_cost; f['return_profit']=f.returned*(f.unit_price*(1-f.discount)-f.unit_cost)
a=f.groupby(['year','category'])[['quantity','list_value','discount_value','cost_value','return_profit','profit']].sum(); cats=sorted(f.category.unique())
def params(y):
 t=a.loc[y].reindex(cats); q=t.quantity; return [q.sum(),q/q.sum(),t.list_value/q,t.discount_value/q,t.cost_value/q,t.return_profit/q]
def profit(x):
 v,m,p,d,c,r=x; return v*(m*(p-d-c-r)).sum()
x=params(2024); z=params(2025); start=a.loc[2024].profit.sum(); end=a.loc[2025].profit.sum(); rows=[]
for j,name in enumerate(['Объём','Микс категорий','Цена до скидки','Скидки','Себестоимость','Возвраты']):
 before=profit(x); x[j]=z[j]; rows.append((name,profit(x)-before))
rows.append(('Округление',end-start-sum(v for _,v in rows))); b=pd.DataFrame(rows,columns=['factor','effect']); b.to_csv(O/'profit_bridge.csv',index=False); assert abs(start+b.effect.sum()-end)<.001
fig,ax=plt.subplots(figsize=(11,5)); running=start; ax.bar(0,start/1e6,color='#14243D');
for j,(_,v) in enumerate(rows,1):
 ax.bar(j,abs(v)/1e6,bottom=min(running,running+v)/1e6,color='#BBA17A' if v>=0 else '#a65353'); ax.text(j,max(running,running+v)/1e6+4,f'{v/1e6:+.1f}',ha='center',fontsize=9); running+=v
ax.bar(len(rows)+1,end/1e6,color='#14243D'); ax.set_xticks(range(len(rows)+2),['2024']+list(b.factor)+['2025'],rotation=20,ha='right'); ax.set_ylabel('млн ₽'); ax.set_title('Изменение валовой прибыли · синтетические данные'); ax.spines[['top','right']].set_visible(False); fig.tight_layout(); fig.savefig(R/'images/profit_waterfall.png',dpi=180); plt.close(fig)
print(start,end,b.to_string(index=False))
# All 720 orders: exact Shapley average and range of order-dependent effects.
from itertools import permutations
names=['Объём','Микс категорий','Цена до скидки','Скидки','Себестоимость','Возвраты']; base=params(2024); target=params(2025); effects=[]
for order in permutations(range(6)):
    state=base.copy(); row=np.zeros(6)
    for j in order:
        before=profit(state); state[j]=target[j]; row[j]=profit(state)-before
    assert abs(row.sum()-(profit(target)-profit(base)))<.001
    effects.append(row)
e=np.array(effects); pd.DataFrame({'factor':names,'min':e.min(axis=0),'max':e.max(axis=0),'shapley':e.mean(axis=0),'positive_orders':(e>0).sum(axis=0)}).to_csv(O/'factor_sensitivity.csv',index=False)
# Return effect at category level under original sequence (returns last).
t0=a.loc[2024].reindex(cats); t1=a.loc[2025].reindex(cats); pd.DataFrame({'category':cats,'return_profit_per_unit_2024':(t0.return_profit/t0.quantity).values,'return_profit_per_unit_2025':(t1.return_profit/t1.quantity).values,'effect':(t1.quantity*(t0.return_profit/t0.quantity-t1.return_profit/t1.quantity)).values}).to_csv(O/'return_factor_detail.csv',index=False)
