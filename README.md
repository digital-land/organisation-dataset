# Digital Land collection of organisations

[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/psd/openregister/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/en/stable/)

A collection of data about Local Planning Authorities and other organisations who publish data used by digital land:

* [collection/organisations.csv](collection/organisations.csv)

The data is assembled from the following authoritative sources:

* [government-organisation](https://www.registers.service.gov.uk/registers/government-organisation)
* [local-authority-eng](https://www.registers.service.gov.uk/registers/local-authority-eng)

and combined with the following datasets, to be replaced with more authoritative sources, where possible:

* [data/development-corporation.csv](data/development-corporation.csv) -- a list of development corporations
* [data/website.csv](data/website.csv) -- websites for local authorities, national parks and development corporations
* [data/statistical-geography.csv](data/gss.csv) -- mapping of organisations to their GSS statistical-geography code

# Updating the collection

We recommend working in [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) before installing the python dependencies:

    $ make init
    $ make

# Licence

The software in this project is open source and covered by LICENSE file.

Individual datasets copied into this repository may have specific copyright and licensing, otherwise all content and data in this repository is
[© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
and available under the terms of the [Open Government 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) licence.
