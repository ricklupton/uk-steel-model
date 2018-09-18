"""Bring together all the data into a list of flows.

Created by Rick Lupton, 17 August 2018.

"""

from collections import defaultdict
import pandas as pd
from logzero import logger
import os.path

from util import load_dataframe

logger.info('Starting %s', os.path.basename(__file__))

###########################################################################
# 1. Load data
###########################################################################

# find the root path of the other data files, relative to this script.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Load data tables
intermediate = pd.read_csv('data/intermediate_products.csv', index_col=['year', 'product'])

# alloc = load_dataframe('allocations/datapackage.json', 'product_sector_allocations') \
#     .set_index('product') \
#     .astype(float)
# assert all(abs(alloc.sum(axis=1) - 1) < 0.01), 'allocations should sum to 1'
# alloc = load_dataframe(os.path.join(ROOT, 'issb-statistics/datapackage.json'),
#                        'deliveries')
    # .set_index('product') \
    # .astype(float)

alloc = pd.read_csv('allocations/intermediate_products_to_sectors.csv', index_col=0) \
    .fillna(0.0)

alloc_numeric = alloc[[c for c, d in zip(alloc.columns, alloc.dtypes) if d == 'float64']]
if not all(abs(alloc_numeric.sum(axis=0) - 1) < 0.01):
    logger.error('Allocations must sum to 1:\n' + str(alloc_numeric.sum(axis=0)))
    # assert False
    # XXX

# sector_yield_losses = load_dataframe('allocations/datapackage.json', 'sector_yield_losses') \
#     .set_index('product') \
#     .astype(float)
sector_yield_losses = pd.read_csv('allocations/data/yield_losses.csv', index_col=0) \
    .fillna(0.0)
assert all(sector_yield_losses <= 1), 'sector yield losses should be less than 1'
assert all(sector_yield_losses >= 0), 'sector yield losses should be greater than 0'

product_imports = load_dataframe(
    os.path.join(ROOT, 'uk-steel-trade/datapackage.json'), 'imports') \
    .set_index(['year', 'sector_code'])
product_exports = load_dataframe(
    os.path.join(ROOT, 'uk-steel-trade/datapackage.json'), 'exports') \
    .set_index(['year', 'sector_code'])

###########################################################################
# 2. Build list of flows
###########################################################################

def build_flows_for_year(year):
    logger.info('Building flows for year %d', year)
    flows = []
    sector_output = defaultdict(float)

    # Data for this year
    ints = intermediate.loc[year]

    for p in ints.index.values:
        # Up to UK intermediate products: flows A and B
        flows.append(('uk_production', 'uk_intermediate', p,
                    ints.loc[p, 'production'] - ints.loc[p, 'exports']))
        flows.append(('uk_production', 'exports', p, ints.loc[p, 'exports']))
        flows.append(('imports', 'uk_intermediate', p, ints.loc[p, 'imports']))

        # From UK intermediate products to sectors that use them: flow C, D, E
        delivered = ints.loc[p, 'delivered']
        for s in alloc.index:
            x = delivered * alloc.loc[s, p]
            y = sector_yield_losses.loc[s, p]
            flows.append(('uk_intermediate', s, p, x))  # flow C
            flows.append((s, 'scrap', 'scrap ' + p, x * y))  # flow D
            flows.append((s, 'products', s, x * (1 - y)))  # flow E
            sector_output[s] += x * (1 - y)

    logger.debug('sector_output: %s', sector_output)

    # Finished products imports and exports
    for sector in product_imports.index.levels[1]:
        exports = float(product_exports.loc[(year, sector), 'mass_iron'])
        imports = float(product_imports.loc[(year, sector), 'mass_iron'])
        flows.append(('products', 'product_exports', sector, exports))

        if exports > sector_output[sector]:
            logger.error('Too many exports for sector %s: exports = %.1f, production = %.1f',
                         sector, exports, sector_output[sector])
            flows.append(('imbalance', 'products', sector, exports - sector_output[sector]))
        else:
            flows.append(('products', 'uk_demand', sector, sector_output[sector] - exports))
        flows.append(('product_imports', 'uk_demand', sector, imports))

    flows = pd.DataFrame(flows, columns=('source', 'target', 'material', 'value'))
    flows['year'] = year
    return flows

years = [2016]
all_flows = pd.concat([
    build_flows_for_year(year) for year in years
])

all_flows = all_flows[all_flows['value'] > 0]

COLUMNS = ['source', 'target', 'material', 'year', 'value']

all_flows[COLUMNS].to_csv('data/flows.csv', index=False, float_format='%.1f')
