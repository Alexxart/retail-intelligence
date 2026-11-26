-- 01. Годовые KPI
SELECT year,SUM(net) net,SUM(net-cogs) profit,COUNT(DISTINCT order_id) orders FROM sales GROUP BY year;

-- 02. Маржа категорий
SELECT year,category,SUM(net-cogs)/SUM(net) margin FROM sales GROUP BY year,category;

-- 03. Скидки
SELECT year,discount,SUM(net-cogs)/SUM(net) margin FROM sales GROUP BY year,discount;

-- 04. Возвраты
SELECT category,1.0*SUM(returned)/SUM(quantity) rate FROM sales GROUP BY category;

-- 05. Каналы
SELECT channel,SUM(net) net,SUM(net-cogs) profit FROM sales GROUP BY channel;

-- 06. Средний чек
SELECT year,SUM(net)/COUNT(DISTINCT order_id) aov FROM sales GROUP BY year;

-- 07. Динамика MoM
WITH m AS (SELECT month,SUM(net) net FROM sales GROUP BY month) SELECT *,net/NULLIF(LAG(net) OVER(ORDER BY month),0)-1 growth FROM m;

-- 08. Накопительная выручка
WITH m AS (SELECT month,SUM(net) net FROM sales GROUP BY month) SELECT *,SUM(net) OVER(ORDER BY month) cumulative FROM m;

-- 09. Рейтинг SKU
WITH p AS (SELECT product_id,SUM(net) net FROM sales GROUP BY product_id) SELECT *,RANK() OVER(ORDER BY net DESC) ranking FROM p;

-- 10. ABC
WITH p AS (SELECT product_id,SUM(net) net FROM sales GROUP BY product_id), a AS (SELECT *, (SUM(net) OVER(ORDER BY net DESC,product_id ROWS UNBOUNDED PRECEDING)-net)/SUM(net) OVER() share FROM p) SELECT *,CASE WHEN share<0.8 THEN 'A' WHEN share<0.95 THEN 'B' ELSE 'C' END class FROM a;

-- 11. Повторные клиенты
WITH c AS (SELECT customer_id,COUNT(DISTINCT order_id) n FROM sales GROUP BY customer_id) SELECT AVG(CASE WHEN n>1 THEN 1.0 ELSE 0.0 END) repeat_rate FROM c;

-- 12. RFM основа
SELECT customer_id,MAX(day) last_day,COUNT(DISTINCT order_id) frequency,SUM(net) monetary FROM sales GROUP BY customer_id;

-- 13. Слабая прибыльность
SELECT product_id,SUM(net) net,SUM(net-cogs) profit FROM sales GROUP BY product_id HAVING SUM(net-cogs)/NULLIF(SUM(net),0)<0.15 ORDER BY net DESC;

-- 14. Доставка
SELECT o.channel,AVG(d.delivery_cost) avg_cost,AVG(CASE WHEN actual_days>promised_days THEN 1.0 ELSE 0.0 END) late FROM deliveries d JOIN orders o ON d.order_id=o.order_id GROUP BY o.channel;

-- 15. Остатки
SELECT month,warehouse_id,SUM(stock_end) units FROM inventory GROUP BY month,warehouse_id;

-- 16. Дефицит
SELECT product_id,SUM(stockout_days) days FROM inventory GROUP BY product_id ORDER BY days DESC;

-- 17. Региональная динамика
SELECT year,region,SUM(net) net FROM sales GROUP BY year,region;

-- 18. Отмены
SELECT channel,AVG(CASE WHEN status='cancelled' THEN 1.0 ELSE 0.0 END) cancel_rate FROM orders GROUP BY channel;

-- 19. Причины возврата
SELECT reason,SUM(quantity) units FROM returns GROUP BY reason;

-- 20. Первый заказ
SELECT customer_id,order_id,day FROM (SELECT *,ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY day,order_id) rn FROM orders WHERE status='completed') q WHERE rn=1;

-- 21. Следующая покупка
SELECT customer_id,order_id,day,LEAD(day) OVER(PARTITION BY customer_id ORDER BY day,order_id) next_day FROM orders WHERE status='completed';

-- 22. Складские KPI по годам
WITH s AS (SELECT year,SUM(cogs) cogs FROM sales GROUP BY year), i AS (SELECT substr(CAST(month AS TEXT),1,4) year,SUM(stock_unit_days*p.unit_cost*CASE WHEN substr(CAST(month AS TEXT),1,4)='2025' THEN 1.045 ELSE 1 END) value_days,SUM(stockout_days) shortage,SUM(unmet_demand) unmet,SUM(sales) units FROM inventory JOIN products p USING(product_id) GROUP BY substr(CAST(month AS TEXT),1,4)), a AS (SELECT i.*,s.cogs,CASE WHEN i.year='2024' THEN 366 ELSE 365 END days FROM i JOIN s USING(year)) SELECT year,value_days/days avg_inventory,cogs/(value_days/days) turnover,value_days/cogs dio,1.0*shortage/(days*1800) stockout_rate,1.0*unmet/(units+unmet) unmet_rate FROM a ORDER BY year;

