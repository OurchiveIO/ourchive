import re

def parse_work_id_from_ao3_url(url):
    if 'archiveofourown' in url:
        exp = r'(?<=archiveofourown.org/works/)([0-9]*)'
        match = re.search(exp, url)
        return match.group(0)
    else:
        return url