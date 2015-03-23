=================
ckan-highlighting
=================
|

An action API function for extending the functionality provided by the action API function package_search by allowing solr highlighting query parameters.
The highlighted text returned by solr will be added to package extras.

|

Installation
============
|

1. Install the extension into your python environment::

   (pyenv) $ pip install -e git+https://race.informatik.uni-hamburg.de/inforeggroup/ckanext-highlighting.git@egg=ckanext-highlighting


2. Add the plugin to the CKAN configuration ini file::

    ckan.plugins = solr_highlighting

|

API usage
=========

If you want to run a search query which returns text extract that shows where the dataset match the query, you can 
use the action API function 'package_search_highlighted'. It extends the usual 'package_search' function with the 
ability to display highlight snippets from Solr response highlighting.
Solr provides a collection of highlighting search parameters (set in the schema.xml 
configuration file and/or as part of the search request) for example to apply highlighting and to select fields to 
highlight. See more at: http://wiki.apache.org/solr/HighlightingParameters
This action accepts all solr’s highlighting query parameters. 
All parameters are optional. You can use as many or as few of them as you want. 

|

When highlighting is requested, package_search_highlighted adds for each package a new metadata field 'highlighting' 
to extras listing all of the highlighted phrases found in each package.

|

Example Query::
    http://test.ckan.net/api/3/action/package_search_highlighted?q=test&hl=true&hl.fl=notes 

|

Result::   
   {'count': 4,
    'sort': 'score desc, metadata_modified desc',
    'facets': { },
    'results': [
       { 
          'extras': [
                {  'value': {'notes': ['This is a <em>test</em> snippet']},
                   'key': 'highlighting'
                }
            ]
        }
      ]
    }

|
|
      
Copying and License
===================
|
This material is copyright (c) 2015  Fachliche Leitstelle Transparenzportal, Hamburg, Germany.

|

It is open and licensed under the GNU Affero General Public License (AGPL) v3.0 whose full text may be found at:
http://www.fsf.org/licensing/licenses/agpl-3.0.html

|
|