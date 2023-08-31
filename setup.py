from setuptools import setup, find_packages
import sys, os

version = '3.7'

setup(
	name='ckanext-highlighting',
	version=version,
	description="solr highlighting plugin for CKAN",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Fachliche Leitstelle Transparenzportal, Hamburg, Germany; Esra Uenal FOKUS, Fraunhofer Berlin, Germany',
	author_email='transparenzportal@kb.hamburg.de',
	url='http://transparenz.hamburg.de/',
	license='AGPL',
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
    	fast_search_solr_highlighting=ckanext.highlighting.package_fast_search_api:FastSearchApi

	""",
)
