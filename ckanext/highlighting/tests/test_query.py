import os
import json


from ckanext.highlighting.query_highlighting import HighlightingPackageSearchQuery
from hmbtg_utils.testing.package import create_dataset, index_package, get_package
from ckan.lib.search.index import clear_index


def load_pkg(**kwargs):
    pkg = json.load(
        open(os.path.join(os.path.dirname(__file__), 'data/index_pkg_01.json')))
    return {**pkg, **kwargs}


def test_query():
    pkg = index_package(load_pkg())

    data = {'sort': u'publishing_date desc, title_sort asc',
            'fq': u'+extras_latestVersion:"true" -dataset_type:"harvest" -forward:"true" capacity:"public"',
            'rows': 20,
            'facet.field': ['temporal_coverage_from', 'groups', 'license_id', 'organization', 'extras_registerobject_type', 'type', 'temporal_coverage_to', 'res_format'],
            'mm': '100%', 'hl.snippets': '1',
            'hl.preserveMulti': 'true', 'q': u'hamburg', 'start': 0, 'hl.maxAnalyzedChars': -1, 'hl': 'true',
        #     'hl.fl': 'res_fulltext title notes author license_title author_email tags extras_source', 'fl': 'id data_dict'}
            'hl.fl': 'title notes', 'fl': 'id data_dict'}


    query = HighlightingPackageSearchQuery()
    query.run(data)

    assert len(query.results) > 0

    pkg = json.loads(query.results[0]['data_dict'])
    h = [e['value'] for e in pkg['extras'] if e['key'] == 'highlighting']

    assert h[0]['title'][0] == '<em>hamburg</em> test'


def test_query_fields():
    clear_index()

    pkg = create_dataset()
    pkg = get_package(pkg['id'])
    pkg['title'] = 'foo'
    pkg['name'] = 'foo'
    pkg['notes'] = 'foo'
    pkg['maintainer'] = 'foo'
    pkg['author'] = 'foo'
    pkg['version'] = 'foo'
    pkg['license'] = 'foo'
    pkg['fulltext'] = 'foo'
    pkg['resources'][0]['fulltext'] = 'foo'
    pkg = index_package(pkg)

    fields = "res_fulltext title notes author license_title author_email tags extras_source"
    data = {'sort': u'publishing_date desc, title_sort asc',
            'fq': u'+extras_latestVersion:"true" -dataset_type:"harvest" -forward:"true" capacity:"public"',
            'rows': 20,
            'facet.field': ['temporal_coverage_from', 'groups', 'license_id', 'organization', 'extras_registerobject_type', 'type', 'temporal_coverage_to', 'res_format'],
            'mm': '100%', 'hl.snippets': '1',
            'hl.preserveMulti': 'true', 'q': u'foo', 'start': 0, 'hl.maxAnalyzedChars': -1, 'hl': 'true',
            'hl.fl': fields, 'fl': 'id data_dict'}

    query = HighlightingPackageSearchQuery()
    query.run(data)

    pkg = json.loads(query.results[0]['data_dict'])
    h = [e['value'] for e in pkg['extras'] if e['key'] == 'highlighting']

    assert h == [{'res_fulltext': ['default_test_dataset fulltext'], 'title': ['<em>foo</em>'], 'notes': ['<em>foo</em>'], 'author': ['<em>foo</em>']}]

