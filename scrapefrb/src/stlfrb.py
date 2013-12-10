import requests
from requests import Session
import lxml.html
import logging
import sys
from urlparse import urljoin
from bankhandler import FRB

class StLouis(FRB):
    """ Contains all the FR-Y6 filing data scraped from the St. Louis FRB."""

    NAME = 'Federal Reserve Bank of St. Louis'
    URL = 'http://www.stlouisfed.org/bsr/y6/'
    DEFAULT_PAYLOAD = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
                    'Host': 'www.stlouisfed.org'
                    }
    DATE_FORMAT = ('%m/%d/%Y')
    BANK_CODE = 'S'

    def __init__(self):
        super(StLouis, self).__init__()

    def scrape(self):
        s = Session()
        self.table_headers = []

        # first request
        request_headers = {}
        for k, v in StLouis.DEFAULT_PAYLOAD.iteritems():
            request_headers[k] = v

        self.logger.info('Beginning scrape of stlouisfed.org')
        req = requests.Request('POST', StLouis.URL, headers=request_headers)
        prepped = s.prepare_request(req)
        req_payload = self._parse_table(self.table_headers, self.documents, s.send(prepped))
        self.logger.info('Initial request parsed %d rows' % len(self.documents))
        page_requests = 1


        # The "next" available pages are parsed and returned for each response
        # Keep requesting new pages while some "next" page is parsed from the response
        while (req_payload):
            req = requests.Request('POST', StLouis.URL, data=req_payload, headers=request_headers)
            prepped = s.prepare_request(req)
            req_payload = self._parse_table(self.table_headers, self.documents, s.send(prepped))
            page_requests += 1
        self.logger.info('Completed %d total page requests. Parsed %d total rows' % 
            (page_requests, len(self.documents)))

    def _map_headers(self):
        super(StLouis, self)._map_headers()
        self.key_map['URL'] = 'URL'

    def _parse_table(self, headers, data, resp=None):
        # Do a POST if one has not occurred already
        if not(resp):
            resp = requests.post(StLouis.URL)

        tree = lxml.html.fromstring(resp.text)

        # Contents of hidden forms from this response will be used in the next POST
        hidden_forms = self._get_hidden_elements(tree)
        next_payload = self._get_form_attributes(hidden_forms)

        # Grab all the table rows on this page
        all_rows = self._parse_rows(tree)

        # grab the headers
        if not(headers):
            self._parse_table_headers(tree, headers)

        for row in all_rows:
            td_contents = self._parse_table_data(row)
            if td_contents:
                # Pair into a dict each row of td_contents to the table headers
                doc = dict(zip(headers, td_contents))
                # Add this document result to the final list
                data.append(doc)

        next_pagers = self._get_pagers(tree)

        # When next_pagers is empty, we've reached the end of the content
        if next_pagers:
            # __EVENTTARGET is effectively the next piece of content, based on the
            # current state (i.e., __VIEWSTATE)
            next_payload['__EVENTTARGET'] = next_pagers[0]

            # Simulate a click by sending next link as __EVENTTARGET along with
            # the __EVENTVALIDATION and __VIEWSTATE hidden form entries collected previously
            next_payload['__EVENTARGUMENT'] = ''
        else:
            # Return None "next" payload when the "next" pager list is empty
            next_payload = None

        return next_payload

    def _get_hidden_elements(self, tree):
        # The hidden elements __VIEWSTATE and __EVENTVALIDATION are required for
        # subsequent post requests. Pull these elements from the source
        return ([e for e in tree.xpath('//input[@type="hidden"]') if 
                            '__' in e.attrib.get('name', None)])

    def _get_form_attributes(self, form_elements):
        attributes = {}

        for elem in form_elements:
                # Map the value of these hidden elements to its name
                attributes[elem.name] = elem.attrib.get('value', None)

        return attributes

    def _parse_rows(self, tree):
        return tree.xpath('body//table//tr')

    def _parse_table_headers(self, tree, headers):
        th_elements = tree.xpath('body//table//th')
        headers += [''.join(e.xpath('.//text()')) for e in th_elements]
        headers.append('URL')

    def _parse_table_data(self, tr):
        # Split the TR into its TDs. 
        # Pull text below each TD into a consolidated string.
        contents = [''.join(''.join(e.xpath('.//text()')).split()) for e in tr.xpath('.//td')]
        if contents:
            # In this row, get the first <a> where class=previewLink
            link_element = tr.xpath('.//a[@class="previewLink"]')[0]
            # Grab the href value from that <a>
            url = urljoin(StLouis.URL, link_element.attrib.get('href', None))
            # Add this URL to the contents
            contents.append(url)
            return contents
        else:
            return None

    def _get_pagers(self, tree):
        pager_div = self._get_pager_div(tree)

        next_pagers = []
        past_current_pager = False

        # The pager elements are below the <div><span> block
        # We only want the links beyond the current/active pager
        for e in pager_div.xpath('span/*'):
            if (e.tag == 'a') & past_current_pager:
                href = e.attrib.get('href', None)
                next_pagers.append(href)
            if (e.tag == 'span') & (e.attrib.get('class') == 'currentSearchPage'):
                past_current_pager = True

        # Return all strings like the one below from __doPostBack javascript <a> elements
        # ctl00$ContentPlaceHolder1$ucSearchReports$pgrSearchData$ctl00$ctl06
        return [e for page in next_pagers for e in page.split("'") if 'SearchData' in e]

    def _get_pager_div(self, tree):
        # Returns the first <div>, which containing the pagination elements
        return tree.xpath('//*[@id="searchResultsPager"]')[0]