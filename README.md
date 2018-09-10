# UK steel flow model

These scripts assemble all the prepared data into a full model of steel flows in
the UK. Currently it's hard-wired to use just the data for 2016, but it will be
easy to extend to use more years' data when they are available.

## Dependencies

Make sure required Python packages are installed:

```shell
$ pip install pandas datapackage
```

For the Sankey diagram, make sure [floWeaver and
ipysankeywidget](https://github.com/ricklupton/floweaver) are installed and
enabled.

### Data dependencies

The model depends on these datapackages:
- [uk-trade-steel](https://github.com/ricklupton/uk-trade-steel)
- [issb-statistics](https://github.com/ricklupton/issb-statistics)
- [worldsteel-statistics](https://github.com/ricklupton/worldsteel-statistics)

These should be saved in an adjacent folder:

```
..
├── flow-model            <--- this folder
├── issb-statistics
├── uk-steel-trade
└── worldsteel-statistics
```

## Preparation

Set up a Python environment using `pipenv` to create a virtualenv and install
dependencies:

```shell
$ pipenv install
```

First, the ISSB and worldsteel data needs to be mapped into a common
categorisation:

```shell
$ pipenv run python scripts/recategorise_production.py
```

This creates the file `data/intermediate_products.csv`.

Then, bring everything together to make the complete list of flows:

```shell
$ pipenv run python scripts/assemble_flows.py
```

This creates the file `data/flows.csv`.

## Sankey diagram

The Sankey diagram is created in the Jupyter notebook `Sankey.ipynb`.

