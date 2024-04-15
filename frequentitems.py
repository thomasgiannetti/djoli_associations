import pandas as pd
import mysql.connector as connection
from operator import attrgetter
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
import re
import pulp
import streamlit as st


mydb = connection.connect(host="db-djoli-mysql-do-user-14041340-0.b.db.ondigitalocean.com", 
                          database = 'Djoli',
                          user="doadmin", 
                          passwd="AVNS_-9GS1aN10LcIonhOplk",
                          port = 25060,
                          use_pure=True)

orderitems_query = """
SELECT o.orderID, sp.sku
FROM orders o
JOIN orderitems oi ON o.orderID = oi.orderID
JOIN products p ON oi.productID = p.productID
JOIN categories c ON c.categoryID = p.categoryID
JOIN standardproducts sp ON sp.sku = p.sku
WHERE c.name != ('FMCG');
"""
standardproducts_query = """
SELECT *
FROM standardproducts sp;
"""
orderitems = pd.read_sql(orderitems_query,mydb)
standardproducts_df = pd.read_sql(standardproducts_query,mydb)

basket = pd.get_dummies(orderitems['sku']).groupby(orderitems['orderID']).max()
basket.index.rename("orderID")

frequent_itemsets = apriori(basket, min_support=0.005, use_colnames=True)

metric = st.selectbox(
    'Select a metric.',
    ('support', 'confidence', 'lift', 'conviction', 'zhangs_metric'))

rules = association_rules(frequent_itemsets, metric=metric, min_threshold=0.05)

sku_num = st.selectbox(
    'Select the maximum number of SKUs by association.',
    (1,2,3,4,5))

rules['antecedent_len'] = rules['antecedents'].apply(lambda x: len(x))
rules['consequent_len'] = rules['consequents'].apply(lambda x: len(x))

# Filter the rules based on the length of antecedents and consequents
filtered_rules = rules[(rules['antecedent_len'] >= sku_num) & (rules['consequent_len'] >= sku_num)]
sorted_rules = filtered_rules.sort_values(by=["support", "confidence"], ascending=[False, False])

num_itemsets = st.slider("Number of Item Sets", 5, 100, 5)

top_rules = sorted_rules.head(num_itemsets)

# Create a dictionary to map SKU numbers to names
sku_to_name = dict(zip(standardproducts_df['sku'], standardproducts_df['name']))

for index, row in top_rules.iterrows():
    # Map SKU numbers to names for antecedents
    antecedent_names = [sku_to_name[sku] for sku in row['antecedents']]
    antecedents = " & ".join([f"{name}" for name in antecedent_names])
    
    # Map SKU numbers to names for consequents
    consequent_names = [sku_to_name[sku] for sku in row['consequents']]
    consequents = " & ".join([f"{name}" for name in consequent_names])
    
    confidence = row['confidence'] * 100  # Convert confidence to percentage
    support = row['support']

    st.subheader(f"{antecedents} & {consequents}\n")
    st.write(f"There is a {confidence:.2f}% probability of finding {consequents} in a transaction given that {antecedents} is present.\n")
    st.write(f"This item association has occurred in approximately {support:.2f} of all transactions.\n")
    st.markdown(f"\n")
    st.divier()





