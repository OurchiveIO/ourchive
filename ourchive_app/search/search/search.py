from core.models import *
from api import object_factory
import re
from django.db.models import Q
from .search_obj import WorkSearch, BookmarkSearch, TagSearch, UserSearch, CollectionSearch
from django.contrib.postgres.search import TrigramWordDistance
from django.core.paginator import Paginator
from django.conf import settings
import logging
import math

logger = logging.getLogger(__name__)


class ElasticSearchProvider:
    from elasticsearch import Elasticsearch
    from elasticsearch_dsl import Search, Q

    def init_provider(self):
        logger.debug("Elasticsearch provider initialized.")

    def search_works(self, **kwargs):
        q = Q("multi_match", query=kwargs['filter']['term'], fields=[
              'title', 'summary', 'chapter__title', 'chapters__summary', 'tags__text'])
        filters = kwargs['filter']

        client = Elasticsearch()

        s = Search(using=client, index="work")
        if 'complete' in filters:
            s = s.filter("term", is_complete=True)
        if 'audio_length' in filters:
            s = s.filter("range", chapters__audio_length={
                "gt": filters['audio_length']
            })
        if 'image_formats' in filters:
            s = s.filter("terms", chapters__image_format=filters['image_formats'])
        if 'image_formats' in filters:
            s = s.filter("terms", tags__text_format=filters['tags'])
        s = s.query(q)
        response = s.execute()
        return response

    def search_bookmarks(self, **kwargs):
        print('search bookmarks')

    def search_users(self, **kwargs):
        print('search users')

    def search_tags(self, **kwargs):
        print('search users')


class ElasticSearchServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, port, **_ignored):
        if not self._instance:
            self._instance = ElasticSearchProvider()
        return self._instance


