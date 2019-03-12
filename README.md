# UK steel flow model

These scripts assemble prepared data on trade and UK production into a full
model of steel flows in the UK. 

## Dependencies

The model depends on these publicly-accessible datapackages:
- [uk-trade-steel](https://github.com/ricklupton/uk-trade-steel)
- [uk-worldsteel-statistics](https://github.com/ricklupton/uk-worldsteel-statistics)

It also depends on data published by ISSB which is not publicly available. The
model expects this to be available as a datapackage when it is run, but
unfortunately we cannot publish this data.

## Uses

This data was prepared for the *TBC report details*.

## Contributing

Corrections and improvements are welcome! Please [get in
touch](https://ricklupton.name), or open an issue or a pull request.

## License

[![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0)

This work is licensed under a [CC-BY
License](http://creativecommons.org/licenses/by/4.0/). Please attribute it as follows:

> Richard Lupton & André Cabrera Serrenho. CITATION TBC. 

## Preparation

Install [Pipenv](https://pipenv.readthedocs.io/en/latest/), and then use it to
set up a Python environment with the necessary packages to prepare the data:

```
pipenv install
```

Run the scripts to download and prepare the data and build the model:

```
make ISSB_DATAPACKAGE_ZIP=path/to/ISSB/datapackage.zip
```

This will:
- Download the required data to `build/input_data`
- Map the ISSB and worldsteel data to a common categorisation, stored in `build/intermediate_products.csv`
- Combine everything together to make the complete list of flows, stored in `data/flows.csv`

