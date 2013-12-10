## Introduction
**Author:** Sean J. Herman

The ScrapeFRB application serves as a specialized web scraper of FRY-6 files
from the Chicago, Atlanta, and St.Louis Federal Reserve Bank (FRB) web sites.
More detailed instructions on usage are available after installation via --help
flag. Documents are downloaded by default into the script's working directory,
but a custom working directory for downloads may be provided on the command
line.

## Prerequisites

* [lxml](https://github.com/lxml/lxml)
* [docopt](https://github.com/docopt/docopt)
* [requests](https://github.com/kennethreitz/requests)


### Installation
    easy_install scrapefrb