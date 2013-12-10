from bankhandler import FRB
import requests
import logging
import lxml.html
import urlparse

class Chicago(FRB):
    """ Contains all the FR-Y6 filing data scraped from the Chicago FRB."""
    
    NAME = 'Federal Reserve Bank of Chicago'
    URL = ('http://www.chicagofed.org/webpages/banking/'
        'financial_institution_reports/annual_report_of_bank_holding_companies.cfm')
    DATE_FORMAT = ('%m/%d/%Y')
    BANK_CODE = 'C'

    def __init__(self):
        super(Chicago, self).__init__()
        self.years = None
        self.first_year = None

    def scrape(self):
        # Request the first page
        html = self._request_html()

        # Get the list of years
        self._get_page_years(html)

        # Given years, parse the file listings for each year
        self._get_files(html)

    def _request_html(self, payload=dict()):
        self.logger.info("Beginning scrape of chicagofed.org")
        # Get the raw HTML
        tries = 0
        while tries <= 5:
            self.logger.info("Please wait. Loading %s... " % Chicago.URL),
            r = requests.get(Chicago.URL, params=payload)
            r.close()
            tries += 1
            if r.status_code == requests.codes.ok:
                self.logger.info("DONE")
                return r.text
            else:
                self.logger.info("No response. Retrying (%d/5)" % (tries+1))
        self.logger.warning("No response after 5 attempts.")

    def _get_page_years(self, html):
        tree = lxml.html.fromstring(html)
        self._parse_years(tree)
        self._parse_current_year(tree)

    def _parse_years(self, tree):
        # Get all td elements with text
        all_tds = [e for e in tree.iter(tag='td') if e.text]

        # Single out the td element that includes the text 'Display Data'
        years_td = [e for e in all_tds if 'Display Data' in e.text][0]

        # Grab the year text in each of the a (a href) elements
        self.years = [a.text for a in list(years_td)]

    def _parse_current_year(self, tree):
        # Find the element that includes the phrase 'Data Displayed for Year'
        year_element = [e for e in tree.iter(tag='b') if 'Data Displayed for Year' in e.text]
        self.first_year = year_element[0].text[-4:]

    def _get_files(self, html):
        # Parse the documents from the first page's HTML
        self._parse_files(html, self.first_year)
        
        if self.documents:
            self.table_headers = list(self.documents[0])

        # Exclude first year from the remaining years to request
        remaining_years = [y for y in self.years if y != self.first_year]

        # Request a new page for each year, and parse its files
        for year in remaining_years:
            html = self._request_year_page(year)
            self._parse_files(html, year)

    def _request_year_page(self, year):
        payload = {
        'SortOrderByFileName': '1',
        'SortOrder': '1',
        'CurrentYear': '2012',
        'DisplayYear': year
        }

        html = self._request_html(payload)
        return html

    def _parse_files(self, html, year):
        # Get the list of files from the HTML
        tree = lxml.html.fromstring(html)
        page_files = self._parse_list(tree)

        # Include the Year with the file data
        for row in page_files:
            row['Report Year'] = year

        # Report on the results
        if page_files:
            self.logger.info("Found %d files covering %s" % (len(page_files), year))
            # Append the new documents
            self.documents += page_files
        else:
            self.logger.warning("No files parsed for %s from %s" % (year, Chicago.URL))

    def _parse_list(self, tree):
        valid_for_label = ['File name', 'ID RSSD', 'Date file was posted']

        # Harvest TR elements that contain file data.
        all_trs = [e for e in tree.iter(tag='tr')]
        # Relevant TRs have TD child, with a valid 'for' attribute (in valid_for_label)
        doc_trs = [e for e in all_trs if list(e)[0].tag == 'td'  # TR child
                   and list(list(e)[0])[0].tag == 'label'  # TR grandchild
                   and list(list(e)[0])[0].attrib['for'] in valid_for_label]

        # Reconstitute this table as a list of dicts
        file_list = []
        for tr in doc_trs:
            one_row = {}
            # Compose a dict for each row
            for td in tr:
                td_label = list(td)[0]  # The first TD child element should be a label.
                if td_label.text:
                    one_row[td_label.attrib['for']] = td_label.text
                else:
                    # When it doesn't have text, then <label>'s first child is <a>
                    # When <label> has a child, text is inside that element.
                    td_a = list(td_label)[0]
                    abs_url = urlparse.urljoin(Chicago.URL, td_a.attrib['href'])
                    one_row['URL'] = abs_url
                    one_row[td_label.attrib['for']] = td_a.text
            file_list.append(one_row)

        return file_list