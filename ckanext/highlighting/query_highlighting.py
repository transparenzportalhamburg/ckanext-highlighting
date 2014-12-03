import re
import logging

from solr import SolrException
from paste.deploy.converters import asbool
from paste.util.multidict import MultiDict
from pylons import config

from ckan.common import json
from ckan.lib.search.common import make_connection, SearchError, SearchQueryError
import ckan.logic as logic
import ckan.model as model
from ckan.lib.search.query import PackageSearchQuery

log = logging.getLogger(__name__)

_open_licenses = None

VALID_SOLR_PARAMETERS = set([
    'q', 'fl', 'fq', 'rows', 'sort', 'start', 'wt', 'qf', 'bf', 'boost',
    'facet', 'facet.mincount', 'facet.limit', 'facet.field',
    'extras', 'fq_list', 'tie', 'defType', 'mm'
])

QUERY_FIELDS = "name^4 title^4 tags^2 groups^2 text"

solr_regex = re.compile(r'([\\+\-&|!(){}\[\]^"~*?:])')

class HighlightingPackageSearchQuery(PackageSearchQuery):

    def normalize_query_keys(self, query):
	'''
	Many Solr highlighting parameters are in a dotted notation (e.g.,
        `hl.simple.post`).  For such parameters, the dots will be replaced 
        with underscores which is required by the solr function 
        raw_query(**params).
	'''
        normalized_query = {}
        if query:
            for key, value in query.iteritems():
                if key.startswith('hl.'):
                    normalized_query[key.replace('.','_')] = value
        	else:
		    normalized_query[key] = value
        return normalized_query


    def addHighlightedText(self, highlighting_dict, results):
    	'''
        This function adds the highlighted text returned by the solr search
        to package extras.
        '''
        if(results):
            for result in results: 		
        	id = result['index_id']
                package_dict = json.loads(result['data_dict'])
                
		               
                if id in highlighting_dict.keys():
                    #if len(highlighting_dict[id]) > 0:
                    package_dict['extras'].append({'value': highlighting_dict[id], 'key' : 'highlighting'})    
                
                result['data_dict'] = json.dumps(package_dict)
    
        return results


    def run(self, query):
        '''
        Performs a dataset search using the given query.
        The query may include highlighting parameters which will be
        added to package extras.

        @param query - dictionary with keys like: q, fq, sort, rows, facet
        @return - dictionary with keys results and count

        May raise SearchQueryError or SearchError.
        '''
       
        assert isinstance(query, (dict, MultiDict))
        # check that query keys are valid
	valid_params = []
	invalid_params = []
        for key in query.keys():
		if key in VALID_SOLR_PARAMETERS or key == 'hl' or key.startswith('hl.'):
			valid_params.append(key)
		else:
			invalid_params.append(key)

	if len(invalid_params) > 0:
		raise SearchQueryError("Invalid search parameters: %s" % invalid_params)

	query = self.normalize_query_keys(query)
              

        # default query is to return all documents
        q = query.get('q')
        if not q or q == '""' or q == "''":
            query['q'] = "*:*"

        # number of results
        rows_to_return = min(1000, int(query.get('rows', 10)))
        if rows_to_return > 0:
            # #1683 Work around problem of last result being out of order
            #       in SOLR 1.4
            rows_to_query = rows_to_return + 1
        else:
            rows_to_query = rows_to_return
        query['rows'] = rows_to_query

        # show only results from this CKAN instance
        fq = query.get('fq', '')
        if not '+site_id:' in fq:
            fq += ' +site_id:"%s"' % config.get('ckan.site_id')

        # filter for package status
        if not '+state:' in fq:
            fq += " +state:active"
        query['fq'] = [fq]

        fq_list = query.get('fq_list', [])
        query['fq'].extend(fq_list)

        # faceting
        query['facet'] = query.get('facet', 'true')
        query['facet.limit'] = query.get('facet.limit', config.get('search.facets.limit', '50'))
        query['facet.mincount'] = query.get('facet.mincount', 1)

        # return the package ID and search scores
        query['fl'] = query.get('fl', 'name')
	query['fl'] = query['fl'] + ' index_id'

        # return results as json encoded string
        query['wt'] = query.get('wt', 'json')

        # If the query has a colon in it then consider it a fielded search and do use dismax.
        defType = query.get('defType', 'dismax')
        if ':' not in query['q'] or defType == 'edismax':
            query['defType'] = defType
            query['tie'] = query.get('tie', '0.1')
            # this minimum match is explained
            # http://wiki.apache.org/solr/DisMaxQParserPlugin#mm_.28Minimum_.27Should.27_Match.29
            query['mm'] = query.get('mm', '2<-1 5<80%')
            query['qf'] = query.get('qf', QUERY_FIELDS)

        
        conn = make_connection()
        log.debug('Package query: %r' % query)
        try:
            solr_response = conn.raw_query(**query)
                    
        except SolrException, e:
            raise SearchError('SOLR returned an error running query: %r Error: %r' %
                              (query, e.reason))
        try:
            data = json.loads(solr_response)
            response = data['response']
            self.count = response.get('numFound', 0)
            self.results = response.get('docs', [])
            self.highlighted = data['highlighting']

            # #1683 Filter out the last row that is sometimes out of order
            self.results = self.results[:rows_to_return]
            self.results = self.addHighlightedText(self.highlighted, self.results)

            # get any extras and add to 'extras' dict
            for result in self.results:
                extra_keys = filter(lambda x: x.startswith('extras_'), result.keys())
                extras = {}
                for extra_key in extra_keys:
                    value = result.pop(extra_key)
                    extras[extra_key[len('extras_'):]] = value
		if extra_keys:
                    result['extras'] = extras

               	   
	    # if just fetching the id or name, return a list instead of a dict
            if query.get('fl') in ['id', 'name']:
                self.results = [r.get(query.get('fl')) for r in self.results]

            # get facets and convert facets list to a dict
            self.facets = data.get('facet_counts', {}).get('facet_fields', {})
            for field, values in self.facets.iteritems():
                self.facets[field] = dict(zip(values[0::2], values[1::2]))
        except Exception, e:
            log.exception(e)
            raise SearchError(e)
        finally:
            conn.close()

        return {'results': self.results, 'count': self.count}

