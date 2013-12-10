import sqlite3
import time
import os
import sys
import logging
import requests
from urllib import quote
from urlparse import urlparse

class FRBDB(object):
    LOGGER = logging.getLogger('root')

    FILE_NAME = 'frb_files.db'

    TABLE = 'fry6'

    COLUMN_MAP = {
        'RSSD': 'rssd_id',
        'Name': 'company',
        'Date': 'date',
        'Year': 'year',
        'URL':  'url'
    }

    COLUMN_ORDER = [
        'RSSD',
        'Name',
        'Date',
        'Year',
        'URL'
    ]

    CREATE_STATEMENT = ('''
        CREATE TABLE IF NOT EXISTS %s
        (doc_id integer PRIMARY KEY AUTOINCREMENT,
        rssd_id integer, 
        company text,
        date text,
        year integer,
        url text,
        insert_date text,
        frb_code text,
        UNIQUE (rssd_id, year, company))
        ''' % (TABLE)
    )

    INSERT_STATEMENT = ('''
        INSERT INTO %s 
        (doc_id, rssd_id, company, date, year, url, insert_date, frb_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''' % (TABLE)
    )

    SELECT_STATEMENT = ('''
        SELECT doc_id, rssd_id, company, date, year, url, insert_date, frb_code FROM %s
        ''' % (TABLE)
    )

    @classmethod
    def set_working_path(cls, path):
        cls.FILE_NAME = os.path.join(path, cls.FILE_NAME)
        #print cls.FILE_NAME

    def __init__(self):
        self.conn = sqlite3.connect(FRBDB.FILE_NAME)
        self.curs = self.conn.cursor()

        self.timestamp = time.time()
        self._old_documents = None
        self.create()
        self._fetch_old_documents()

    @property
    def old_documents(self):
        return self._old_documents

    @property
    def old_id_pairs(self):
        if self._old_documents:
            return [(row[1], row[2], row[4]) for row in self._old_documents]

    def create(self):
        self.curs.execute(FRBDB.CREATE_STATEMENT)

    def insert_data(self, data, key_map=None, bank_code=''):
        if key_map:
            data = self.prepare_keyed_data(data, key_map, bank_code)

        for datum in data:
            try:
                self.curs.execute(FRBDB.INSERT_STATEMENT, datum)
            except sqlite3.IntegrityError:
                raise sqlite3.IntegrityError(datum)
            self.conn.commit()

    def prepare_keyed_data(self, data, key_map, code):
        temp = []

        # Arrange the data columns the database column order
        mapped_columns = [key_map[col] for col in FRBDB.COLUMN_ORDER]

        for datum in data:
            # build each insert record
            this_record = [None] # doc_id place holder
            this_record += [datum[column] for column in mapped_columns] # ordered columns
            this_record.append(self.timestamp)
            this_record.append(code)
            temp.append(tuple(this_record)) # convert to tuple
        return temp

    def _fetch_old_documents(self):
        self._old_documents = self.curs.execute(FRBDB.SELECT_STATEMENT).fetchall()

class FRBDownload(object):
    LOGGER = logging.getLogger('root')

    PATH_NAME = 'downloads'
    CHUNK_SIZE = 8192 # 8KB

    @classmethod
    def download(cls, urls):
        existing_files = os.listdir(FRBDownload.PATH_NAME)

        total_files = len(urls)
        FRBDownload.LOGGER.info('Checking %d total files.' % total_files)

        for i, url in enumerate(urls):
            # Request the headers
            r = requests.get(url, stream=True)
            if not(r.ok):
                FRBDownload.LOGGER.warning('ERROR (%s) retreiving %s' 
                    % (r.status_code, r.url))
                break

            # Construct the filename if the URL doesn't provide something workable
            file_name = url.split('/')[-1]
            if 'aspx' in file_name.lower():
                file_name = FRBDownload.make_filename(r.headers)

            file_name_abs = os.path.join(FRBDownload.PATH_NAME, file_name)

            try:
                remote_size = int(r.headers['content-length'])
            except ValueError:
                remote_size = -1

            # If the file exists already, get its size
            local_size = 0

            # Download if the file does not exist, or is smaller than the remote
            if file_name not in existing_files:
                with open(file_name_abs, 'wb') as outfile:
                    local_size = 0
                    for chunk in r.iter_content(chunk_size=FRBDownload.CHUNK_SIZE):
                        local_size += len(chunk)
                        sys.stdout.write('\rDownloading file #%d/%d. Completed: %d%%' % 
                            (i + 1, total_files, 100.0 * local_size / remote_size))
                        sys.stdout.flush()
                        outfile.write(chunk)
                    sys.stdout.write('\n')
                FRBDownload.LOGGER.info('Finished Downloading %s (%d)' 
                    % (file_name, remote_size))
            #else:
                #FRBDownload.LOGGER.info('%s exists already (%dB). Skipping download.' % 
                    #(file_name, local_size))

    @classmethod
    def set_working_path(cls, path):
        cls.PATH_NAME = os.path.join(path, cls.PATH_NAME)
        #print cls.PATH_NAME

    @classmethod
    def make_filename(cls, headers):
        for key, value in headers.iteritems():
            if '.pdf' in value.lower():
                return value.split('=')[-1]


    def __init__(self):
        pass