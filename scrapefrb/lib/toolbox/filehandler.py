import os
import sys
import logging
import download
import csv


class FileHandler():
    def __init__(self, path='', dry_run=False, no_down=False):
        self.file_data = []
        self.total_filers = 0
        self.dry_run = dry_run
        self.download = (not no_down)
        if path:
            self.working_path = self.change_working_path(path)
        else:
            self.working_path = self._add_default_path()
        self.log_filename = self._set_log_filename(self.working_path)
        self.old_data = self._read_old_file(self.output_working_dir(), self.output_filename())
        self.new_data = []
        self.output_csv = True
        self.output_xml = False

    def add_file_data(self, files):
        if files:
            logging.info("Adding %d new files" % len(files))
            self.file_data += files
            self.total_filers += 1
        # Update old data by diffing new expanded self.file_data to existing old_data
        self.new_data = self._diff_data(self.old_data, self.file_data)

    def output_file_data(self):
        return self.file_data

    def output_new_files(self):
        return self.new_data

    def output_filename(self):
        return self.log_filename

    def output_working_dir(self):
        return self.working_path

    def has_data(self):
        return self.file_data

    def list_urls(self, datadict):
        return [row['URL'] for row in datadict]

    def do_output(self, download_all):
        if self.dry_run:
            return
        elif self.download:
            self._download_files(download_all)
        else:
            self._write_log()

    def _download_files(self, download_all):
        # Write new log file (or not)
        self._write_log()

        if download_all:
            self.download_all_files()
        else:
            self.download_new_files()

    def _write_log(self):
        if self.output_csv:
            self._output_csv(self.output_file_data(), self.output_working_dir(), self.output_filename())
        if self.output_xml:
            pass

    def download_new_files(self):
        urls = self.list_urls(self.new_data)
        if urls:
            logging.info("Downloading new files to %s" % self.working_path)
            download.download_list(urls, out_path=self.working_path)
        else:
            logging.info("No new files to download!")

    def download_all_files(self):
        urls = self.list_urls(self.file_data)

        if urls:
            logging.info("Downloading all files to %s" % self.output_working_dir())
            download.download_list(urls, out_path=self.working_path)
        else:
            logging.WARNING("No files scraped!")

    def change_working_path(self, input_path):
        # Make path absolute
        input_path = os.path.abspath(input_path)

        # Update the instance working_path value
        logging.info('Changing output directory to %s' % input_path)

        # Make this new path if it does not exist already
        if (not os.path.exists(input_path)) & (not self.dry_run):
            os.mkdir(input_path)

        return input_path

    def output_file_data_headers(self):
        return list(self.file_data[0])

    def _output_csv(self, datalist, filepath, filename):
        working_path = os.path.join(filepath, 'log')

        logging.info("Checking for the existence of %s", working_path)
        if (not os.path.exists(working_path)) & (not self.dry_run):
            logging.info("Creating %s", working_path)
            os.mkdir(working_path)

        full_file_path = os.path.join(filepath, 'log', filename)
        logging.info("Writing new logfile to %s ..." % full_file_path),

        csv_headers = self.output_file_data_headers()

        with open(full_file_path, 'wb') as csv_file:
            dw = csv.DictWriter(csv_file, csv_headers)
            dw.writeheader()
            dw.writerows(datalist)
        logging.info("DONE")

    def _compare_old_to_new(self):
        # Read existing logfile. Empty list is returned if there is no previous log.
        old_data = self._read_old_file(self.output_working_dir(), self.output_filename())

        # create list of new results not in previous file
        new_files = self._diff_data(old_data, self.output_file_data())
        return new_files

    def _read_old_file(self, path, filename):
        olddata = []

        # Open existing log file
        logfile = os.path.join(path, 'log', filename)

        # Read in the existing CSV, if it exists
        if os.path.exists(logfile):
            logging.info("Opening existing log file at %s" % logfile)
            with open(logfile, 'r') as infile:
                dictreader = csv.DictReader(infile)
                for row in dictreader:
                    olddata.append(row)
        else:
            logging.info("No existing log file at %s" % logfile)
        return olddata

    def _diff_data(self, oldlist, newlist):
        logging.info("Comparing old data against new data.")
        diff = [data for data in newlist if data not in oldlist]
        logging.info("Comparison completed. Found %d new files." % len(diff))
        return diff

    def _add_default_path(self):
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            workingpath = os.path.dirname(sys.executable)
        else:
            workingpath = os.path.dirname(__file__)
            workingpath = self._prep_script_path(workingpath)

        # Locate output to the output/ directory
        workingpath = os.path.join(workingpath, 'output')

        logging.info("Checking for the existence of %s", workingpath)

        # Check if the directory exists. If not, create it.
        if (not os.path.exists(workingpath)) & (not self.dry_run):
            logging.info("Creating %s", workingpath)
            os.mkdir(workingpath)
        return workingpath

    def _prep_script_path(self, pathstr):
        # Drop down 2 directories
        return os.path.abspath(os.path.join(pathstr, '..', '..'))

    def _set_log_filename(self, path):
        file = 'ScrapeFRB_log.csv'
        return file