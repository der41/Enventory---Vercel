\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV
-- since id is auto-generated; we need the next command to adjust the counter
-- for auto-generation so next INSERT will not clash with ids loaded above:
SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

\COPY Products FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.products_id_seq',
                         (SELECT MAX(id)+1 FROM Products),
                         false);

\COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.purchases_id_seq',
                         (SELECT MAX(id)+1 FROM Purchases),
                         false);

\COPY Wishes FROM 'Wishes.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.wishes_id_seq',
                        (SELECT MAX(id)+1 FROM Wishes),
                        false);

\COPY Address FROM 'Address.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.address_id_seq',
                          (SELECT MAX(id)+1 FROM Address),
                          false);

\COPY Sellers FROM 'Sellers.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.sellers_id_seq',
                        (SELECT MAX(id)+1 FROM Sellers),
                        false);

\COPY Accounts FROM 'Accounts.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.accounts_id_seq',
                          (SELECT MAX(id)+1 FROM Accounts),
                          false);

\COPY Loyalty FROM 'Loyalty.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.loyalty_id_seq', 
                        (SELECT MAX(id)+1 FROM Loyalty),
                        false);

\COPY Purchases_2 FROM 'Purchases_2.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.purchases_2_id_seq',
                         (SELECT MAX(id)+1 FROM Purchases_2),
                         false);

\COPY ProductCategories FROM 'ProductCategories.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.productcategories_id_seq',
                         (SELECT MAX(id)+1 FROM ProductCategories),
                         false);

\COPY Products_2 FROM 'Products_2.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.products_2_id_seq',
                         (SELECT MAX(id)+1 FROM Products_2),
                         false);
                
\COPY Events FROM 'Events.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.events_id_seq',
                         (SELECT MAX(id)+1 FROM Events),
                         false);

\COPY Seller_Reviews FROM 'Seller_Reviews.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.seller_reviews_id_seq',
                         (SELECT MAX(id)+1 FROM Seller_Reviews),
                         false);

\COPY Cart FROM 'Cart.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.cart_id_seq',
                         (SELECT MAX(id)+1 FROM Cart),
                         false);
                        
\COPY Wishlist_2 FROM 'Wishlist_2.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.wishlist_2_id_seq',
                         (SELECT MAX(id)+1 FROM Wishlist_2),
                         false);

\COPY LineItem FROM 'LineItem.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.lineitem_id_seq',
                         (SELECT MAX(id)+1 FROM LineItem),
                         false);

\COPY Inventory FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.inventory_id_seq',
                         (SELECT MAX(id)+1 FROM Inventory),
                         false);

\COPY Product_Reviews FROM 'Product_Reviews.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.product_reviews_id_seq',
                         (SELECT MAX(id)+1 FROM Product_Reviews),
                         false);
                         