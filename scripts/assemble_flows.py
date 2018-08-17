"""Bring together all the data into a list of flows.

Created by Rick Lupton, 17 August 2018.

"""

from collections import defaultdict
import pandas as pd
import os.path
from util import load_dataframe
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

###########################################################################
# 1. Load data
###########################################################################

# find the root path of the other data files, relative to this script.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Load data tables
ints = pd.read_csv('data/intermediate_products.csv', index_col='product')

alloc = load_dataframe('allocations/datapackage.json', 'product_sector_allocations') \
    .set_index('product') \
    .astype(float)
assert all(abs(alloc.sum(axis=1) - 1) < 0.01), 'allocations should sum to 1'

sector_yield_losses = load_dataframe('allocations/datapackage.json', 'sector_yield_losses') \
    .set_index('product') \
    .astype(float)
assert all(sector_yield_losses <= 1), 'sector yield losses should be less than 1'
assert all(sector_yield_losses >= 0), 'sector yield losses should be greater than 0'

product_imports = load_dataframe(
    os.path.join(ROOT, 'uk-steel-trade/datapackage.json'), 'imports') \
    .query('year == 2016') \
    .set_index('product_group')
product_exports = load_dataframe(
    os.path.join(ROOT, 'uk-steel-trade/datapackage.json'), 'exports') \
    .query('year == 2016') \
    .set_index('product_group')

###########################################################################
# 2. Build list of flows
###########################################################################

product_lookup = {
    'Construction': 'Structural steelwork and building and civil engineering',
    'Mechanical Engineering': 'Mechanical engineering',
    'Automotive': 'Vehicles',
    'Electrical': 'Electrical engineering',
    'Other Transport': 'Shipbuilding',
    'Tubes': 'Boilers, drums and other vessels',
    'Metal Goods': 'Metal goods',
    'Other sectors': 'Other industries',
}

flows = []
sector_output = defaultdict(float)

for p in ints.index.values:
    # Up to UK intermediate products: flows A and B
    flows.append(('uk_production', 'uk_intermediate', p,
                  ints.loc[p, 'production'] - ints.loc[p, 'exports']))
    flows.append(('uk_production', 'exports', p, ints.loc[p, 'exports']))
    flows.append(('imports', 'uk_intermediate', p, ints.loc[p, 'imports']))

    # From UK intermediate products to sectors that use them: flow C, D, E
    delivered = ints.loc[p, 'delivered']
    for s in alloc.columns:
        x = delivered * alloc.loc[p, s]
        y = sector_yield_losses.loc[p, s]
        prod = product_lookup[s]
        flows.append(('uk_intermediate', s, p, x))  # flow C
        flows.append((s, 'scrap', 'scrap ' + p, x * y))  # flow D
        flows.append((s, 'products', prod, x * (1 - y)))  # flow E
        sector_output[prod] += x * (1 - y)

# Finished products imports and exports
for prod in product_imports.index:
    exports = float(product_exports.loc[prod, 'mass_iron'])
    flows.append(('products', 'product_exports', prod, exports))
    flows.append(('products', 'uk_demand', prod, sector_output[prod] - exports))
    flows.append(('product_imports', 'uk_demand', prod, product_imports.loc[prod, 'mass_iron']))

flows = pd.DataFrame(flows, columns=('source', 'target', 'material', 'value'))
flows.to_csv('data/flows.csv', index=False)
