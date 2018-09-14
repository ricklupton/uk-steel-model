data/flows.csv: data/intermediate_products.csv
	pipenv run python scripts/assemble_flows.py

data/intermediate_products.csv:
	pipenv run python scripts/recategorise_production.py
