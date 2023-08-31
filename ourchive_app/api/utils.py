from django.core.exceptions import ObjectDoesNotExist
import nh3
import unidecode


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


def clean_text(text):
    return nh3.clean(text, 
        tags={
            'a', 'abbr', 'acronym', 'area', 'article', 'aside', 'b', 'bdi',
            'bdo', 'blockquote', 'br', 'caption', 'center', 'cite', 'code',
            'col', 'colgroup', 'data', 'dd', 'del', 'details', 'dfn', 'div',
            'dl', 'dt', 'em', 'figcaption', 'figure', 'footer', 'h1', 'h2',
            'h3', 'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'i', 'img',
            'ins', 'kbd', 'kbd', 'li', 'map', 'mark', 'nav', 'ol', 'p', 'pre',
            'q', 'rp', 'rt', 'rtc', 'ruby', 's', 'samp', 'small', 'span',
            'strike', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody',
            'td', 'th', 'thead', 'time', 'tr', 'tt', 'u', 'ul', 'var', 'wbr',
            'iframe'
        }, 
        attributes={
            "*": {'style'}, 
            "iframe": {'src', 'width', 'height', 'frameborder', 'allow', 'title', 'allowfullscreen'},
            "img": {'src', 'alt', 'width', 'height'},
            "a": {'href', 'alt', 'title', 'target'}
        }
    )

def clean_tag_text(tag_text):
    return unidecode.unidecode(nh3.clean(tag_text.lower()))
