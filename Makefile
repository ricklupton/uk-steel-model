data/flows.csv: data/intermediate_products.csv scripts/assemble_flows.py
	pipenv run ipython --pdb scripts/assemble_flows.py

data/intermediate_products.csv: scripts/recategorise_production.py
	pipenv run python scripts/recategorise_production.py
