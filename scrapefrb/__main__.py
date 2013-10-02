"""    ScapeFRB is a FR-Y6 Federal Reserve Bank file scraper.
    Currently, only the Chicago FR (chicagofed.org) and Atlanta FRB (frbatlanta.org) are supported.
    This scraper will find and download all FR-Y6 filings from these supported FRB sites.

Usage:
    scrapefrb.py [-qdlcn]
    scrapefrb.py [-qalcn]
    scrapefrb.py [-qalcn --workpath=<path>]
    scrapefrb.py [-qdlcn --workpath=<path>]
    scrapefrb.py --workpath=<path>
    scrapefrb.py -h | --help
    scrapefrb.py --version

Options:
    -h --help           Show this help screen
    --version           Show version
    --workpath=<path>   Customize the working directory (for new & existing downloads and log files)
    -q --quiet          Quiet mode (i.e., No console output).
    -d --dryrun         Execute a dry run. Do not download any files or write logfile.
    -a --alldown        Download all files and overwrite existing copies
    -n --nodown         Do not download files. A logfile will still be written.
    -c                  Include Chicago FRB.
    -l                  Include Atlanta FRB.
"""

__author__ = 'Sean J. Herman'
__version__ = '0.2.16'

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

    if args['--dryrun']:
        logging.info("Doing a dry run.")

    if args['--nodown']:
        logging.info("Skipping downloads.")

    filings = filehandler.FileHandler(args['--workpath'], args['--dryrun'], args['--nodown'])

    if args['-l'] & args['-c']:
        scrape_all = True
    elif (not args['-l']) & (not args['-c']):
        scrape_all = True
    else:
        scrape_all = False

    if args['-l'] | scrape_all:
        # Create the AFRB scraper
        afrb = afrbfiler.Filer()
        filings.add_file_data(afrb.output_files())

    if args['-c'] | scrape_all:
        # Create the CFRB scraper
        cfrb = cfrbfiler.Filer()
        filings.add_file_data(cfrb.output_files())

    filings.do_output(args['--alldown'])