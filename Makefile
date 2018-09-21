data/flows.csv: data/intermediate_products.csv scripts/assemble_flows.py allocations/alloc_products_sectors_home.csv allocations/alloc_products_sectors_imports.csv
	pipenv run ipython --pdb scripts/assemble_flows.py

data/intermediate_products.csv: scripts/recategorise_production.py
	pipenv run python scripts/recategorise_production.py
