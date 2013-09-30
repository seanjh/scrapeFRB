import os
import logging
import cleanpath
import download
import csv


class FileHandler():
    def __init__(self):
        self.file_data = []
        self.totalfilers = 0
        self.workingdir = self._add_default_path()
        self.logfilename = self._set_log_filename(self.workingdir)
        self.old_data = self._read_old_file(self.output_working_dir(), self.output_filename())
        self.new_data = []
        self.outputCSV = True
        self.outputXML = False

    def add_file_data(self, files):
        if files:
            logging.info("Adding %d new files" % len(files))
            self.file_data += files
            self.totalfilers += 1
        # Update old data by diffing new expanded self.file_data to existing old_data
        self.new_data = self._diff_data(self.old_data, self.file_data)

    def output_file_data(self):
        return self.file_data

    def output_new_files(self):
        return self.new_data

    def output_filename(self):
        return self.logfilename

    def output_working_dir(self):
        return self.workingdir

    def list_urls(self, datadict):
        return [row['URL'] for row in datadict]

    def download_files(self, downloadall):
        # Write new log file
        if self.outputCSV:
            self._output_csv(self.output_file_data(), self.output_working_dir(), self.output_filename())
        elif self.outputXML:
            pass
        if downloadall:
            self.download_all_files()
        else:
            self.download_new_files()

    def download_new_files(self):
        urls = self.list_urls(self.new_data)
        if urls:
            logging.info("Downloading new files to %s" % self.workingdir)
            download.download_list(urls, out_path=self.workingdir)
        else:
            logging.info("No new files to download!")

    def download_all_files(self):
        urls = self.list_urls(self.file_data)

        if urls:
            logging.info("Downloading all files to %s" % self.output_working_dir())
            download.download_list(urls, out_path=self.workingdir)
        else:
            logging.WARNING("No files scraped!")

    def _output_csv(self, datalist, filepath, filename):
        filename = os.path.join(self.workingdir, self.logfilename)
        logging.info("Writing new logfile to %s ..." % filename),

        csv_headers = self.output_file_data_headers()

        with open(filename, 'wb') as csv_file:
            dw = csv.DictWriter(csv_file, csv_headers)
            dw.writeheader()
            dw.writerows(self.file_data)
        logging.info("DONE")

    def change_working_path(self, path):
        # If path is a list, make it a string
        if cleanpath.path_is_list(path):
            path = os.path.join(*path)

        # Make path absolute
        path = os.path.abspath(path)

        # Update the instance workdir value
        logging.info('Changing output directory to %s' % path)
        self.workingdir = path

        # Make this new path if it does not exist already
        cleanpath.check_path_make(path)

        self.old_data = self._read_old_file(self.output_working_dir(), self.output_filename())

    def output_file_data_headers(self):
        return list(self.file_data[0])

    def _compare_old_to_new(self):
        # Read existing logfile. Empty list is returned if there is no previous log.
        old_data = self._read_old_file(self.output_working_dir(), self.output_filename())

        # create list of new results not in previous file
        new_files = self._diff_data(old_data, self.output_file_data())
        return new_files

    def _read_old_file(self, path, filename):
        olddata = []

        # Open existing log file
        logfile = os.path.join(path, filename)

        # Read in the existing CSV, if it exists
        if cleanpath.path_exists(logfile):
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
        # Path for filehandler.py
        thisfilepath = str(os.path.realpath(__file__))

        # Convert path to a list
        workingpath = cleanpath.path_to_list(thisfilepath)

        # Drop down 3 relative levels (file + 2 directories)
        workingpath.pop()
        workingpath.pop()
        workingpath.pop()

        # Locate output to ../../output
        workingpath.append('output')

        # Check if the directory exists. If not, create it.
        cleanpath.check_path_make(workingpath)
        return os.path.join(*workingpath)

    def _set_log_filename(self, path):
        file = 'ScrapeFRB_log.csv'
        return file