-- 23. ABC XYZ по годам
WITH months AS (SELECT DISTINCT substr(CAST(day AS TEXT),1,7) month FROM calendar), m AS (SELECT product_id,month,SUM(quantity) units,SUM(net) net FROM sales GROUP BY product_id,month), grid AS (SELECT p.product_id,substr(t.month,1,4) year,COALESCE(m.units,0) units,COALESCE(m.net,0) net FROM products p CROSS JOIN months t LEFT JOIN m ON m.product_id=p.product_id AND m.month=t.month), a AS (SELECT year,product_id,SUM(net) net,AVG(1.0*units) mu,AVG(1.0*units*units) m2 FROM grid GROUP BY year,product_id), b AS (SELECT *, (SUM(net) OVER(PARTITION BY year ORDER BY net DESC,product_id ROWS UNBOUNDED PRECEDING)-net)/SUM(net) OVER(PARTITION BY year) prior_share,(m2-mu*mu)/NULLIF(mu*mu,0) cv2 FROM a) SELECT year,product_id,net,CASE WHEN prior_share<0.8 THEN 'A' WHEN prior_share<0.95 THEN 'B' ELSE 'C' END abc,CASE WHEN cv2<=0.0625 THEN 'X' WHEN cv2<=0.25 THEN 'Y' ELSE 'Z' END xyz FROM b ORDER BY year,product_id;

-- 24. Когорты по месяцу первой наблюдаемой покупки
WITH a AS (SELECT DISTINCT customer_id,month FROM sales), b AS (SELECT customer_id,MIN(month) cohort FROM a GROUP BY customer_id), c AS (SELECT cohort,COUNT(*) cohort_size FROM b GROUP BY cohort) SELECT b.cohort,a.month,COUNT(*) active,c.cohort_size,1.0*COUNT(*)/c.cohort_size retention FROM a JOIN b USING(customer_id) JOIN c ON b.cohort=c.cohort GROUP BY b.cohort,a.month,c.cohort_size ORDER BY b.cohort,a.month;

-- 25. Повторные покупки по годам
WITH c AS (SELECT year,customer_id,COUNT(DISTINCT order_id) n FROM sales GROUP BY year,customer_id) SELECT year,COUNT(*) buyers,SUM(CASE WHEN n>1 THEN 1 ELSE 0 END) repeat_buyers,AVG(CASE WHEN n>1 THEN 1.0 ELSE 0.0 END) repeat_rate FROM c GROUP BY year ORDER BY year;

-- 26. Клиентские сегменты
WITH c AS (SELECT customer_id,MAX(day) last_day,COUNT(DISTINCT order_id) frequency,SUM(net) monetary FROM sales GROUP BY customer_id), s AS (SELECT *,CASE WHEN frequency>=4 AND last_day>='2025-10-03' THEN 'active_repeat' WHEN frequency=1 THEN 'one_time' ELSE 'other' END segment FROM c) SELECT segment,COUNT(*) buyers,SUM(monetary) net FROM s GROUP BY segment ORDER BY segment;

-- 27. Убыточные SKU по годам
SELECT year,product_id,SUM(net) net,SUM(net-cogs) profit FROM sales GROUP BY year,product_id HAVING SUM(net-cogs)<0 ORDER BY year,profit;

-- 28. Складской баланс и непрерывность
WITH a AS (SELECT *,LAG(stock_end) OVER(PARTITION BY warehouse_id,product_id ORDER BY month) previous_end FROM inventory) SELECT COUNT(*) records,SUM(CASE WHEN stock_start+receipts+emergency_receipts+restocked-sales<>stock_end THEN 1 ELSE 0 END) balance_errors,SUM(CASE WHEN previous_end<>stock_start THEN 1 ELSE 0 END) continuity_errors FROM a;

-- 29. Доставка по годам без размножения строк
SELECT substr(CAST(o.day AS TEXT),1,4) year,o.channel,COUNT(*) orders,SUM(d.delivery_cost) cost,AVG(1.0*d.delivery_cost) cost_per_order,AVG(CASE WHEN actual_days>promised_days THEN 1.0 ELSE 0.0 END) late_rate FROM deliveries d JOIN orders o USING(order_id) WHERE o.status='completed' GROUP BY substr(CAST(o.day AS TEXT),1,4),o.channel ORDER BY year,channel;