UK_STEEL_TRADE_DOI = 10.5281/zenodo.2591364
UK_STEEL_TRADE_FILENAME = uk-steel-trade-v2.0.0.zip

WORLDSTEEL_DOI = 10.5281/zenodo.2591422
WORLDSTEEL_FILENAME = uk-worldsteel-statistics-v1.0.0.zip

# ISSB path is passed in as environment variable
ISSB_FILENAME = uk-issb-statistics-v1.0.0.zip

ALLOCATIONS = allocations/alloc_products_sectors_home.csv allocations/alloc_products_sectors_imports.csv

.phony: all clean

all: data/flows.csv

clean:
	rm -rf build
	rm -f data/flows.csv

# Data dependencies

build/input_data/$(UK_STEEL_TRADE_FILENAME):
	mkdir -p build/input_data
	cd build/input_data && pipenv run zenodo_get.py $(UK_STEEL_TRADE_DOI)

build/input_data/$(WORLDSTEEL_FILENAME):
	mkdir -p build/input_data
	cd build/input_data && pipenv run zenodo_get.py $(WORLDSTEEL_DOI)

build/input_data/$(ISSB_FILENAME):
	mkdir -p build/input_data
	test -f "$(ISSB_DATAPACKAGE_ZIP)"  # Check $$ISSB_DATAPACKAGE_ZIP exists
	cp $(ISSB_DATAPACKAGE_ZIP) build/input_data/$(ISSB_FILENAME)

# The processed data files

data/flows.csv: build/intermediate_products.csv scripts/assemble_flows.py $(ALLOCATIONS) build/input_data/$(UK_STEEL_TRADE_FILENAME)
	pipenv run python scripts/assemble_flows.py

build/intermediate_products.csv: scripts/recategorise_production.py build/input_data/$(WORLDSTEEL_FILENAME) build/input_data/$(ISSB_FILENAME)
	pipenv run python scripts/recategorise_production.py
