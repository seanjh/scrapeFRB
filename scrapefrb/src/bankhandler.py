import logging
import sqlite3
import time
import logging
import os
from datetime import datetime
from resultshandler import FRBDB, FRBDownload


class FRB(object):
    """Bank objects represent a single Federal Reserve branch bank.
    """
    DATE_FORMAT = None
    BANK_CODE = None
    DB = FRBDB()
    WORK_PATH = None
    DOWNLOAD_ALL = False

    @classmethod
    def set_working_path(cls, path):
        cls.WORK_PATH = path
        #print cls.WORK_PATH
        FRBDB.set_working_path(path)
        FRBDownload.set_working_path(path)

    @classmethod
    def set_download_all(cls):
        cls.DOWNLOAD_ALL = True

    def __init__(self):
        self.documents = []
        self.new_documents = []
        self.table_headers = []
        self.key_map = {}
        
        self.logger = logging.getLogger('root')

        self.scrape()
        if self.documents:
            self._normalize()
            self.compare()
        #self.insert()
        #self.download()

    def scrape(self):
        pass

    def compare(self):
        old_pairs = FRB.DB.old_id_pairs
        self.new_documents = []

        if old_pairs:
            self.logger.info('Fetched %d old documents' % len(old_pairs))
            for d in self.documents:
                new_pair = (d[self.key_map.get('RSSD')], d[self.key_map.get('Name')], d[self.key_map.get('Year')])
                if new_pair not in old_pairs:
                    self.new_documents.append(d)
            self.logger.info('Located %d total new documents for insert' % len(self.new_documents))
        else:
            self.new_documents = self.documents
            self.logger.info('No old documents fetched. All %d documents flagged as new' % len(self.new_documents))

    def _normalize(self):
        self._map_headers()
        self._normalize_dates()
        
    def _map_headers(self):
        # Pair generic headers with the site-specific header text
        if self.table_headers:
            # FRBDB.COLUMN_MAP contain the generic column names
            for key, value in FRBDB.COLUMN_MAP.iteritems():
                for column in self.table_headers:
                    if key.lower() in column.lower():
                        self.key_map[key] = column
                        break

    def _normalize_dates(self):
        date_key = self.key_map.get('Date')
        for doc in self.documents:
            # Convert date string to datetime object
            doc[date_key] = datetime.strptime(doc.get(date_key), self.DATE_FORMAT)

    def insert(self):
        self.logger.info('Inserting %d records' % len(self.new_documents))
        start = time.time()
        try:
            FRB.DB.insert_data(self.new_documents, self.key_map, self.BANK_CODE)
        except sqlite3.IntegrityError as e:
            self.logger.warning('Caught SQLite3 IntegrityError')
            self.logger.warning(e)
        stop = time.time()
        diff = stop - stop
        diff = stop - start
        try:
            rows_per_second = 1.0 * len(self.new_documents) / diff
            self.logger.info('Finished batch insert in %0.4f seconds (%d rows/second)' % 
                (diff, rows_per_second))
        except ZeroDivisionError as e:
            self.logger.warning(e)
            self.logger.warning('Insert warning. Possible loss of data.')

    def download(self):
        if FRB.DOWNLOAD_ALL:
            downloads = self.documents
        else:
            downloads = self.new_documents

        url_key = self.key_map.get('URL')
        FRBDownload.download([doc[url_key] for doc in downloads])