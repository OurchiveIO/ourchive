from django.core.exceptions import ObjectDoesNotExist
import nh3
import unidecode
from django.contrib.auth.models import AnonymousUser


def count_words(text):
    return len(text.split())


def convert_boolean(string_bool):
    if string_bool.lower() in ['true', 'yes', 'y', '1']:
        return True
    elif string_bool.lower() in ['false', 'no', 'n', '0']:
        return False
    else:
        raise ValueError("Value is not a boolean.")


def get_star_count(rating_star_count=None):
    star_count = list(range(1, 5))
    if rating_star_count is not None:
        rating_star_count = rating_star_count.value
        star_count = [x for x in range(
            1, int(rating_star_count) + 1)]
    return star_count


def clean_text(text, user=None):
    tags = set({'a', 'abbr', 'acronym', 'area', 'article', 'aside', 'b', 'bdi',
                'bdo', 'blockquote', 'br', 'caption', 'center', 'cite', 'code',
                'col', 'colgroup', 'data', 'dd', 'del', 'details', 'dfn', 'div',
                'dl', 'dt', 'em', 'figcaption', 'figure', 'footer', 'h1', 'h2',
                'h3', 'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'i',
                'ins', 'kbd', 'kbd', 'li', 'map', 'mark', 'nav', 'ol', 'p', 'pre',
                'q', 'rp', 'rt', 'rtc', 'ruby', 's', 'samp', 'small', 'source', 'span',
                'strike', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody',
                'td', 'th', 'thead', 'time', 'tr', 'tt', 'u', 'ul', 'var',
                'wbr', 'iframe', 'img', 'video'})
    attributes = {"*": {'style'},
                  "iframe": {'src', 'width', 'height', 'frameborder', 'allow', 'title', 'allowfullscreen'},
                  "a": {'href', 'alt', 'title', 'target'},
                  "source": {'src', 'type'},
                  "img": {'src', 'alt', 'width', 'height'},
                  "video": {'controls', 'width', 'height'}
                  }
    if user and not isinstance(user, AnonymousUser) and not user.can_upload_images:
        tags.remove('img')
        attributes.remove('video')
    if user and not isinstance(user, AnonymousUser) and not user.can_upload_video:
        tags.remove('video')
        attributes.remove('video')
    if user and not isinstance(user, AnonymousUser) and (not user.can_upload_video and not user.can_upload_audio and not user.can_upload_export_files and not user.can_upload_images):
        # if absolutely no upload permissions have been configured to be true then you also can't embed iframes
        tags.remove('iframe')
        attributes.remove('iframe')
    return nh3.clean(text, tags=tags, attributes=attributes)


def clean_tag_text(tag_text):
    return unidecode.unidecode(nh3.clean(tag_text.lower()))
