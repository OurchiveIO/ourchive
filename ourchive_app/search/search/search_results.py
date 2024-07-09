from search.models import SavedSearch
from search.search.search_obj import FilterFacet, ResultFacet, GroupFacet, ContextualFilterFacet
from core.models import WorkType, OurchiveSetting, Tag, AttributeType, TagType, Language, SearchGroup, AttributeValue
from search.search import constants as search_constants
import logging

logger = logging.getLogger(__name__)


class SearchResults(object):

    def __init__(self):
        self.include_search_groups = {}
        self.exclude_search_groups = {}
        self.default_search_group = SearchGroup(label='Facets')
        if not SearchGroup.objects.count() > 0:
            self.include_search_groups['Facets'] = []
            self.exclude_search_groups['Facets'] = []
        else:
            self.default_search_group = SearchGroup.objects.first()
            for group in SearchGroup.objects.all():
                self.include_search_groups[group.label] = []
                self.exclude_search_groups[group.label] = []

    def set_shared_vals(self, kwargs):
        self.tag_id = kwargs.get('tag_id', None)
        self.work_type_id = kwargs.get('work_id', None)
        self.work_search_include = kwargs.get('work_search', []).get('include_filter', {})
        self.work_search_exclude = kwargs.get('work_search', []).get('exclude_filter', {})
        self.collection_search_include = kwargs.get('collection_search', []).get('include_filter', {})
        self.collection_search_exclude = kwargs.get('collection_search', []).get('exclude_filter', {})
        self.tag_search_include = kwargs.get('tag_search', []).get('include_filter', {})
        self.tag_search_exclude = kwargs.get('tag_search', []).get('exclude_filter', {})
        self.split_include_exclude = str(
            kwargs.get('options', {}).get('split_include_exclude', 'true')).lower() == "true"
        self.order_by = str(kwargs.get('options', {}).get('order_by', '-updated_on'))
        self.search_name = kwargs.get('search_name', None)
        self.user_id = kwargs.get('user_id', None)
        self.term = kwargs.get('work_search', []).get('term', '')

    def flatten_search_groups(self, context):
        groups_array = []
        for group in getattr(self, f'{context}_search_groups').keys():
            if getattr(self, f'{context}_search_groups')[group]:
                groups_array.append({'label': group, 'facets': getattr(self, f'{context}_search_groups')[group]})
        return groups_array

    def process_tag_tags(self, tags, tags_dict):
        for result in tags:
            if result['display_text'] not in tags_dict[result['tag_type']]['tags']:
                tags_dict[result['tag_type']]['tags'].append(result['display_text'])
        return tags_dict

    def get_inverse_context(self, context):
        return 'exclude' if context == 'include' else ('include' if context == 'exclude' else None)

    def build_final_tag_facets(self, tag_filter_name, result_json, tags_dict, context):
        for tag_type in tags_dict:
            if len(tags_dict[tag_type]['tags']) > 0:
                tag_filter_vals = []
                for tag_text in tags_dict[tag_type]['tags']:
                    checked_tag = True if (self.tag_id and tag_filter_name and tag_filter_name == tag_text) else False
                    if not checked_tag:
                        checked_tag = tag_text in getattr(self, f'work_search_{context}').get('tags', [])
                        if not checked_tag:
                            checked_tag = tag_text.lower() in getattr(self, f'work_search_{context}').get('tags', [])
                        if not self.split_include_exclude:
                            inverse_checked = tag_text.lower() in getattr(self,
                                                                          f'work_search_{self.get_inverse_context(context)}').get(
                                'tags', [])
                            tag_filter_vals.append(ContextualFilterFacet(tag_text, checked_tag, inverse_checked))
                        else:
                            tag_filter_vals.append(FilterFacet(tag_text, checked_tag))
                result_facet = ResultFacet(tags_dict[tag_type]['type_id'], tag_type, tag_filter_vals, 'tag').to_dict()
                getattr(self, f'{context}_search_groups')[tags_dict[tag_type]['group']].append(result_facet)

    def get_tag_facets(self, results, result_json, context, tags):
        tag_filter_name = None
        if self.tag_id:
            tag_filter = Tag.objects.filter(id=self.tag_id).first()
            if tag_filter:
                tag_filter_name = tag_filter.display_text
        tags_dict = {}
        for tag_type in TagType.objects.all():
            tags_dict[tag_type.label] = {'tags': [], 'type_id': tag_type.id, 'type_label': tag_type.label,
                                         'group': tag_type.search_group.label if tag_type.search_group else self.default_search_group.label}
        for tag in getattr(self, f'work_search_{context}').get('tags', []):
            db_tag_list = Tag.objects.filter(display_text__iexact=tag).all()
            for db_tag in db_tag_list:
                tags_dict[db_tag.tag_type.label]['tags'].append(db_tag.display_text)
        # if we're including all tags and their include + exclude states, we need tags that might not 
        # already be in the resultset e.g. excluded tags
        if not self.split_include_exclude:
            for tag in getattr(self, f'work_search_{self.get_inverse_context(context)}').get('tags', []):
                db_tag_list = Tag.objects.filter(display_text__iexact=tag).all()
                for db_tag in db_tag_list:
                    if db_tag.display_text not in tags_dict[db_tag.tag_type.label]['tags']:
                        tags_dict[db_tag.tag_type.label]['tags'].append(db_tag.display_text)
        tags_dict = self.process_tag_tags(tags, tags_dict)
        tags_dict = self.process_tag_tags(results['tag']['data'], tags_dict)
        self.build_final_tag_facets(tag_filter_name, result_json, tags_dict, context)
        return result_json

    def process_chive_attributes(self, results, attributes_dict):
        for result in results:
            if len(result['attributes']) > 0:
                for attribute in result['attributes']:
                    if attribute['attribute_type'] not in attributes_dict:
                        attributes_dict[attribute['attribute_type']] = [attribute['display_name']]
                    elif attribute['display_name'] not in attributes_dict[attribute['attribute_type']]['attrs']:
                        attributes_dict[attribute['attribute_type']]['attrs'].append(attribute['display_name'])
        return attributes_dict

    def get_attribute_facets(self, results, result_json, context):
        attributes_dict = {}
        for attribute_type in AttributeType.objects.filter().all():
            attributes_dict[attribute_type.display_name] = {'attrs': [], 'type_id': attribute_type.id,
                                                            'type_label': attribute_type.display_name,
                                                            'group': attribute_type.search_group.label if attribute_type.search_group else self.default_search_group.label}
        for attribute in getattr(self, f'work_search_{context}').get('attributes', []):
            db_attr_list = AttributeValue.objects.filter(display_name__iexact=attribute).all()
            for db_attr in db_attr_list:
                attributes_dict[db_attr.attribute_type.display_name]['attrs'].append(db_attr.display_name)
        attributes_dict = self.process_chive_attributes(results['work']['data'], attributes_dict)
        attributes_dict = self.process_chive_attributes(results['bookmark']['data'], attributes_dict)
        attributes_dict = self.process_chive_attributes(results['collection']['data'], attributes_dict)
        for key in attributes_dict:
            if len(attributes_dict[key]['attrs']) > 0:
                attribute_filter_vals = []
                for val in attributes_dict[key]['attrs']:
                    checked_attr = val.lower() in getattr(self, f'work_search_{context}').get('attributes', [])
                    if not checked_attr:
                        checked_attr = val in getattr(self, f'work_search_{context}').get('attributes', [])
                    attribute_filter_vals.append(FilterFacet(val, checked_attr))
                result_facet = ResultFacet(attributes_dict[key]['type_id'], key, attribute_filter_vals,
                                           'attribute').to_dict()
                try:
                    getattr(self, f'{context}_search_groups')[attributes_dict[key]['group']].append(result_facet)
                except Exception as e:
                    logger.error(f'Attribute has search group which is not in search groups. '
                                 f'This likely means you should assign a search group to this attribute '
                                 f'in the admin console. Error: {e}')
                    continue

    def get_chive_info_facets(self, context):
        chive_info = {"label": "Chive Info", "facets": []}
        work_types = WorkType.objects.all()
        work_types_list = []
        for work_type in work_types:
            checked = self.work_type_id and self.work_type_id == str(work_type.id)
            if not checked:
                checked = work_type.type_name in getattr(self, f'work_search_{context}').get('Work Type', [])
            work_types_list.append(
                {"label": work_type.type_name, "filter_val": work_type.type_name, "checked": checked})
        work_types_dict = {}
        work_types_dict["display_type"] = 'checkbox'
        work_types_dict["label"] = "Work Type"
        work_types_dict["values"] = work_types_list
        work_types_dict["object_type"] = 'work'
        chive_info["facets"].append(work_types_dict)

        languages = Language.objects.all()
        languages_list = []
        for language in languages:
            checked = language.display_name in getattr(self, f'work_search_{context}').get('Language',
                                                                                           []) or language.display_name in getattr(
                self, f'collection_search_{context}').get('Language', [])
            languages_list.append(
                {"label": language.display_name, "filter_val": language.display_name, "checked": checked})
        languages_dict = {}
        languages_dict["display_type"] = 'checkbox'
        languages_dict["label"] = "Language"
        languages_dict["values"] = languages_list
        languages_dict["object_type"] = "chive"
        chive_info["facets"].append(languages_dict)

        # todo move to separate class
        word_count_dict = {}
        word_count_dict["display_type"] = 'input'
        word_count_dict["label"] = "Work Word Count"
        word_count_dict["object_type"] = 'work'
        word_count_dict["filters"] = ["word_count_gte", "word_count_lte"]
        input_value_gte = getattr(self, f'work_search_{context}').get('word_count_gte', [""])[0]
        input_value_lte = getattr(self, f'work_search_{context}').get('word_count_lte', [""])[0]
        word_count_dict["values"] = [
            {"label": "From", "filter_val": "word_count_gte", "type": "text_range", "value": input_value_gte},
            {"label": "To", "filter_val": "word_count_lte", "type": "text_range", "value": input_value_lte}]
        chive_info["facets"].append(word_count_dict)

        # TODO: ADD FILTER
        audio_length_dict = {}
        audio_length_dict["label"] = "Audio Length"
        audio_length_dict["display_type"] = 'checkbox'
        audio_length_dict["values"] = [{"label": "Under 30:00", "filter_val": "audio_length_range|ranges|0|30"},
                                       {"label": "30:00 - 1:00:00",
                                        "filter_val": "audio_length_range|ranges|30|60"},
                                       {"label": "1:00:00 - 2:00:00",
                                        "filter_val": "audio_length_range|ranges|60|120"},
                                       {"label": "2:00:00 - 3:00:00",
                                        "filter_val": "audio_length_range|ranges|120|180"},
                                       {"label": "3:00:00+", "filter_val": "audio_length_range|ranges|20000|180"}]
        chive_info["facets"].append(audio_length_dict)

        # todo move to db setting
        complete_dict = {}
        complete_dict["label"] = "Completion Status"
        complete_dict["object_type"] = 'work'
        complete_dict['display_type'] = 'checkbox'
        complete_dict["values"] = [{"label": "Complete", "filter_val": "1",
                                    "checked": "1" in getattr(self, f'work_search_{context}').get("Completion Status",
                                                                                                  [])},
                                   {"label": "Work In Progress", "filter_val": "0",
                                    "checked": "0" in getattr(self, f'work_search_{context}').get("Completion Status",
                                                                                                  [])}]
        chive_info["facets"].append(complete_dict)

        return chive_info

    def get_options_facets(self):
        options = {}
        options["order_by"] = self.order_by
        options["search_name"] = self.search_name
        return options

    def get_contextual_result_facets(self, results, context, tags):
        result_json = []
        chive_info = self.get_chive_info_facets(context)
        result_json.append(chive_info)
        self.get_tag_facets(results, result_json, context, tags)
        self.get_attribute_facets(results, result_json, context)
        result_json = result_json + self.flatten_search_groups(context)
        return result_json

    def get_result_facets(self, results, kwargs, tags=None):
        # TODO: use translation on labels, move ranges to a dynamic number
        if tags is None:
            tags = []
        self.set_shared_vals(kwargs)
        result_json_include = self.get_contextual_result_facets(results, 'include', tags)
        options = self.get_options_facets()
        dict_results = {'include_facets': result_json_include, 'options': options}
        dict_results['exclude_facets'] = []
        self.get_tag_facets(results, dict_results['exclude_facets'], 'exclude', tags)
        if self.search_name:
            dict_results['search_name'] = self.search_name
            self.save_search(self.order_by, self.user_id)
        return dict_results

    def save_search(self, order_by, user_id):
        '''tag_id = models.IntegerField(null=True, blank=True)
        type_id = models.IntegerField(null=True, blank=True)
        attr_id = models.IntegerField(null=True, blank=True)
        languages = models.ManyToManyField('core.Language')
        info_facets = models.CharField(null=True, blank=True)
        include_facets = models.CharField(null=True, blank=True)
        exclude_facets = models.CharField(null=True, blank=True)
        order_by = models.CharField(max_length=100, blank=True, null=True)'''
        info_facets = {
            search_constants.WORK_TYPE_FILTER_KEY: getattr(self, f'work_search_include').get(
                search_constants.WORK_TYPE_FILTER_KEY, []),
            search_constants.LANGUAGE_FILTER_KEY: getattr(self, f'work_search_include').get(
                search_constants.LANGUAGE_FILTER_KEY, []),
            search_constants.COMPLETE_FILTER_KEY: getattr(self, f'work_search_include').get(
                search_constants.COMPLETE_FILTER_KEY, []),
            search_constants.WORD_COUNT_FILTER_KEY_LTE:
                getattr(self, f'work_search_include').get('word_count_lte', [""])[0],
            search_constants.WORD_COUNT_FILTER_KEY_GTE:
                getattr(self, f'work_search_include').get('word_count_gte', [""])[0]
        }
        include_facets = list(set(self.work_search_include['tags'] + self.collection_search_include['tags']))
        exclude_facets = list(set(self.work_search_exclude['tags'] + self.collection_search_exclude['tags']))
        if SavedSearch.objects.filter(name=self.search_name, user_id=user_id).count() > 0:
            saved_search = SavedSearch.objects.filter(name=self.search_name, user_id=user_id).first()
        else:
            saved_search = SavedSearch(user_id=user_id,
                                       name=self.search_name)
        saved_search.order_by = order_by
        saved_search.info_facets = info_facets
        saved_search.include_facets = include_facets
        saved_search.exclude_facets = exclude_facets
        saved_search.term = self.term
        saved_search.save()
        return saved_search