class PostgresProvider:

    def init_tags(self):
        self.tag_filters = {'include': [], 'exclude': []}
        self.attr_filters = {'include': [], 'exclude': []}

    def init_provider(self):
        logger.debug("Postgres provider initialized.")

    # ref: https://www.julienphalip.com/blog/adding-search-to-a-django-site-in-a-snap/
    def normalize_query(self, query_string,
                        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                        normspace=re.compile(r'\s{2,}').sub):
        ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
            and grouping quoted words together.
            Example:
                normalize_query('  some random  words "with   quotes  " and   spaces')
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

        '''
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

    def get_query(self, query_string, search_fields):
        ''' Returns a query, that is a combination of Q objects. That combination
            aims to search keywords within a model by testing the given search fields.

        '''
        query = None  # Query to search for every search term
        terms = self.normalize_query(query_string)
        for term in terms:
            or_query = None  # Query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    def build_filter_query(self, filter_array, filter_text, existing_query, exclude_ctx='include'):
        if len(filter_array) > 0:
            or_query = None
            # this is a workaround - I can't figure out how to chain these filters in a way
            # that applies AND logic to all items in the many-to-many relationship.
            # so instead we're chaining filters. if you can do this in a cleaner way please do PR.
            if 'tags' in filter_text:
                for val in filter_array:
                    self.tag_filters[exclude_ctx].append(Q(tags__text__icontains=val))
            elif 'attributes' in filter_text:
                for val in filter_array:
                    self.attr_filters[exclude_ctx].append(Q(attributes__display_name__icontains=val))
            else:
                for array_item in filter_array:
                    q = Q(**{filter_text: array_item})
                    if or_query is None:
                        or_query = q
                    else:
                        or_query = or_query | q if 'tags' not in filter_text else or_query & q
                if existing_query is None:
                    existing_query = or_query
                else:
                    existing_query = existing_query | or_query if 'count' not in filter_text else existing_query & or_query

        return existing_query

    def build_range_query(self, filter_obj, existing_query):
        if len(filter_obj['ranges']) < 1:
            return existing_query
        or_query = None
        for array_item in filter_obj['ranges']:
            q_high = Q(**{filter_obj['less_than']: array_item[0]})
            q_low = Q(**{filter_obj['greater_than']: array_item[1]})
            if or_query is None:
                or_query = (q_high & q_low)
            else:
                or_query = or_query | (q_high & q_low)
        if existing_query is None:
            existing_query = or_query
        else:
            existing_query = existing_query | or_query
        return existing_query

    def build_filters(self, filters, include):
        full_filters = None
        join_filters_arr = []
        for field in filters:
            join_filters = None
            if '_range' in field:
                join_filters = self.build_range_query(
                    filters[field], join_filters)
            else:
                for key in filters[field]:
                    join_filters = self.build_filter_query(
                        filters[field][key], key, join_filters, 'include' if include else 'exclude')
            if join_filters:
                if not include:
                    join_filters = ~join_filters
                if full_filters is None:
                    full_filters = join_filters
                else:
                    full_filters = Q(full_filters & join_filters)
                join_filters_arr.append(join_filters)
        return full_filters

    def process_result_tags(self, resultset):
        tags = []
        for result in resultset:
            if result and result.tags:
                for tag in result.tags.all():
                    tags.append(self.get_tags_dict(tag))
        return tags

    def process_results(self, resultset, page, obj, base_string='/search/?'):
        page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
        paginator = Paginator(resultset, page_size)
        count = paginator.count if resultset else 0
        resultset = paginator.get_page(page) if resultset else []
        next_params = None if not resultset or not resultset.has_next(
        ) else f"{base_string}limit={page_size}&page={page+1}&object_type={obj.__name__}"
        prev_params = None if not resultset or not resultset.has_previous(
        ) else f"{base_string}limit={page_size}&page={page-1}&object_type={obj.__name__}"
        return [resultset, {"count": count, "prev_params": prev_params, "next_params": next_params, "page_params": f"&object_type={obj.__name__}", "current_page": page}]

    # TODO: move to kwargs or obj. my god.
    def run_queries(self, filters, query, obj, trigram_fields, term, page=1, order_by='-updated_on', has_drafts=False, trigram_max=0.85, require_distinct=True, has_private=False, has_filterable=False):
        resultset = None
        page = int(page)
        import time
        start = time.time()
        # filter on query first, then use filters (more exact, used when searching within) to narrow
        if query is not None:
            resultset = obj.objects.filter(query).distinct()
            if resultset is not None and has_drafts:
                resultset = resultset.filter(draft=False)
            if resultset is not None and has_private:
                resultset = resultset.filter(is_private=False)
            end = time.time()
            length = end - start
            print(f'text execution: {length}')
            start = time.time()
        if filters is not None and (not not term and resultset is not None and len(resultset) > 0):
            if resultset is None and filters[0]:
                resultset = obj.objects.filter(filters[0])
            elif filters[0]:
                resultset = resultset.filter(filters[0])
                if hasattr(obj, 'tags'):
                    for tag in self.tag_filters['include']:
                        resultset = resultset.filter(tag)
                    for tag in self.tag_filters['exclude']:
                        resultset = resultset.filter(~tag)
                if hasattr(obj, 'attributes'):
                    for attribute in self.attr_filters['include']:
                        resultset = resultset.filter(attribute)
                    for attribute in self.attr_filters['exclude']:
                        resultset = resultset.filter(~attribute)
                resultset = resultset.distinct()
            if resultset is None and filters[1]:
                resultset = obj.objects.filter(filters[1])
            elif filters[1]:
                resultset = resultset.filter(filters[1])
        end = time.time()
        length = end - start
        print(f'filter execution: {length}')
        start = time.time()
        if resultset is not None and len(resultset) == 0 and query and not filters:
            # if exact matching & filtering produced no results, let's do limited trigram searching
            if len(trigram_fields) > 1:
                resultset = obj.objects.annotate(zero_distance=TrigramWordDistance(
                    term, trigram_fields[0])).annotate(one_distance=TrigramWordDistance(term, trigram_fields[1]))
                if filters[0] and filters[1]:
                    resultset = resultset.filter(
                        Q((Q(zero_distance__lte=trigram_max) | Q(one_distance__lte=trigram_max)) & filters[0] & filters[1]))
                elif filters[0]:
                    resultset = resultset.filter(
                        Q((Q(zero_distance__lte=trigram_max) | Q(one_distance__lte=trigram_max)) & filters[0]))
                elif filters[1]:
                    resultset = resultset.filter(
                        Q((Q(zero_distance__lte=trigram_max) | Q(one_distance__lte=trigram_max)) & filters[1]))
                else:
                    resultset = resultset.filter(zero_distance__lte=trigram_max).filter(
                        one_distance__lte=trigram_max)
                if resultset is not None and has_drafts:
                    resultset = resultset.filter(draft=False)
                if hasattr(obj, order_by.replace('-', '')):
                    resultset = resultset.order_by('zero_distance', 'one_distance', order_by)
                else:
                    resultset = resultset.order_by('zero_distance', 'one_distance', '-updated_on')
            else:
                resultset = obj.objects.annotate(
                    zero_distance=TrigramWordDistance(term, trigram_fields[0]))
                if filters[0] and filters[1]:
                    resultset = resultset.filter(
                        Q((Q(zero_distance__lte=trigram_max) & filters[0] & filters[1])))
                elif filters[0]:
                    resultset = resultset.filter(
                        Q((Q(zero_distance__lte=trigram_max) & filters[0])))
                elif filters[1]:
                    resultset = resultset.filter(
                        Q((Q(zero_distance__lte=trigram_max) & filters[1])))
                else:
                    resultset = resultset.filter(zero_distance__lte=trigram_max)
                if resultset is not None and has_drafts:
                    resultset = resultset.filter(draft=False)
                if hasattr(obj, order_by.replace('-', '')):
                    resultset = resultset.order_by('zero_distance', order_by) 
                else:
                    resultset = resultset.order_by('zero_distance', '-updated_on')
            require_distinct = False
        end = time.time()
        length = end - start
        print(f'trigram: {length}')
        start = time.time()
        if resultset and has_filterable:
            resultset = resultset.filter(filterable=True)
        if require_distinct and resultset:
            # remove any dupes & apply order_by
            if hasattr(obj, order_by.replace('-', '')):
                resultset = resultset.order_by(order_by)
            else:
                resultset = resultset.order_by('-updated_on')
            resultset = resultset.distinct()
        end = time.time()
        length = end - start
        print(f'result processing: {length}')
        start = time.time()
        tags = self.process_result_tags(resultset) if resultset and hasattr(obj, 'tags') else []
        end = time.time()
        length = end - start
        print(f'tags: {length}')
        start = time.time()
        final = self.process_results(resultset, page, obj), tags
        end = time.time()
        length = end - start
        print(f'final: {length}')
        return final

    def get_filters(self, search_object):
        include_filters = self.build_filters(
            search_object.filter.include_filters, True)
        exclude_filters = self.build_filters(
            search_object.filter.exclude_filters,False)
        return [include_filters, exclude_filters]

    def get_user_dict(self, users):
        users_dict = []
        for result in users:
            user = {
                'id': result.id,
                'username': result.username
            }
            users_dict.append(user)
        return users_dict

    def get_tags_dict(self, tag):
        return {"tag_type": tag.tag_type.label, "text": tag.text, "display_text": tag.display_text,
         "id": tag.id, "search_group": tag.tag_type.search_group.label if tag.tag_type.search_group else TagType.DEFAULT_SEARCH_GROUP_LABEL}

    def build_work_resultset(self, resultset, reserved_fields, return_tags=False):
        # build final resultset
        result_json = []
        all_tags = []
        for result in resultset:
            chapters = list(result.chapters.all())
            username = result.user.username
            tags = []
            for tag in result.tags.all():
                tag_dict = self.get_tags_dict(tag)
                tags.append(tag_dict)
            if return_tags:
                all_tags += tags
            attributes = []
            for attribute in result.attributes.all():
                attribute_dict = {"attribute_type": attribute.attribute_type.display_name, "name": attribute.name,
                                  "display_name": attribute.display_name, "id": attribute.id, "order": attribute.order}
                attributes.append(attribute_dict)
            languages = []
            for language in result.languages.all():
                languages.append(
                    {
                        "display_name": language.display_name
                    })
            users = self.get_user_dict(result.users.all())
            work_type = None if result.work_type is None else result.work_type.type_name
            result_dict = result.__dict__
            for field in reserved_fields:
                result_dict.pop(field, None)
            result_dict["user"] = username
            result_dict["users"] = users
            result_dict["work_type_name"] = work_type
            result_dict["tags"] = tags
            result_dict["attributes"] = attributes
            result_dict["languages_readonly"] = languages
            result_dict["chapter_count"] = len(chapters)
            if result.series_id:
                series = WorkSeries.objects.get(id=result.series_id).__dict__
                series.pop("_state")
                result_dict["series"] = series
            anthologies = AnthologyWork.objects.filter(work_id=result.id).all()
            if anthologies:
                result_dict["anthologies"] = []
                for anthology in anthologies:
                    result_dict["anthologies"].append({
                        "id": anthology.anthology.id,
                        "anthology": anthology.anthology.title
                    })
            result_json.append(result_dict)
        if not return_tags:
            return result_json
        else:
            return result_json, all_tags

    def build_bookmark_resultset(self, resultset, reserved_fields, return_tags=False):
        result_json = []
        all_tags = []
        for result in resultset:
            username = result.user.username
            tags = []
            for tag in result.tags.all():
                tag_dict = {"tag_type": tag.tag_type.label, "text": tag.text, "display_text": tag.display_text,
                            "id": tag.id}
                tags.append(tag_dict)
            if return_tags:
                all_tags += tags
            attributes = []
            for attribute in result.attributes.all():
                attribute_dict = {"attribute_type": attribute.attribute_type.display_name, "name": attribute.name,
                                  "display_name": attribute.display_name, "id": attribute.id, "order": attribute.order}
                attributes.append(attribute_dict)
            result_dict = result.__dict__
            result_dict["tags"] = tags
            result_dict["user"] = username
            result_dict["attributes"] = attributes
            if result.work:
                result_dict["work"] = {}
                result_dict["work"]["id"] = result.work.id
                result_dict["work"]["title"] = result.work.title
                result_dict["work"]["user_id"] = result.work.user_id
            for field in reserved_fields:
                result_dict.pop(field, None)
            result_json.append(result_dict)
        if not return_tags:
            return result_json
        else:
            return result_json, all_tags

    def build_collection_resultset(self, resultset, reserved_fields, return_tags=False):
        result_json = []
        all_tags = []
        for result in resultset:
            username = result.user.username
            tags = []
            for tag in result.tags.all():
                tag_dict = {"tag_type": tag.tag_type.label, "text": tag.text, "display_text": tag.display_text,
                            "id": tag.id}
                tags.append(tag_dict)
            if return_tags:
                all_tags += tags
            attributes = []
            for attribute in result.attributes.all():
                attribute_dict = {"attribute_type": attribute.attribute_type.display_name, "name": attribute.name,
                                  "display_name": attribute.display_name, "id": attribute.id, "order": attribute.order}
                attributes.append(attribute_dict)
            users = self.get_user_dict(result.users.all())
            result_dict = result.__dict__
            result_dict["tags"] = tags
            result_dict["attributes"] = attributes
            result_dict["user"] = username
            result_dict["users"] = users
            for field in reserved_fields:
                result_dict.pop(field, None)
            result_json.append(result_dict)
        if not return_tags:
            return result_json
        else:
            return result_json, all_tags

    def search_works(self, options, **kwargs):
        work_search = WorkSearch()
        work_search.from_dict(kwargs)
        work_filters = self.get_filters(work_search)
        # build query
        query = self.get_query(work_search.term, work_search.term_search_fields)
        if not query and not work_filters:
            return {'data': []}
        resultset = self.run_queries(work_filters, query, Work, [
                                     'title', 'summary'], work_search.term, kwargs['page'], options.get('order_by', '-updated_on'), True)
        result_json = self.build_work_resultset(resultset[0][0], work_search.reserved_fields)
        return {'pages': math.ceil(resultset[0][1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': result_json, 'page': resultset[0][1], 'tags': resultset[1]}

    def search_bookmarks(self, options, **kwargs):
        bookmark_search = BookmarkSearch()
        bookmark_search.from_dict(kwargs)
        bookmark_filters = self.get_filters(bookmark_search)
        query = self.get_query(bookmark_search.term, bookmark_search.term_search_fields)
        if not query and not bookmark_filters:
            return {'data': []}
        resultset = self.run_queries(bookmark_filters, query, Bookmark, [
                                     'title', 'description'], bookmark_search.term, kwargs.get('page', 1), options.get('order_by', '-updated_on'), True, .85, True, True)
        result_json = self.build_bookmark_resultset(resultset[0][0], bookmark_search.reserved_fields)
        return {'pages': math.ceil(resultset[0][1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': result_json, 'page': resultset[0][1], 'tags': resultset[1]}

    def search_collections(self, options, **kwargs):
        collection_search = CollectionSearch()
        collection_search.from_dict(kwargs)
        collection_filters = self.get_filters(collection_search)
        query = self.get_query(collection_search.term,
                               collection_search.term_search_fields)
        if not query and not collection_filters:
            return {'data': []}
        resultset = self.run_queries(collection_filters, query, BookmarkCollection, [
                                     'title', 'short_description'], collection_search.term, kwargs.get('page', 1), options.get('order_by', '-updated_on'), True)
        result_json = self.build_collection_resultset(resultset[0][0], collection_search.reserved_fields)
        return {'pages': math.ceil(resultset[0][1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': result_json, 'page': resultset[0][1], 'tags': resultset[1]}

    def search_users(self, options, **kwargs):
        user_search = UserSearch()
        user_search.from_dict(kwargs)
        query = self.get_query(user_search.term, user_search.term_search_fields)
        if query is None:
            return {'data': []}
        if hasattr(User, options.get('order_by', '-updated_on')):
            resultset = User.objects.filter(is_active=True).filter(query).order_by(options.get('order_by', '-updated_on'))[:20]
        else:
            resultset = User.objects.filter(is_active=True).filter(query).order_by('-updated_on')[:20]
        result_json = []
        for result in resultset:
            result_dict = result.__dict__
            for field in user_search.reserved_fields:
                result_dict.pop(field, None)
            result_json.append(result_dict)
        return {'pages': math.ceil(resultset.count()/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': result_json, 'page': {}, 'tags': []}

    def autocomplete_tags(self, term, tag_type, fetch_all=False):
        results = []
        resultset = None
        term = term.lower()
        if tag_type:
            resultset = Tag.objects.filter(
                tag_type__type_name=tag_type).filter(tag_type__filterable=True).filter(filterable=True).filter(Q(text__icontains=term) | Q(display_text__icontains=term))
        else:
            resultset = Tag.objects.annotate(zero_distance=TrigramWordDistance(term, 'text'))
            resultset = resultset.filter(zero_distance__lte=.85)
            resultset = resultset.order_by('zero_distance', 'text')
            resultset = resultset[:10]
        if resultset is None:
            resultset = Tag.objects.filter(
                tag_type__type_name=tag_type).filter(tag_type__filterable=True).filter(filterable=True) if fetch_all else []
        for result in resultset:
            usages = Work.objects.filter(tags__id=result.id, draft=False).count() + BookmarkCollection.objects.filter(tags__id=result.id, draft=False).count()
            results.append({"tag": result.text, "display_text": result.display_text, "count": usages,
                            "id": result.id, "type": result.tag_type.label, "type_name": result.tag_type.type_name})
        return results

    def autocomplete_works(self, term, user):
        results = []
        resultset = None
        term = term.lower()
        resultset = Work.objects.filter(user__id=user,draft=False).filter(
            Q(title__icontains=term) | Q(summary__icontains=term)).order_by('-updated_on')
        for result in resultset:
            work_dict = vars(result)
            if '_state' in work_dict:
                work_dict.pop('_state')
            results.append({"work": work_dict})
        return results

    def autocomplete_users(self, term, user):
        results = []
        resultset = None
        term = term.lower()
        resultset = User.objects.filter(
            Q(username__icontains=term))
        for result in resultset:
            user_dict = vars(result)
            if '_state' in user_dict:
                user_dict.pop('_state')
            results.append(user_dict)
        return results

    def autocomplete_series(self, term, user):
        results = []
        resultset = None
        term = term.lower()
        resultset = WorkSeries.objects.filter(works__work_users__user__id=user).filter(
            Q(title__icontains=term)).order_by('-updated_on')
        for result in resultset:
            series_dict = vars(result)
            if '_state' in series_dict:
                series_dict.pop('_state')
            results.append(series_dict)
        return results

    def autocomplete_anthologies(self, term, user):
        results = []
        resultset = None
        term = term.lower()
        resultset = Anthology.objects.filter(works__work_users__user__id=user).filter(
            Q(title__icontains=term)).order_by('-updated_on')
        for result in resultset:
            anthology_dict = vars(result)
            if '_state' in anthology_dict:
                anthology_dict.pop('_state')
            results.append(anthology_dict)
        return results

    def search_tags(self, options, **kwargs):
        tag_search = TagSearch()
        tag_search.from_dict(kwargs)
        tag_filters = self.get_filters(tag_search)
        query = self.get_query(tag_search.term, tag_search.term_search_fields)
        if not query and not tag_filters:
            return {'data': []}
        resultset = self.run_queries(tag_filters, query, Tag, [
                                     'text'], tag_search.term, kwargs.get('page', 1), options.get('order_by', '-updated_on'), False, 0.6, False, False, True)
        result_json = []
        if resultset is None:
            return result_json
        for result in resultset[0][0]:
            tag_type = result.tag_type.label
            result_dict = result.__dict__
            for field in tag_search.reserved_fields:
                result_dict.pop(field, None)
            result_dict['tag_type'] = tag_type
            result_json.append(result_dict)
        return {'pages': math.ceil(resultset[0][1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': result_json, 'page': resultset[0][1], 'tags': resultset[1]}

    def filter_by_tag(self, **kwargs):
        tag_search = TagSearch()
        work_search = WorkSearch()
        work_search.from_dict(kwargs['work_search'])
        work_filters = self.get_filters(work_search)
        bookmark_search = BookmarkSearch()
        bookmark_search.from_dict(kwargs['bookmark_search'])
        bookmark_filters = self.get_filters(bookmark_search)
        collection_search = CollectionSearch()
        collection_search.from_dict(kwargs['collection_search'])
        collection_filters = self.get_filters(collection_search)

        page = kwargs['page'] if 'page' in kwargs else 1
        

        if 'page' in kwargs['work_search']:
            work_search.page = int(kwargs['work_search']['page'])
        if 'page' in kwargs['bookmark_search']:
            bookmark_search.page = int(kwargs['bookmark_search']['page'])
        if 'page' in kwargs['collection_search']:
            collection_search.page = int(kwargs['collection_search']['page'])

        tag = Tag.objects.get(pk=kwargs['tag_id'])
        works = Work.objects.filter(tags__id__exact=tag.id)
        if work_filters[0]:
            works = works.filter(work_filters[0])
        if work_filters[1]:
            works = works.filter(work_filters[1])
        works = works.filter(draft=False).distinct().order_by('-updated_on')
        bookmarks = Bookmark.objects.filter(tags__id__exact=tag.id)
        if bookmark_filters[0]:
            bookmarks = bookmarks.filter(bookmark_filters[0])
        if bookmark_filters[1]:
            bookmarks = bookmarks.filter(bookmark_filters[1])
        bookmarks = bookmarks.filter(draft=False).order_by('-updated_on').distinct()
        collections = BookmarkCollection.objects.filter(tags__id__exact=tag.id)
        if collection_filters[0]:
            collections = collections.filter(collection_filters[0])
        if collection_filters[1]:
            collections = collections.filter(collection_filters[1])
        collections = collections.filter(draft=False).order_by('-updated_on').distinct()

        base_string = f'/search/?tag_id={kwargs["tag_id"]}&'

        works_processed = self.process_results(works, work_search.page, Work, base_string)
        bookmarks_processed = self.process_results(bookmarks, bookmark_search.page, Bookmark, base_string)
        collections_processed = self.process_results(collections, collection_search.page, BookmarkCollection, base_string)

        # tag result object
        result_json = []
        tag_type = tag.tag_type.label
        result_dict = tag.__dict__
        for field in tag_search.reserved_fields:
            result_dict.pop(field, None)
        result_dict['tag_type'] = tag_type
        result_json.append(result_dict)
        tag_results = {'pages': math.ceil(1/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': result_json, 'page': {'count': len(result_json)}}

        work_data, work_tag_data = self.build_work_resultset(works_processed[0], work_search.reserved_fields, True)
        bookmark_data, bookmark_tag_data = self.build_bookmark_resultset(bookmarks_processed[0], bookmark_search.reserved_fields, True)
        collection_data, collection_tag_data = self.build_collection_resultset(collections_processed[0], collection_search.reserved_fields, True)
        work_results = {'pages': math.ceil(works_processed[1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': work_data, 'tags': work_tag_data, 'page': works_processed[1]}
        bookmark_results = {'pages': math.ceil(bookmarks_processed[1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': bookmark_data, 'tags': bookmark_tag_data, 'page': bookmarks_processed[1]}
        collection_results = {'pages': math.ceil(collections_processed[1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': collection_data, 'tags': collection_tag_data, 'page': collections_processed[1]}
        results = {'work': work_results, 'bookmark': bookmark_results, 'collection': collection_results,
                   'tag': tag_results, 'user': {'data': [], 'page': {}}}
        return results

    def filter_by_attribute(self, **kwargs):
        work_search = WorkSearch()
        work_search.from_dict(kwargs['work_search'])
        work_filters = self.get_filters(work_search)
        bookmark_search = BookmarkSearch()
        bookmark_search.from_dict(kwargs['bookmark_search'])
        bookmark_filters = self.get_filters(bookmark_search)
        collection_search = CollectionSearch()
        collection_search.from_dict(kwargs['collection_search'])
        collection_filters = self.get_filters(collection_search)

        page = kwargs['page'] if 'page' in kwargs else 1

        if 'page' in kwargs['work_search']:
            work_search.page = int(kwargs['work_search']['page'])
        if 'page' in kwargs['bookmark_search']:
            bookmark_search.page = int(kwargs['bookmark_search']['page'])
        if 'page' in kwargs['collection_search']:
            collection_search.page = int(kwargs['collection_search']['page'])

        attribute = AttributeValue.objects.get(pk=kwargs['attr_id'])
        works = Work.objects.filter(attributes__id__exact=attribute.id)
        if work_filters[0]:
            works = works.filter(work_filters[0])
        if work_filters[1]:
            works = works.filter(work_filters[1])
        works = works.filter(draft=False).order_by('-updated_on').distinct()
        bookmarks = Bookmark.objects.filter(attributes__id__exact=attribute.id)
        if bookmark_filters[0]:
            bookmarks = bookmarks.filter(bookmark_filters[0])
        if bookmark_filters[1]:
            bookmarks = bookmarks.filter(bookmark_filters[1])
        bookmarks = bookmarks.filter(draft=False).order_by('-updated_on').distinct()
        collections = BookmarkCollection.objects.filter(attributes__id__exact=attribute.id)
        if collection_filters[0]:
            collections = collections.filter(collection_filters[0])
        if collection_filters[1]:
            collections = collections.filter(collection_filters[1])
        collections = collections.filter(draft=False).order_by('-updated_on').distinct()

        base_string = f'/search/?attr_id={kwargs["attr_id"]}&'

        works_processed = self.process_results(works, work_search.page, Work, base_string)
        bookmarks_processed = self.process_results(bookmarks, bookmark_search.page, Bookmark, base_string)
        collections_processed = self.process_results(collections, bookmark_search.page, BookmarkCollection, base_string)

        # tag result object
        tag_results = {'pages': 0, 'data': {}, 'page': {'count': 0}}

        work_data, work_tag_data = self.build_work_resultset(works_processed[0], work_search.reserved_fields, True)
        bookmark_data, bookmark_tag_data = self.build_bookmark_resultset(bookmarks_processed[0],
                                                                         bookmark_search.reserved_fields, True)
        collection_data, collection_tag_data = self.build_collection_resultset(collections_processed[0],
                                                                               collection_search.reserved_fields, True)
        work_results = {'pages': math.ceil(works_processed[1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': work_data, 'tags': work_tag_data, 'page': works_processed[1]}
        bookmark_results = {'pages': math.ceil(bookmarks_processed[1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': bookmark_data, 'tags': bookmark_tag_data, 'page': bookmarks_processed[1]}
        collection_results = {'pages': math.ceil(collections_processed[1]['count']/settings.REST_FRAMEWORK.get('page_size', 10)), 'data': collection_data, 'tags': collection_tag_data, 'page': collections_processed[1]}
        results = {'work': work_results, 'bookmark': bookmark_results, 'collection': collection_results,
                   'tag': tag_results, 'user': {'data': [], 'page': {}}}
        return results

    def filter_by_work_type(self, **kwargs):
        work_type_id = kwargs.get('work_type_id')
        work_search = WorkSearch()
        work_search.from_dict(kwargs['work_search'])
        work_filters = self.get_filters(work_search)

        if 'page' in kwargs['work_search']:
            work_search.page = int(kwargs['work_search']['page'])

        works = Work.objects.filter(work_type__id__exact=work_type_id)
        if work_filters[0]:
            works = works.filter(work_filters[0])
        if work_filters[1]:
            works = works.filter(work_filters[1])
        works = works.filter(draft=False).order_by('-updated_on').distinct().prefetch_related('tags')
        tags = []
        for work in works:
            for tag in work.tags.all():
                tag_dict = {"tag_type": tag.tag_type.label, "text": tag.text, "display_text": tag.display_text,
                            "id": tag.id}
                tags.append(tag_dict)

        base_string = f'?work_type={work_type_id}&'

        works_processed = self.process_results(works, work_search.page, Work, base_string)
        pages = math.ceil(works_processed[1]['count']/settings.REST_FRAMEWORK.get('page_size', 10))
        data = self.build_work_resultset(works_processed[0], work_search.reserved_fields)
        page = works_processed[1]
        work_results = {'pages': pages, 'data': data, 'page': page, 'tags': tags}
        results = {'work': work_results, 'bookmark': {'pages': 0, 'data': [], 'page': {'count': 0}},
                   'collection': {'pages': 0, 'data': [], 'page': {'count': 0}}, 'tag': {'pages': 0, 'data': [], 'page': {'count': 0}},
                   'user': {'data': [], 'page': {'count': 0}}}
        return results


class PostgresServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, **_ignored):
        if not self._instance:
            self._instance = PostgresProvider()
        return self._instance


factory = object_factory.ObjectFactory()
factory.register_builder('ELASTICSEARCH', ElasticSearchServiceBuilder())
factory.register_builder('POSTGRES', PostgresServiceBuilder())
factory.register_builder('Default', PostgresServiceBuilder())
