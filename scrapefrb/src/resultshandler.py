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
        s = requests.Session()

        new_files = FRBDownload.compare_local(urls)
        total_files = len(new_files)

        for i, doc in enumerate(new_files):
            url = doc.get('URL')
            file_name = doc.get('File Name')

            req = requests.Request('GET', url)
            prepped = req.prepare()
            r = s.send(prepped, stream=True)
            if not(r.ok):
                FRBDownload.LOGGER.warning('ERROR (%s) retreiving %s' 
                    % (r.status_code, r.url))
                return

            file_name_abs = os.path.join(FRBDownload.PATH_NAME, file_name)

            try:
                remote_size = int(r.headers['content-length'])
            except ValueError:
                remote_size = -1

            # Download the file
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

    @classmethod
    def compare_local(cls, urls):
        FRBDownload.LOGGER.info("Comparing remote URLs to local files in %s" % 
            FRBDownload.PATH_NAME)

        existing_files = os.listdir(FRBDownload.PATH_NAME)
        files = []

        for url in urls:
            one_file = {}
            one_file['URL'] = url
            file_name = url.split('/')[-1]
            if 'aspx' in file_name.lower():
                url_query = urlparse(url)[4] # query component
                file_name = url_query.split('=')[1] # just the query value
                file_name += '_stlfrb.pdf'
            one_file['File Name'] = file_name
            files.append(one_file)

        return [doc for doc in files if doc['File Name'] not in existing_files]


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