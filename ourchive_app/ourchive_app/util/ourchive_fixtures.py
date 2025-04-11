import yaml
from core.models import OurchiveSetting, NotificationType, WorkType, TagType, AttributeType, AttributeValue, SearchGroup, Language
from etl.models import ObjectMapping

data_keys = {'core.ourchivesetting': OurchiveSetting,
             'core.notificationtype': NotificationType,
             'etl.objectmapping': ObjectMapping,
             'core.worktype': WorkType,
             'core.attributetype': AttributeType,
             'core.attributevalue': AttributeValue,
             'core.tagtype': TagType,
             'core.searchgroup': SearchGroup,
             'core.language': Language}


def load_data(path, filename):
    with open(f"{path}{filename}") as stream:
        try:
            objs_added = 0
            settings = yaml.safe_load(stream)
            for setting in settings:
                model_obj = data_keys[setting['model']]
                obj = model_obj(**setting['fields'])
                if setting.get('pk', None):
                    obj_id = setting.get('pk')
                    if model_obj.objects.filter(id=obj_id).count() > 0:
                        continue
                    obj.id = obj_id
                obj.save()
                objs_added += 1
            return objs_added
        except yaml.YAMLError as exc:
            print(exc)
