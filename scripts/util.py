import pandas as pd
import datapackage


def load_dataframe(filename, resource):
    """Load one table from a datapackage."""
    package = datapackage.Package(filename)
    r = package.get_resource(resource)
    return pd.DataFrame(r.read(), columns=r.headers)


def load_datapackage_tables(filename):
    """Load all the tables from a datapackage."""
    package = datapackage.Package(filename)
    tables = {
        r.name: pd.DataFrame(r.read(), columns=r.headers)
        for r in package.resources
    }
    return {
        k: df.set_index(['year', 'product']).loc[2016]
        for k, df in tables.items()
    }
