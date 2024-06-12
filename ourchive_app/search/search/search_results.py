from search.search.search_obj import FilterFacet, ResultFacet, GroupFacet
from core.models import WorkType, OurchiveSetting, Tag, AttributeType, TagType, Language, SearchGroup
from core.utils import get_star_count

class SearchResults(object):

    def __init__(self):
        self.search_groups = {}
        for group in SearchGroup.objects.all():
            self.search_groups[group.label] = []

    def flatten_search_groups(self):
        groups_array = []
        for group in self.search_groups.keys():
            if self.search_groups[group]:
                groups_array.append({'label': group, 'facets': self.search_groups[group]})
        return groups_array

    def process_tag_tags(self, tags, tags_dict):
        for result in tags:
            if result['display_text'] not in tags_dict[result['tag_type']]['tags']:
                tags_dict[result['tag_type']]['tags'].append(result['display_text'])
        return tags_dict

    def process_chive_tags(self, tags, tags_dict):
        for result in tags:
            if len(result['tags']) > 0:
                tags_dict = self.process_tag_tags(result['tags'], tags_dict)
        return tags_dict

    def build_final_tag_facets(self, tag_id, tag_filter_name, result_json, tags_dict):
        for key in tags_dict:
            if len(tags_dict[key]['tags']) > 0:
                tag_filter_vals = []
                for val in tags_dict[key]['tags']:
                    checked_tag = True if (tag_id and tag_filter_name and tag_filter_name == val) else False
                    tag_filter_vals.append(FilterFacet(val, checked_tag))
                result_facet = ResultFacet(tags_dict[key]['type_id'], key, tag_filter_vals, 'tag').to_dict()
                self.search_groups[tags_dict[key]['group']].append(result_facet)

    def get_tag_facets(self, tag_id, results, result_json):
        tag_filter_name = None
        if tag_id:
            tag_filter = Tag.objects.filter(id=tag_id).first()
            if tag_filter:
                tag_filter_name = tag_filter.display_text
        tags_dict = {}
        for tag_type in TagType.objects.all():
            tags_dict[tag_type.label] = {'tags': [], 'type_id': tag_type.id, 'type_label': tag_type.label, 'group': tag_type.search_group.label}
        tags_dict = self.process_chive_tags(results['work']['data'], tags_dict)
        tags_dict = self.process_chive_tags(results['bookmark']['data'], tags_dict)
        tags_dict = self.process_chive_tags(results['collection']['data'], tags_dict)
        tags_dict = self.process_tag_tags(results['tag']['data'], tags_dict)
        self.build_final_tag_facets(tag_id, tag_filter_name, result_json, tags_dict)
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

    def get_attribute_facets(self, results, result_json):
        attributes_dict = {}
        for attribute_type in AttributeType.objects.filter(search_group__isnull=False).all():
            attributes_dict[attribute_type.display_name] = {'attrs': [], 'type_id': attribute_type.id, 'type_label': attribute_type.display_name, 'group': attribute_type.search_group.label}
        attributes_dict = self.process_chive_attributes(results['work']['data'], attributes_dict)
        attributes_dict = self.process_chive_attributes(results['bookmark']['data'], attributes_dict)
        attributes_dict = self.process_chive_attributes(results['collection']['data'], attributes_dict)
        for key in attributes_dict:
            if len(attributes_dict[key]['attrs']) > 0:
                attribute_filter_vals = []
                for val in attributes_dict[key]['attrs']:
                    attribute_filter_vals.append(FilterFacet(val, False))
                result_facet = ResultFacet(attributes_dict[key]['type_id'], key, attribute_filter_vals, 'attribute').to_dict()
                self.search_groups[attributes_dict[key]['group']].append(result_facet)

    def get_result_facets(self, results, tag_id=None, work_type_id=None):
        # todo: refactor - move attribute & tag processing to individual functions,
        # change facet dicts to pull from consts, use translation on labels,
        # move ranges to a dynamic number
        result_json = []
        chive_info = {"label": "Chive Info", "facets": []}
        work_types = WorkType.objects.all()
        work_types_list = []
        for work_type in work_types:
            work_types_list.append(
                {"label": work_type.type_name, "filter_val": work_type.type_name, "checked": work_type_id and work_type_id == str(work_type.id)})
        work_types_dict = {}
        work_types_dict["display_type"] = 'checkbox'
        work_types_dict["label"] = "Work Type"
        work_types_dict["values"] = work_types_list
        work_types_dict["object_type"] = 'work'
        chive_info["facets"].append(work_types_dict)

        languages = Language.objects.all()
        languages_list = []
        for language in languages:
            languages_list.append(
                {"label": language.display_name, "filter_val": language.display_name})
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
        word_count_dict["values"] = [{"label": "From", "filter_val": "word_count_gte", "type": "text_range"},
                                     {"label": "To","filter_val": "word_count_lte", "type": "text_range"}]
        chive_info["facets"].append(word_count_dict)

        # todo move to db setting
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
        complete_dict["values"] = [{"label": "Complete", "filter_val": "1"},
                                   {"label": "Work In Progress", "filter_val": "0"}]
        chive_info["facets"].append(complete_dict)

        result_json.append(chive_info)

        self.get_tag_facets(tag_id, results, result_json)
        self.get_attribute_facets(results, result_json)
        result_json = result_json + self.flatten_search_groups()
        return result_json