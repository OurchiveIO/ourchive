from search.search.search_obj import FilterFacet, ResultFacet, GroupFacet, ContextualFilterFacet
from core.models import WorkType, OurchiveSetting, Tag, AttributeType, TagType, Language, SearchGroup, AttributeValue
from core.utils import get_star_count
from copy import deepcopy

class SearchResults(object):

    def __init__(self):
        self.include_search_groups = {}
        self.exclude_search_groups = {}
        if not SearchGroup.objects.any():
            self.include_search_groups['Facets'] = []
            self.exclude_search_groups['Facets'] = []
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
        self.split_include_exclude = str(kwargs.get('options', {}).get('split_include_exclude', 'true')).lower() == "true"
        self.order_by = str(kwargs.get('options', {}).get('order_by', '-updated_on'))

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
                        checked_tag = tag_text.lower() in getattr(self, f'work_search_{context}').get('tags', [])
                        if not self.split_include_exclude:
                            inverse_checked = tag_text.lower() in getattr(self, f'work_search_{self.get_inverse_context(context)}').get('tags', [])
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
            tags_dict[tag_type.label] = {'tags': [], 'type_id': tag_type.id, 'type_label': tag_type.label, 'group': tag_type.search_group.label if tag_type.search_group else 'Facets'}
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
            attributes_dict[attribute_type.display_name] = {'attrs': [], 'type_id': attribute_type.id, 'type_label': attribute_type.display_name, 'group': attribute_type.search_group.label if attribute_type.search_group else 'Facets'}
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
                    attribute_filter_vals.append(FilterFacet(val, checked_attr))
                result_facet = ResultFacet(attributes_dict[key]['type_id'], key, attribute_filter_vals, 'attribute').to_dict()
                getattr(self, f'{context}_search_groups')[attributes_dict[key]['group']].append(result_facet)

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
            checked = language.display_name in getattr(self, f'work_search_{context}').get('Language', []) or language.display_name in getattr(self, f'collection_search_{context}').get('Language', [])
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
        word_count_dict["values"] = [{"label": "From", "filter_val": "word_count_gte", "type": "text_range", "value": input_value_gte},
                                     {"label": "To","filter_val": "word_count_lte", "type": "text_range", "value": input_value_lte}]
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
        complete_dict["values"] = [{"label": "Complete", "filter_val": "1", "checked": "1" in getattr(self, f'work_search_{context}').get("Completion Status", [])},
                                   {"label": "Work In Progress", "filter_val": "0", "checked": "0" in getattr(self, f'work_search_{context}').get("Completion Status", [])}]
        chive_info["facets"].append(complete_dict)

        return chive_info

    def get_options_facets(self):
        options = {}
        options["order_by"] = self.order_by
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
        if self.split_include_exclude:
            result_json_exclude = self.get_contextual_result_facets(results, 'exclude', tags)
            return [result_json_include, result_json_exclude, options]
        else:
            return [result_json_include, options]