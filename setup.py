try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from scrapefrb.__main__ import __version__

setup(
    name='scrapefrb',
    version=__version__,
    packages=['scrapefrb', 'scrapefrb.src'],
    url='https://github.com/seanjh',
    license='MIT',
    author='Sean J. Herman',
    author_email='seanherman@gmail.com',
    description='Federal Reserve Bank FR Y-6 filing web scraper.',
    install_requires=['docopt', 'lxml', 'requests >= 2.0.1', 'sqlite3']
)