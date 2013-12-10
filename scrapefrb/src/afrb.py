from bankhandler import FRB
import requests
import logging
import time
import json

class Atlanta(FRB):
    """ Contains all the FR-Y6 filing data scraped from the Atlanta FRB."""
    
    NAME = 'Federal Reserve Bank of Atlanta'
    URL = ('http://www.frbatlanta.org/banking/reporting/fry6/reader.cfm')
    DOC_PREFIX = ('http://www.frbatlanta.org/banking/reporting/fry6/docs/')
    DATE_FORMAT = ('%B, %d %Y %H:%M:%S')
    BANK_CODE = 'A'

    def __init__(self):
        super(Atlanta, self).__init__()

    def scrape(self):
        json = {}
        session = requests.Session()
        years = self._get_years(session)
        if years:
            self._parse_files(years, session)
        if self.documents:
            self.table_headers = list(self.documents[0])

    def _get_years(self, session):
        # Announce the commencement of the scraper
        self.logger.info("Beginning scrape of frbatlanta.org")

        # Get the list of years from the YearParser
        tail_url = '?{%22reader%22:%22getYearList%22}'
        full_url = Atlanta.URL + tail_url
        req = requests.Request('GET', full_url)
        prepped = req.prepare()
        resp = session.send(prepped)
        if resp.ok:
            return [str(y) for y in resp.json()]

    def _parse_files(self, years, session):
        # Request new JSON for each year, and parse the JSON
        for year in years:
            full_url = self._compose_full_url(year)
            raw_json = self._get_json(full_url, session)
            if raw_json:
                self._parse_json_docs(raw_json)
        if self.documents:
            self._add_urls()

        self.logger.info("Parsed %d files from frbatlanta.org" % len(self.documents))

    def _get_json(self, full_url, session):
        self.logger.info("Please wait. Loading %s... " % full_url)
        req = requests.Request('GET', full_url)
        prepped = req.prepare()
        resp = session.send(prepped)

        if resp.ok:
            return resp.json()
        else:
            self.logger.warning("No response")

    def _parse_json_docs(self, raw_json):
        # Parse out the columns
        columns = [str(c) for c in raw_json['COLUMNS']]

        for row in raw_json['DATA']:
            clean_row = [str(e) for e in row]
            self.documents.append(dict(zip(columns, clean_row)))

    def _add_urls(self):
        for doc in self.documents:
            doc['URL'] = (Atlanta.DOC_PREFIX + doc['FILENAME'])

    def _compose_full_url(self, year):
        url = (Atlanta.URL + 
            '?{%22reader%22:%22getDocs%22,%22dataStruct%22:{%22docyear%22:%22'+ 
            str(year)+'%22}}')
        return url