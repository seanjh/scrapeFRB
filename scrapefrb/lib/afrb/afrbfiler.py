import requests
import logging
import time

BASE_URL = 'http://www.frbatlanta.org/banking/reporting/fry6/reader.cfm'
DOC_URL = 'https://www.frbatlanta.org/banking/reporting/fry6/docs/'


def output_base_url():
    return BASE_URL


def output_doc_url():
    return DOC_URL


class Filer():
    """ Contains all the FR-Y6 filing data scraped from the Chicago FRB.
    """
    def __init__(self):
        scraper = Scraper()
        self.base_url = BASE_URL
        self.years = scraper.output_years()
        self.files = scraper.output_data()
        self.html = None
        self.json = scraper.output_json()
        now = time.gmtime()
        self.attributes = ({"Full Name": "Atlanta Federal Reserve Bank",
                            "Short Name": "AFRB",
                            "URL": BASE_URL,
                           "Total Files": len(self.files),
                           "Executed": str("%02d-%02d-%02d %02d:%02d:%02d GMT" %
                                           (now.tm_mon, now.tm_mday, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
                            })

    def output_files(self):
        if self.files:
            #self.log.info("Finished scraping frbatlanta.org")
            logging.info("Finished scraping frbatlanta.org")
            return self.files
        else:
            #self.log.warning("No files recovered from frbatlanta.org")
            logging.warning("No files recovered from frbatlanta.org")

    def output_years(self):
        return self.years

    def refresh(self):
        self.__init__()


class Scraper():
    def __init__(self):
        # Get the list of years
        self.json = {}
        self.years = self._get_years()

        # Get the files
        self.files = self._get_files(self.years)
        #self.log = logging.getLogger("AFRBScraper")

    def output_data(self):
        return self.files

    def output_years(self):
        return self.years

    def output_json(self):
        return self.json

    def _get_files(self, years):
        if years:
            raw_files = self._get_file_data(years)
            files = self._normalize_file_data(raw_files)
            return files

    def _get_years(self):
        # Announce the commencement of the scraper
        logging.info("Beginning scrape of frbatlanta.org")

        # Get the list of years from the YearParser
        p = YearParser()
        return p.output_years()

    def _get_file_data(self, year_list):
        # Create the file list parser
        p = FileParser(year_list)

        # Preserve the JSON
        self.json = p.output_raw_json()

        # Get the parsed list of files
        files = p.output_file_list()
        return files

    def _normalize_file_data(self, data):
        norm_data = []
        key_mapper = {"DOCYEAR": "Year",
                      "DOCRSSD": "RSSD",
                      "DOCINSTNAME": "Name",
                      "FILEDATE": "Date",
                      "URL": "URL"
        }
        for d in data:
            one_norm_row = {}
            for key in list(key_mapper):
                one_norm_row[key_mapper[key]] = d.pop(key)
            norm_data.append(one_norm_row)
        return norm_data


class YearParser():
    """ YearParser parses the available year values from the Atlanta FRB FR Y-6 page."""
    def __init__(self):
        self.tail_url = '?{%22reader%22:%22getYearList%22}'
        self.full_url = BASE_URL + self.tail_url
        self.years = [str(y) for y in self._request_years()]
        #self.log = logging.getLogger("AFRBYearParser")

    def _request_years(self):
        r = requests.get(self.full_url)
        return r.json()

    def output_full_url(self):
        return self.full_url

    def output_years(self):
        """ Returns the list of year values as a list of strings."""
        return self.years


class FileParser():
    """ FileParser translates a list of year values into a list of files for the given years.
    """
    def __init__(self, year_list):
        """ Year list input. """
        self.raw_json = {}
        self.doc_prefix = 'https://www.frbatlanta.org/banking/reporting/fry6/docs/'
        self.file_list = self._parse_files(year_list)
        #self.log = logging.getLogger("AFRBFileParser")

    def _parse_files(self, year_list):
        file_data = []
        for y in year_list:
            file_data += self._parse_year(y)
        file_data = self._add_urls(file_data)
        return file_data

    def _parse_year(self, year_str):
        # Get the raw JSON
        full_url = self._compose_full_url(year_str)
        self.raw_json = self._get_json(full_url)

        # Parse the file data from JSON.
        file_data = self._clean_json(self.raw_json)

        # Report on the results
        # self.log.info("Found %d files covering %s\n" % (len(file_data), year_str))
        logging.info("Found %d files covering %s\n" % (len(file_data), year_str))

        return file_data

    def _get_json(self, full_url):
        # Get the raw JSON
        tries = 0
        while tries <= 5:
            # self.log.info("Please wait. Loading %s... " % full_url),
            logging.info("Please wait. Loading %s... " % full_url),
            r = requests.get(full_url)
            r.close()
            tries += 1
            if r.status_code == requests.codes.ok:
                #self.log.info("DONE")
                logging.info("DONE")
                return r.json()
            else:
                #self.log.info("No response. Retrying (%d/5)" % (tries+1))
                logging.info("No response. Retrying (%d/5)" % (tries+1))
        #self.log.warning("No response after 5 attempts.")
        logging.warning("No response after 5 attempts.")

    def _clean_json(self, raw_json):
        # Parse out the columns
        columns = [str(c) for c in raw_json['COLUMNS']]

        data = []
        # Parse out the rows, and pair with columns in a new dict
        for row in raw_json['DATA']:
            clean_row = [str(e) for e in row]
            data.append(dict(zip(columns, clean_row)))
        return data

    def _add_urls(self, data_list):
        # Include URL with each entry
        for row in data_list:
            row['URL'] = self.doc_prefix + row['FILENAME']
        return data_list

    def output_file_list(self):
        """ Returns the full parsed list of files parsed from the remote HTML."""
        return self.file_list

    def _compose_full_url(self, year_str):
        url = (BASE_URL + '?{%22reader%22:%22getDocs%22,%22dataStruct%22:{%22docyear%22:%22'+str(year_str)+'%22}}')
        return url

    def output_raw_json(self):
        return self.raw_json