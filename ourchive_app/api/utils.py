from api.models import OurchiveSetting
from django.core.exceptions import ObjectDoesNotExist


def convert_boolean(string_bool):
    if string_bool.lower() in ['true', 'yes', 'y', '1']:
        return True
    elif string_bool.lower() in ['false', 'no', 'n', '0']:
        return False
    else:
        raise ValueError("Value is not a boolean.")


def get_star_count():
    try:
        if OurchiveSetting.objects.get(name='Rating Star Count') is not None:
            star_count = [x for x in range(
                1, int(OurchiveSetting.objects.get(name='Rating Star Count').value) + 1)]
        else:
            star_count = list(range(1, 5))
    except ObjectDoesNotExist:
        star_count = list(range(1, 5))
    return star_count
