from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-highlighting',
	version=version,
	description="solr highlighting plugins for CKAN",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Esra Uenal',
	author_email='esra.uenal@fokus.fraunhofer.de',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.highlighting'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
    
    	[ckan.plugins]
    	solr_highlighting=ckanext.highlighting.search_api:HighlightingSearchApi

	""",
)
