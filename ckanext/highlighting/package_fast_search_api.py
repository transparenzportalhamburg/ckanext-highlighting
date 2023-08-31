from logging import getLogger
import sqlalchemy

from ckan.lib.helpers import json
import ckan.lib.dictization
import ckan.logic as logic
import ckan.logic.schema
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.navl.dictization_functions
import ckan.plugins as plugins

from ckan.plugins import implements, SingletonPlugin

import ckan.plugins.toolkit as toolkit
from ckan.logic import ValidationError

from ckan.plugins import IActions
from .query_highlighting import HighlightingPackageSearchQuery

_select = sqlalchemy.sql.select
_aliased = sqlalchemy.orm.aliased
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case
_text = sqlalchemy.text

log = getLogger(__name__)
_validate = ckan.lib.navl.dictization_functions.validate
_table_dictize = ckan.lib.dictization.table_dictize
_check_access = logic.check_access
NotFound = logic.NotFound
ValidationError = logic.ValidationError
_get_or_bust = logic.get_or_bust


class FastSearchApi(SingletonPlugin):
    '''
    Highlighting Search API 
    '''
    implements(IActions)

# for IActions
    def get_actions(self):
        action_functions = _get_functions()

        return action_functions
    

def _get_functions():
    return {            
            'package_fast_search': package_fast_search
    }


@toolkit.side_effect_free
def package_fast_search(context, data_dict):
    '''
    This function extends the functionality provided by package_search 
    by allowing highlighting queries. The highlight text will be added
    to package extras. This action accepts all solr highlighting query 
    parameters. 
    '''
    # sometimes context['schema'] is None
    log.debug("Start package_fast_search")
    schema = (context.get('schema') or
              logic.schema.default_package_search_schema())
    if isinstance(data_dict.get('facet.field'), str):
        data_dict['facet.field'] = json.loads(data_dict['facet.field'])
    data_dict, errors = _validate(data_dict, schema, context)
    # put the extras back into the data_dict so that the search can
    # report needless parameters
    data_dict.update(data_dict.get('__extras', {}))
    data_dict.pop('__extras', None)
    if errors:
        raise ValidationError(errors)

    model = context['model']
    session = context['session']

    # KG Brauchen wir das? Ich glaube nicht
     #_check_access('package_search', context, data_dict)

    # Move ext_ params to extras and remove them from the root of the search
    # params, so they don't cause and error
    data_dict['extras'] = data_dict.get('extras', {})
    for key in [key for key in list(data_dict.keys()) if key.startswith('ext_')]:
        data_dict['extras'][key] = data_dict.pop(key)

    # check if some extension needs to modify the search params
    #needed?
    #for item in plugins.PluginImplementations(plugins.IPackageController):
    #    data_dict = item.before_search(data_dict)

    # the extension may have decided that it is not necessary to perform
    # the query
    abort = data_dict.get('abort_search', False)

    if data_dict.get('sort') in (None, 'rank'):
        data_dict['sort'] = 'score desc, metadata_modified desc'

    results = []
    if not abort:
        # return a list of package ids
        data_dict['fl'] = 'id data_dict'

        # If this query hasn't come from a controller that has set this flag
        # then we should remove any mention of capacity from the fq and
        # instead set it to only retrieve public datasets
        fq = data_dict.get('fq', '')
        if not context.get('ignore_capacity_check', False):
            fq = ' '.join(p for p in fq.split(' ')
                            if not 'capacity:' in p)
            data_dict['fq'] = fq + ' capacity:"public"'

        # Pop these ones as Solr does not need them
        extras = data_dict.pop('extras', None)

        query = HighlightingPackageSearchQuery()
        #query = search.query_for(model.Package)
        query.run(data_dict)

        # Add them back so extensions can use them on after_search
        data_dict['extras'] = extras

        for package in query.results:
            # get the package object
            package, package_dict = package['id'], package.get('data_dict')
            # here only the id for checking
            # pkg_query = session.query(model.PackageRevision.id)\
            #     .filter(model.PackageRevision.id == package)\
            #     .filter(_and_(
            #         model.PackageRevision.state == u'active',
            #         model.PackageRevision.current == True
            #     ))
            # But: harvest_object and harvest_source DB-accesses are still done
            # Hence, delete the DB check. I.e., if a package is in the solr and not in the DB 
            # it will be presented as search result
            # pkg_query = session.query(model.Package.id)\
            #     .filter(model.Package.id == package)\
            #     .filter(_and_(
            #         model.Package.state == u'active'
            #     ))

            # pkg = pkg_query.first()
            #log.warning('package %s in database found %s' % (pkg, package))
            ## if the index has got a package that is not in ckan then
            ## ignore it.
            #if not pkg:
            #    log.warning('package %s in index but not in database' % package)
            #    continue
            ## use data in search index if there
            if package_dict:
                ## the package_dict still needs translating when being viewed
                package_dict = json.loads(package_dict)
                # TEST is it needed?
                # Creates access to harvest_object
                #if context.get('for_view'):
                #     for item in plugins.PluginImplementations( plugins.IPackageController):
                #         package_dict = item.before_view(package_dict)
                results.append(package_dict)
            else:
                # Here get the whole package. But should not occur because it should be in the SOLR
                pkg_query = session.query(model.PackageRevision)\
                                   .filter(model.PackageRevision.id == package)\
                                   .filter(_and_(
                                       model.PackageRevision.state == 'active',
                                       model.PackageRevision.current == True
                                   ))
                pkg = pkg_query.first()
                log.warning('package %s is not in index but in database as %s' % (package, pkg))
                results.append(model_dictize.package_dictize(pkg,context))

        count = query.count
        facets = query.facets
    else:
        count = 0
        facets = {}
        results = []

    search_results = {
        'count': count,
        'facets': facets,
        'results': results,
        'sort': data_dict['sort']
    }

    # Transform facets into a more useful data structure.
    restructured_facets = {}
    for key, value in list(facets.items()):
        restructured_facets[key] = {
                'title': key,
                'items': []
                }
        for key_, value_ in list(value.items()):
            new_facet_dict = {}
            new_facet_dict['name'] = key_
            # TEST needed?
            # if key in ('groups', 'organization'):
            #     group = model.Group.get(key_)
            #     if group:
            #         new_facet_dict['display_name'] = group.display_name
            #     else:
            #         new_facet_dict['display_name'] = key_
            # elif key == 'license_id':
            #     license = model.Package.get_license_register().get(key_)
            #     if license:
            #         new_facet_dict['display_name'] = license.title
            #     else:
            #         new_facet_dict['display_name'] = key_
            # else:
            new_facet_dict['display_name'] = key_
            new_facet_dict['count'] = value_
            restructured_facets[key]['items'].append(new_facet_dict)
    search_results['search_facets'] = restructured_facets

    # check if some extension needs to modify the search results
    for item in plugins.PluginImplementations(plugins.IPackageController):
        search_results = item.after_search(search_results,data_dict)

    # After extensions have had a chance to modify the facets, sort them by
    # display name.
    for facet in search_results['search_facets']:
        search_results['search_facets'][facet]['items'] = sorted(
                search_results['search_facets'][facet]['items'],
                key=lambda facet: facet['display_name'], reverse=True)

    return search_results


