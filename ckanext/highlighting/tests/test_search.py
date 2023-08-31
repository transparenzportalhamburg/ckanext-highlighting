import os
import json

from hmbtg_utils.testing.package import index_package

from ckan.logic import get_action
import ckan.model as model

context = {'model': model, 'session': model.Session,
           'user': "", 'for_view': True}

def load_pkg(**kwargs):
    pkg = json.load(
        open(os.path.join(os.path.dirname(__file__), 'data/index_pkg_01.json')))
    return {**pkg, **kwargs}

def test_search():
    data = {'sort': u'publishing_date desc, title_sort asc',
            'fq': u'+extras_latestVersion:"true" -dataset_type:"harvest" -forward:"true" capacity:"public"',
            'rows': 20,
            'facet.field': ['temporal_coverage_from', 'groups', 'license_id', 'organization', 'extras_registerobject_type', 'type', 'temporal_coverage_to', 'res_format'],
            'mm': '100%', 'hl.snippets': '1',
            'hl.preserveMulti': 'true', 'q': u'hamburg', 'start': 0, 'hl.maxAnalyzedChars': -1, 'hl': 'true',
        #     'hl.fl': 'res_fulltext title notes author license_title author_email tags extras_source', 'fl': 'id data_dict'}
            'hl.fl': 'title notes', 'fl': 'id data_dict'}
    pkg = index_package(load_pkg())
    ret = get_action('package_fast_search')(context, data)

    assert len(ret['results']) >= 1

