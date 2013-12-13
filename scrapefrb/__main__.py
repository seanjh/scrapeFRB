"""ScapeFRB is a web scraper that crawls and collects FR Y-6 documents from
    several US Federal Reserve Bank branch websites. Currently supported:
        * Chicago (https://www.chicagofed.org/webpages/banking/financial_institution_reports/annual_report_of_bank_holding_companies.cfm) 
        * Atlanta (http://www.frbatlanta.org/banking/reporting/fry6/)
        * St. Louis (http://www.stlouisfed.org/bsr/y6/)

Usage:
    scrapefrb [-a]
    scrapefrb [-a --workpath=<path>]
    scrapefrb --workpath=<path>
    scrapefrb -h | --help
    scrapefrb --version

Options:
    -h --help           Show this help screen.
    --version           Show version.
    --workpath=<path>   Customize the working/output directory.
    -a --alldown        Download all files. By default, only new files are downloaded.
"""

__author__ = 'Sean J. Herman'
__version__ = '0.5.0'

import docopt
import os
import sys
from src import frblogger
from src.bankhandler import FRB
from src.stlfrb import StLouis
from src.cfrb import Chicago
from src.afrb import Atlanta

OUTPUT_DIRECTORIES = ['', 'downloads']

def main():
    args = docopt.docopt(__doc__, version=__version__)

    if args['--alldown']:
        FRB.set_download_all()

    if args['--workpath']:
        working_path = args['--workpath']
    else:
        working_path = get_default_path()

    try:
        logger = frblogger.configure_logger('root', working_path)
    except IOError as e:
        print(e)
        sys.exit(0)

    for directory in OUTPUT_DIRECTORIES:
        this_path = os.path.join(working_path, directory)
        this_path = os.path.abspath(this_path)
        if not(os.path.exists(this_path)):
            logger.info('Making %s' % this_path)
            os.mkdir(this_path)

    if not(os.path.exists(working_path)):
        os.mkdir(working_path)

    FRB.set_working_path(working_path)

    frbs = [StLouis(), Chicago(), Atlanta()]
    
    for f in frbs:
        if f.documents:
            f.insert()
            f.download()
        else:
            logger.warning("No documents found at %s" % f.URL)

def get_default_path():
    if getattr(sys, 'frozen', False):
        working_path = os.path.dirname(sys.executable)
    else:
        working_path = os.path.dirname(__file__)
        working_path = os.path.abspath(os.path.join(working_path, '..'))

    return working_path

if __name__ == '__main__':
    main()