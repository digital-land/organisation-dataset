# Digital Land collection of organisations

[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/psd/openregister/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/en/stable/)

A collection of data about Local Planning Authorities and other organisations who publish data used by digital land:

* [collection/organisation.csv](collection/organisation.csv)

The list of organisations is assembled from the following registers:

* [government-organisation](https://government-organisation.register.gov.uk)
* [local-authority-eng](https://local-authority-eng.register.gov.uk)

and combined with the following registers to provide statistical geographies:

* [statistical-geography-county-eng](https://statistical-geography-county-eng.register.gov.uk)
* [statistical-geography-london-borough-eng](https://statistical-geography-london-borough-eng.register.gov.uk)
* [statistical-geography-metropolitan-district-eng](https://statistical-geography-metropolitan-district-eng.register.gov.uk)
* [statistical-geography-non-metropolitan-district-eng](https://statistical-geography-non-metropolitan-district-eng.register.gov.uk)
* [statistical-geography-unitary-authority-eng](https://statistical-geography-unitary-authority-eng.register.gov.uk)

The data is matched against [https://opendatacommunities.org](https://opendatacommunities.org/home).

This locally maintained dataset provides websites for local authorities, development corporations not yet listed on GOV.UK, and other missing values:

* [data/organisations.csv](data/organisations.csv)

The plan is to move to replace this locally maintained data with the website, and other data sourced from Wikipedia, such as https://www.wikidata.org/wiki/Q931180

# Updating the collection

We recommend working in [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) before installing the python dependencies:

    $ make init
    $ make

# Licence

The software in this project is open source and covered by LICENSE file.

Individual datasets copied into this repository may have specific copyright and licensing, otherwise all content and data in this repository is
[© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
and available under the terms of the [Open Government 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) licence.
