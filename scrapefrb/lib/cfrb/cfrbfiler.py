import requests
import lxml.html
import urlparse
import logging
import time

BASE_URL = ('http://chicagofed.org/webpages/banking/financial_institution_reports/'
            'annual_report_of_bank_holding_companies.cfm')


def output_base_url():
    return BASE_URL


class Filer():
    """ Contains all the FR-Y6 filing data scraped from the Chicago FRB.
    """
    def __init__(self):
        scraper = Scraper()
        self.base_url = BASE_URL
        self.years = scraper.output_years()
        self.files = scraper.output_data()
        self.html = scraper.output_html()
        now = time.gmtime()
        self.attributes = ({"Full Name": "Chicago Federal Reserve Bank",
                            "Short Name": "CFRB",
                            "URL": BASE_URL,
                           "Total Files": len(self.files),
                           "Executed": str("%02d-%02d-%02d %02d:%02d:%02d GMT" %
                                           (now.tm_mon, now.tm_mday, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
                            })

    def output_files(self):
        if self.files:
            logging.info("Finished scraping chicagofed.org")
            return self.files
        else:
            logging.warning("No files recovered from chicagofed.org")

    def output_years(self):
        return self.years

    def refresh(self):
        self.__init__()


class Scraper():
    """
        yaddayadda
    """
    def __init__(self):
        # Get the list of years
        self.json = None
        self.html = self._request_html(BASE_URL)
        self.years, self.first_year = self._get_page_years(self.html)

        # Get the files
        self.files = self._get_files(self.years, self.first_year, self.html)

    def output_data(self):
        return self.files

    def output_years(self):
        return self.years

    def output_html(self):
        return self.html

    def _request_html(self, url, payload=dict()):
        logging.info("Beginning scrape of chicagofed.org")
        # Get the raw HTML
        tries = 0
        while tries <= 5:
            logging.info("Please wait. Loading %s... " % url),
            r = requests.get(url, params=payload)
            r.close()
            tries += 1
            if r.status_code == requests.codes.ok:
                logging.info("DONE")
                return r.text
            else:
                logging.info("No response. Retrying (%d/5)" % (tries+1))
        logging.warning("No response after 5 attempts.")

    def _get_page_years(self, html):
        parser = YearParser(html)
        return parser.get_all_years(), parser.get_current_year()

    def _get_files(self, all_years, first_year, html):
        files = self._parse_files(html, first_year)

        all_years = [y for y in all_years if y != first_year]

        # Pull the file data from the remaining pages.
        for year in all_years:
            html = self._request_year_page(year)
            files += self._parse_files(html, year)

        files = self._normalize_file_data(files)

        return files

    def _request_year_page(self, year):
        payload = {
        'SortOrderByFileName': '1',
        'SortOrder': '1',
        'CurrentYear': '2012',
        'DisplayYear': year
        }

        html = self._request_html(BASE_URL, payload)
        return html

    def _parse_files(self, html, year):
        # Get the list of files from the HTML
        page_files = FileListParser(html).get_full_list()

        # Include the Year with the file data
        for row in page_files:
            row['Report Year'] = year

        # Report on the results
        logging.info("Found %d files covering %s" % (len(page_files), year))

        return page_files

    def _normalize_file_data(self, data):
        norm_data = []

        key_mapper = {"Report Year": "Year",
                      "ID RSSD": "RSSD",
                      "File name": "Name",
                      "Date file was posted": "Date",
                      "URL": "URL"
        }

        for d in data:
            one_norm_row = {}
            for key in list(key_mapper):
                one_norm_row[key_mapper[key]] = d.pop(key)
            norm_data.append(one_norm_row)
        return norm_data


class YearParser():
    def __init__(self, html):
        """String HTML input"""
        tree = lxml.html.fromstring(html)
        self.years = self._parse_years(tree)
        self.current_year = self._parse_current_year(tree)

    def _parse_years(self, tree):
        # Get all td elements with text
        all_tds = [e for e in tree.iter(tag='td') if e.text]

        # Single out the td element that includes the text 'Display Data'
        years_td = [e for e in all_tds if 'Display Data' in e.text][0]

        # Grab the year text in each of the a (a href) elements
        years = [a.text for a in list(years_td)]

        return years

    def _parse_current_year(self, tree):
        # Find the element that includes the phrase 'Data Displayed for Year'
        year_element = [e for e in tree.iter(tag='b') if 'Data Displayed for Year' in e.text]
        return year_element[0].text[-4:]


    def get_current_year(self):
        """Returns string value, representing the current year parsed from HTML."""
        return self.current_year

    def get_all_years(self):
        """Returns a list of year values. This list represents all year values
        parsed from the HTML."""
        return self.years


class FileListParser():
    def __init__(self, html):
        tree = lxml.html.fromstring(html)
        self.file_list = self._parse_list(tree)
        self.url = ('http://chicagofed.org/webpages/banking/financial_institution_reports/'
                    'annual_report_of_bank_holding_companies.cfm')

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
                    abs_url = urlparse.urljoin(BASE_URL, td_a.attrib['href'])
                    one_row['URL'] = abs_url
                    one_row[td_label.attrib['for']] = td_a.text
            file_list.append(one_row)

        return file_list

    def get_full_list(self):
        """ Returns the full parsed list of files parsed from the remote HTML."""
        return self.file_list

    def get_length(self):
        """ Returns the length of the parsed file list. """
        return len(self.file_list)