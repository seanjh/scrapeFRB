"""    ScapeFRB is a FR-Y6 Federal Reserve Bank file scraper.
    Currently, only the Chicago FR (chicagofed.org) and Atlanta FRB (frbatlanta.org) are supported.
    This scraper will find and download all FR-Y6 filings from these supported FRB sites.

Usage:
    scrapefrb.py [-qd]
    scrapefrb.py [-qa]
    scrapefrb.py [-qa --outpath=<path>]
    scrapefrb.py [-qd --outpath=<path>]
    scrapefrb.py --outpath=<path>
    scrapefrb.py -h | --help
    scrapefrb.py --version

Options:
    -h --help       Show this help screen
    --version       Show version
    --outpath=<path> Customize the working directory (for new & existing downloads and log files)
    -q --quiet      Quiet mode (i.e., No console output).
    -d --dryrun     Dry run. Do not download any files or write logfile.
    -a --alldown    Download all files and overwrite existing copies

"""

__author__ = 'Sean J. Herman'
__version__ = '0.1'

import docopt
import logging
from lib.afrb import afrbfiler
from lib.cfrb import cfrbfiler
from lib.toolbox import filehandler

if __name__ == '__main__':
    args = docopt.docopt(__doc__, version=__version__)

    # print args
    if args['--quiet']:
        logging.basicConfig(level=logging.CRITICAL)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Create the AFRB scraper
    afrb = afrbfiler.Filer()

    # Create the CFRB scraper
    cfrb = cfrbfiler.Filer()

    filings = filehandler.FileHandler()
    if args['--outpath']:
        filings.change_working_path(args['--outpath'])
    filings.add_file_data(afrb.output_files())
    filings.add_file_data(cfrb.output_files())

    if not args['--dryrun']:
        filings.download_files(args['--alldown'])