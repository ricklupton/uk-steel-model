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
from logzero import logger
import os.path

from util import load_datapackage_tables

logger.info('Starting %s', os.path.basename(__file__))


###########################################################################
# 1. Load data
###########################################################################

# find the root path of the other data files, relative to this script.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Load data tables
issb_tables = load_datapackage_tables(os.path.join(ROOT, 'issb-statistics/datapackage.json'))
worldsteel_tables = load_datapackage_tables(os.path.join(ROOT, 'worldsteel-statistics/datapackage.json'))

# Extract ISSB production tables. The first is just ECSC, which is used for
# scaling imports & exports for consistency with Andre's spreadsheet. The
# second is net production (the value we really want).
issb_ecsc = issb_tables['production_ecsc']['mass']
issb = issb_tables['production']['mass']

# Extract worldsteel production table.
worldsteel = worldsteel_tables['production']['mass']

# Extract ISSB import and export tables.
imports = issb_tables['supply']['imports']
exports = issb_tables['exports']['mass']


###########################################################################
# 2. Define the mapping
###########################################################################

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
        'Heavy sections': worldsteel_func(HSEC, 'Heavy sections (>=80mm)'),
        'Sheet piling and rolled accessories': (
            issb_data['Heavy sections, sheet piling, rails and rolled accessories'] -
            worldsteel_func(HSEC, 'Heavy sections (>=80mm)') -
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

def calculate_for_year(year):

    # These functions define how to scale imports and exports, which are unknown
    # for worldsteel data.

    def scale_exports(ref_categories, k):
        production = worldsteel[year, k]
        ref_exports = sum(exports[year, c] for c in ref_categories)
        # XXX this should perhaps be relative to net `issb` -- but being consistent
        # with André for now.
        ref_production = sum(issb_ecsc[year, c] for c in ref_categories)
        logger.debug('Scaling exports of "%s" with respect to %s: %.1f * %.1f / %.1f',
                    k, ref_categories, production, ref_exports, ref_production)
        return production * ref_exports / ref_production

    def scale_imports(ref_categories, k):
        deliveries = worldsteel[year, k] - scale_exports(ref_categories, k)
        ref_imports = sum(imports[year, c] for c in ref_categories)
        # XXX this should perhaps be relative to net `issb` -- but being consistent
        # with André for now.
        ref_deliveries = sum(issb_ecsc[year, c] - exports[year, c] for c in ref_categories)
        logger.debug('Scaling imports of "%s" with respect to %s: %.1f * %.1f / %.1f',
                    k, ref_categories, deliveries, ref_imports, ref_deliveries)
        return deliveries * ref_imports / ref_deliveries

    # This function just looks up the worldsteel production data, for consistency
    # with the two above.
    def lookup_production(_, k):
        return worldsteel[year, k]

    try:
        issb_this_year = issb.loc[year]
    except KeyError:
        raise KeyError('No ISSB production data for year %d' % year)
    try:
        exports_this_year = exports.loc[year]
    except KeyError:
        raise KeyError('No ISSB exports data for year %d' % year)
    try:
        imports_this_year = imports.loc[year]
    except KeyError:
        raise KeyError('No ISSB imports data for year %d' % year)
    new_production = recategorise(issb_this_year, lookup_production)
    new_exports = recategorise(exports_this_year, scale_exports)
    new_imports = recategorise(imports_this_year, scale_imports)

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

    # Add year column
    df['year'] = year

    return df.reset_index()

###########################################################################
# 4. Save the results as a single new table
###########################################################################

# YEARS = list(issb.index.get_level_values('year').unique())
# YEARS = list(range(2009, 2018))
YEARS = [2015, 2016]
logger.info('Loaded ISSB data with years: %s', YEARS)

results = pd.concat([
    calculate_for_year(year)
    for year in YEARS
])

# sort columns and save
COLUMNS = ['year', 'product', 'product_family', 'production', 'exports', 'imports', 'delivered']

results[COLUMNS].to_csv('data/intermediate_products.csv', index=False, float_format='%.1f')
