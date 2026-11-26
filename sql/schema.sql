CREATE TABLE categories (
  category_id INTEGER NOT NULL,
  category TEXT NOT NULL,
  PRIMARY KEY (category_id)
);
CREATE TABLE products (
  product_id INTEGER NOT NULL,
  category_id INTEGER NOT NULL,
  list_price NUMERIC NOT NULL,
  unit_cost NUMERIC NOT NULL,
  PRIMARY KEY (product_id),
  FOREIGN KEY (category_id) REFERENCES categories(category_id)
);
CREATE TABLE customers (
  customer_id INTEGER NOT NULL,
  loyalty TEXT NOT NULL,
  PRIMARY KEY (customer_id)
);
CREATE TABLE stores (
  store_id INTEGER NOT NULL,
  region TEXT NOT NULL,
  PRIMARY KEY (store_id)
);
CREATE TABLE warehouses (
  warehouse_id INTEGER NOT NULL,
  region TEXT NOT NULL,
  PRIMARY KEY (warehouse_id)
);
CREATE TABLE calendar (
  day TEXT NOT NULL,
  PRIMARY KEY (day)
);
CREATE TABLE marketing_channels (
  marketing_id INTEGER NOT NULL,
  source TEXT NOT NULL,
  PRIMARY KEY (marketing_id)
);
CREATE TABLE promotions (
  promotion_id INTEGER NOT NULL,
  discount NUMERIC NOT NULL,
  PRIMARY KEY (promotion_id)
);
CREATE TABLE orders (
  order_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  customer_id INTEGER NOT NULL,
  store_id INTEGER NOT NULL,
  warehouse_id INTEGER NOT NULL,
  channel TEXT NOT NULL,
  marketing_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  PRIMARY KEY (order_id),
  FOREIGN KEY (day) REFERENCES calendar(day),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (store_id) REFERENCES stores(store_id),
  FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
  FOREIGN KEY (marketing_id) REFERENCES marketing_channels(marketing_id)
);
CREATE TABLE order_items (
  item_id INTEGER NOT NULL,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  promotion_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price NUMERIC NOT NULL,
  unit_cost NUMERIC NOT NULL,
  PRIMARY KEY (item_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id),
  FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id)
);
CREATE TABLE returns (
  return_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  return_day TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  reason TEXT NOT NULL,
  PRIMARY KEY (return_id),
  FOREIGN KEY (item_id) REFERENCES order_items(item_id)
);
CREATE TABLE deliveries (
  order_id INTEGER NOT NULL,
  promised_days INTEGER NOT NULL,
  actual_days INTEGER NOT NULL,
  delivery_cost INTEGER NOT NULL,
  PRIMARY KEY (order_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
CREATE TABLE inventory (
  month TEXT NOT NULL,
  warehouse_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  stock_start INTEGER NOT NULL,
  receipts INTEGER NOT NULL,
  emergency_receipts INTEGER NOT NULL,
  sales INTEGER NOT NULL,
  restocked INTEGER NOT NULL,
  stock_end INTEGER NOT NULL,
  stockout_days INTEGER NOT NULL,
  unmet_demand INTEGER NOT NULL,
  ordered INTEGER NOT NULL,
  lead_days INTEGER NOT NULL,
  stock_unit_days INTEGER NOT NULL,
  CHECK (stock_start + receipts + emergency_receipts + restocked - sales = stock_end),
  CHECK (stock_end >= 0 AND stock_start >= 0 AND sales >= 0 AND receipts >= 0 AND emergency_receipts >= 0 AND restocked >= 0 AND unmet_demand >= 0),
  CHECK (lead_days IN (7,14)),
  PRIMARY KEY (month,warehouse_id,product_id),
  FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id),
  FOREIGN KEY (month) REFERENCES calendar(day)
);