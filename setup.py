from distutils.core import setup

from scrapefrb.__main__ import __version__

setup(
    name='scrapefrb',
    version=__version__,
    packages=['scrapefrb', 'scrapefrb.lib', 'scrapefrb.lib.afrb', 'scrapefrb.lib.cfrb', 'scrapefrb.lib.toolbox'],
    url='https://github.com/seanjh',
    license="MIT",
    author='Sean J. Herman',
    author_email='seanherman@gmail.com',
    description='Web scraper covering the Chicago and Atlanta FRB FR-Y6 files.',
    install_requires=['docopt', 'lxml', 'requests']
)
