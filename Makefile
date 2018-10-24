.phony: all svgs

all: data/flows.csv

data/flows.csv: data/intermediate_products.csv scripts/assemble_flows.py allocations/alloc_products_sectors_home.csv allocations/alloc_products_sectors_imports.csv
	pipenv run ipython --pdb scripts/assemble_flows.py

data/intermediate_products.csv: scripts/recategorise_production.py
	pipenv run ipython --pdb scripts/recategorise_production.py

svgs:
	pipenv run python figures/apply_layout.py
	cd figures && ./convert-svgs.sh
