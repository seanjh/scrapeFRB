__author__ = 'sherman'
# downloader.py
# by Sean J. Herman

import urllib
import urllib2
import os
import sys


def stitch_url(fname, url_prefix):
    u = url_prefix.split('/')
    if not u[-1]:  # yank trailing slash
        u.pop(-1)
    if '.' in u[-1]:  # yank trailing filename
        u.pop(-1)
    f = fname.split('/')[-1]
    u.append(f)
    return '/'.join(u)


def clean_url(url):
    split_url = url.split('/')
    new_url = [urllib.quote(part) for part in split_url[1:]]
    new_url.insert(0, split_url[0])  # re-include protocol
    return '/'.join(new_url)


def download_list(files, url_prefix='', out_path=os.getcwd()):
    if url_prefix:
        files = [stitch_url(file_name, url_prefix) for file_name in files]
    for one_file in files:
        download_one(one_file, out_path)


def download_one(url, out_path=os.getcwd()):
    # compose full url and file path
    file_name = url.split('/')[-1]
    out_file = os.path.join(out_path, file_name)

    # open download file, prepare download handlers
    with open(out_file, 'wb') as df:
        block, file_size = 8192, 0  # 8KB blocks
        try:
            u = urllib2.urlopen(clean_url(url))
            metadata = u.info()
            url_size = int(metadata['content-length'])
            while True:
                data_buffer = u.read(block)
                if not data_buffer:
                    break
                df.write(data_buffer)
                file_size += len(data_buffer)
                sys.stdout.write('\r %s: %d/%d KB (%0.0f%%) ... ' %
                                 (file_name, file_size, url_size, file_size * 100. / url_size)),
            u.close()
            sys.stdout.write('Done\n')
        except:
               sys.stdout.write('Download failed!\n')