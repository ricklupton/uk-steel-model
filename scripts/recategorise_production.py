"""Recategorise ISSB and worldsteel production data.

Copying André's calculations in "ISSB-WorldSteel (A,B,C)" sheet.

Imports & exports: We have this for ISSB products directly. For the worldsteel
categories, assume the share of exports relative to production is the same as
for the larger ISSB category (sheets, heavy sections, rods). For imports, it's
scaled relative to deliveries (production - exports).

Created by Rick Lupton, 17 August 2018.

"""

import pandas as pd
import os.path
from util import load_datapackage_tables
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

###########################################################################
# 1. Load data
###########################################################################

# find the root path of the other data files, relative to this script.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Load data tables
issb_tables = load_datapackage_tables(os.path.join(ROOT, 'issb-statistics/datapackage.json'))
worldsteel_tables = load_datapackage_tables(os.path.join(ROOT, 'worldsteel-statistics/datapackage.json'))

# Extract ISSB production table -- ECSC plus derived, minus use of ECSC
# products for feedstocks. Use `fill_value` to fill in zeros instead of NaNs
# where some of the tables don't have a value for every product.
issb_ecsc = issb_tables['production_ecsc']['mass'] \

issb = issb_ecsc \
    .add(issb_tables['production_derived']['mass'], fill_value=0) \
    .sub(issb_tables['production_ecsc_for_derived']['mass'], fill_value=0)

# Extract worldsteel production table.
worldsteel = worldsteel_tables['production']['mass']

# Extract ISSB import and export tables. Note: need to aggregate different
# alloy types in supply table.
imports = issb_tables['supply'].reset_index().groupby(['product'])['imports'].sum()
exports = issb_tables['exports']['mass']


###########################################################################
# 2. Define the mapping
###########################################################################

# These functions define how to scale imports and exports, which are unknown
# for worldsteel data.

def scale_exports(ref_categories, k):
    production = worldsteel[k]
    ref_exports = sum(exports[c] for c in ref_categories)
    # XXX this should perhaps be relative to net `issb` -- but being consistent
    # with André for now.
    ref_production = sum(issb_ecsc[c] for c in ref_categories)
    logger.debug('Scaling exports of "%s" with respect to %s: %.1f * %.1f / %.1f',
                 k, ref_categories, production, ref_exports, ref_production)
    return production * ref_exports / ref_production

def scale_imports(ref_categories, k):
    deliveries = worldsteel[k] - scale_exports(ref_categories, k)
    ref_imports = sum(imports[c] for c in ref_categories)
    # XXX this should perhaps be relative to net `issb` -- but being consistent
    # with André for now.
    ref_deliveries = sum(issb_ecsc[c] - exports[c] for c in ref_categories)
    logger.debug('Scaling imports of "%s" with respect to %s: %.1f * %.1f / %.1f',
                 k, ref_categories, deliveries, ref_imports, ref_deliveries)
    return deliveries * ref_imports / ref_deliveries

# This function just looks up the worldsteel production data, for consistency
# with the two above.

def lookup_production(_, k):
    return worldsteel[k]

# Some useful shorthands
SHEETS = ['Sheets, coated and uncoated']
HSEC = ['Heavy sections, sheet piling, rails and rolled accessories']
RODS = ['Rods and bars for reinforcement',
        'Rods in coil']

def recategorise(issb_data, worldsteel_func):
    """Recategorise production, imports or exports.

    issb_data: pandas.Series
        one of production, exports, imports
    worldsteel_func: callable
        a function that returns the appropriate worldsteel data. It is passed
        two arguments: the first is the reference category for scaling imports
        and exports; the second is the worldsteel category name.

    """

    # Flat products
    flat = {
        'Plate': issb_data['Plates in coil and in lengths'],
        'Cold rolled': issb_data['Cold rolled narrow strip'],
        'Hot dipped galvanised': worldsteel_func(SHEETS, 'Other metal coated sheet and strip'),
        # XXX I don't think this is right
        'Electro coated': worldsteel_func(SHEETS, 'Electrical sheet and strip'),
        'Organic coated': worldsteel_func(SHEETS, 'Non-metalic coated sheet and strip'),
        'Tin plate': worldsteel_func(SHEETS, 'Tinmill products'),
        'Tubes and pipes': issb_data['Tubes and pipes'],
    }

    # Add "Hot rolled" as everything left over in ISSB "Sheets" category
    flat['Hot rolled'] = (
        issb_data['Sheets, coated and uncoated'] -
        flat['Hot dipped galvanised'] -
        flat['Electro coated'] -
        flat['Organic coated'] -
        flat['Tin plate']
    )

    # Long products
    long = {
        'Railway track material': worldsteel_func(HSEC, 'Railway track material'),
        'Heavy sections': (
            issb_data['Heavy sections, sheet piling, rails and rolled accessories'] -
            worldsteel_func(HSEC, 'Railway track material')
        ),
        'Light sections': issb_data['Light sections'],
        'Hot rolled bars in lengths': issb_data['Hot rolled bars in lengths'],
        'Bright bars': issb_data['Bright bars'],
        'Reinforcing bar': worldsteel_func(RODS, 'Concrete reinforced bars'),
    }

    # Add "Rods" as everything left over from ISSB rods, minus rebar
    long['Rods'] = (
        issb_data['Rods and bars for reinforcement'] +
        issb_data['Rods in coil'] -
        long['Reinforcing bar']
    )

    # Combine into new dataframe.
    both = pd.concat([
        pd.DataFrame({'mass': flat, 'product_family': 'flat'}),
        pd.DataFrame({'mass': long, 'product_family': 'long'}),
    ])

    return both


###########################################################################
# 3. Do the recategorisation
###########################################################################

new_production = recategorise(issb, lookup_production)
new_exports = recategorise(exports, scale_exports)
new_imports = recategorise(imports, scale_imports)


###########################################################################
# 4. Save the results as a single new table
###########################################################################

# Stack the three dataframes together. `astype(float)` because datapackage loads
# numbers as Decimal objects which is a little annoying.

df = pd.concat({
    'production': new_production['mass'].astype(float),
    'exports': new_exports['mass'].astype(float),
    'imports': new_imports['mass'].astype(float),
    'product_family': new_production['product_family'],
}, axis='columns')
df.index.name = 'product'

df['delivered'] = df['production'] + df['imports'] - df['exports']

# sort columns
df = df[['product_family', 'production', 'exports', 'imports', 'delivered']]

df.to_csv('data/intermediate_products.csv')
