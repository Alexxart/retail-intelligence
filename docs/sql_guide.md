# SQL: задачи и результаты

## 01. Годовые KPI
```sql
SELECT year,SUM(net) net,SUM(net-cogs) profit,COUNT(DISTINCT order_id) orders FROM sales GROUP BY year
```
Результат: `data/processed/sql_01.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 02. Маржа категорий
```sql
SELECT year,category,SUM(net-cogs)/SUM(net) margin FROM sales GROUP BY year,category
```
Результат: `data/processed/sql_02.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 03. Скидки
```sql
SELECT year,discount,SUM(net-cogs)/SUM(net) margin FROM sales GROUP BY year,discount
```
Результат: `data/processed/sql_03.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 04. Возвраты
```sql
SELECT category,1.0*SUM(returned)/SUM(quantity) rate FROM sales GROUP BY category
```
Результат: `data/processed/sql_04.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 05. Каналы
```sql
SELECT channel,SUM(net) net,SUM(net-cogs) profit FROM sales GROUP BY channel
```
Результат: `data/processed/sql_05.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 06. Средний чек
```sql
SELECT year,SUM(net)/COUNT(DISTINCT order_id) aov FROM sales GROUP BY year
```
Результат: `data/processed/sql_06.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 07. Динамика MoM
```sql
WITH m AS (SELECT month,SUM(net) net FROM sales GROUP BY month) SELECT *,net/NULLIF(LAG(net) OVER(ORDER BY month),0)-1 growth FROM m
```
Результат: `data/processed/sql_07.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 08. Накопительная выручка
```sql
WITH m AS (SELECT month,SUM(net) net FROM sales GROUP BY month) SELECT *,SUM(net) OVER(ORDER BY month) cumulative FROM m
```
Результат: `data/processed/sql_08.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 09. Рейтинг SKU
```sql
WITH p AS (SELECT product_id,SUM(net) net FROM sales GROUP BY product_id) SELECT *,RANK() OVER(ORDER BY net DESC) ranking FROM p
```
Результат: `data/processed/sql_09.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 10. ABC
```sql
WITH p AS (SELECT product_id,SUM(net) net FROM sales GROUP BY product_id), a AS (SELECT *, (SUM(net) OVER(ORDER BY net DESC,product_id ROWS UNBOUNDED PRECEDING)-net)/SUM(net) OVER() share FROM p) SELECT *,CASE WHEN share<0.8 THEN 'A' WHEN share<0.95 THEN 'B' ELSE 'C' END class FROM a
```
Результат: `data/processed/sql_10.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 11. Повторные клиенты
```sql
WITH c AS (SELECT customer_id,COUNT(DISTINCT order_id) n FROM sales GROUP BY customer_id) SELECT AVG(CASE WHEN n>1 THEN 1.0 ELSE 0.0 END) repeat_rate FROM c
```
Результат: `data/processed/sql_11.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 12. RFM основа
```sql
SELECT customer_id,MAX(day) last_day,COUNT(DISTINCT order_id) frequency,SUM(net) monetary FROM sales GROUP BY customer_id
```
Результат: `data/processed/sql_12.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 13. Слабая прибыльность
```sql
SELECT product_id,SUM(net) net,SUM(net-cogs) profit FROM sales GROUP BY product_id HAVING SUM(net-cogs)/NULLIF(SUM(net),0)<0.15 ORDER BY net DESC
```
Результат: `data/processed/sql_13.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 14. Доставка
```sql
SELECT o.channel,AVG(d.delivery_cost) avg_cost,AVG(CASE WHEN actual_days>promised_days THEN 1.0 ELSE 0.0 END) late FROM deliveries d JOIN orders o ON d.order_id=o.order_id GROUP BY o.channel
```
Результат: `data/processed/sql_14.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 15. Остатки
```sql
SELECT month,warehouse_id,SUM(stock_end) units FROM inventory GROUP BY month,warehouse_id
```
Результат: `data/processed/sql_15.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 16. Дефицит
```sql
SELECT product_id,SUM(stockout_days) days FROM inventory GROUP BY product_id ORDER BY days DESC
```
Результат: `data/processed/sql_16.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 17. Региональная динамика
```sql
SELECT year,region,SUM(net) net FROM sales GROUP BY year,region
```
Результат: `data/processed/sql_17.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 18. Отмены
```sql
SELECT channel,AVG(CASE WHEN status='cancelled' THEN 1.0 ELSE 0.0 END) cancel_rate FROM orders GROUP BY channel
```
Результат: `data/processed/sql_18.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 19. Причины возврата
```sql
SELECT reason,SUM(quantity) units FROM returns GROUP BY reason
```
Результат: `data/processed/sql_19.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 20. Первый заказ
```sql
SELECT customer_id,order_id,day FROM (SELECT *,ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY day,order_id) rn FROM orders WHERE status='completed') q WHERE rn=1
```
Результат: `data/processed/sql_20.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.

## 21. Следующая покупка
```sql
SELECT customer_id,order_id,day,LEAD(day) OVER(PARTITION BY customer_id ORDER BY day,order_id) next_day FROM orders WHERE status='completed'
```
Результат: `data/processed/sql_21.csv`. Проверено в SQLite. При работе с sales учитывайте гранулярность позиции: заказы считаются DISTINCT, доли — отношением сумм.
## 22–29 / Расширение stage3
См. analysis.sql и docs/stage3.md: складские KPI, ABC/XYZ, когорты, повторные покупки, сегменты, убыточные SKU, баланс, логистика. Результаты сохранены отдельно. Не соединяйте складские агрегаты с позициями без предварительной агрегации.
