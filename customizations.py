"""
Most functions from this file were nearly identical to the customizations
found in bibtexparser.customization, but with minor changes in order to work
with the system.
"""
import re

texToUtf = {
    "{\\'{}}": "\\[CloseCurlyQuote]",
    "{\\`{a}}": "à",
    "{\\'{a}}": "á",
    "{\\\"{a}}": "ä",
    "{\\'{c}}": "ć",
    "{\\c{c}}": "ç",
    "{\\'{e}}": "é",
    "{\\`{e}}": "è",
    "{\\^{e}}": "ê",
    "{\\k{e}}": "ę",
    "{\\'{E}}": "É",
    "{\\u{g}}": "ğ",
    "{\\`{i}}": "ì",
    "{\\i}": "ı",
    "{\\\"{i}}": "ï",
    "{\\l}": "ł",
    "{\\'{o}}": "ó",
    "{\\^{o}}": "ô",
    "{\\\"{o}}": "ö",
    "{\\\"{O}}": "Ö",
    "{\\'{s}}": "ś",
    "{\\v{s}}": "š",
    "{\\'{S}}": "Ś",
    "{\\v{z}}": "ž",
    "{\\`{u}}": "ù",
    "{\\'{u}}": "ú",
    "{\\\"{u}}": "ü",
    "{\\\"{u}}": "ü",
    "{\\\"{U}}": "Ü",
    "\\`a": "à",  # Without brackets
    "\\'a": "á",
    "\\\"a": "ä",
    "\\'c": "ć",
    "\\'e": "é",
    "\\`e": "è",
    "\\^e": "ê",
    "\\'E": "É",
    "\\`i": "ì",
    "\\i": "ı",
    "\\\"i": "ï",
    "\\l": "ł",
    "\\'o": "ó",
    "\\^o": "ô",
    "\\\"o": "ö",
    "\\\"O": "Ö",
    "\\'s": "ś",
    "\\'S": "Ś",
    "\\`u": "ù",
    "\\'u": "ú",
    "\\\"u": "ü",
    "\\\"u": "ü",
    "\\\"U": "Ü",
    "\\textasciitilde ": "~"
}


# bibtex parser customizations
def customizations(record):
    record = name_fixer(record, 'author', False)  # Formats names
    record = name_fixer(record, 'editor', False)  # Formats names
    record = page_double_hyphen(record)  # Converts pages to --
    record = keyword(record)  # Converts 'keyword' to a list
    record = utf_fixer(record)  # fixes latex to utf
    record = strip_brackets(record)  # Removes '{' and '}'
    record = month(record)  # Changes month to full name

    return record


def name_fixer(record, ty, last_first=True):
    '''
    Similar to bibtexparser's `author` function, but generalized
    '''
    if ty in record:
        if record[ty]:
            names = record[ty].replace('\n', ' ').split(' and ')
            names = [i.strip() for i in names]
            names = getnames(names, last_first)
            # Convert to string "name, name, name and name"
            record[ty] = ', '.join(names[:-2] + [' and '.join(names[-2:])])
        else:
            del record[ty]
    return record


def utf_fixer(record):
    """
    Needs to come before `strip_brackets`
    """
    return replacer(record, texToUtf)


def strip_brackets(record):
    """
    Strips brackets
    """
    return replacer(record, {'{': '', '}': ''})


def replacer(record, dictionary):
    """
    Based off bibtexparser's `add_plaintext_fields` function, but inplace
    """
    def _replace(string):
        for key in dictionary:
            string = string.replace(key, dictionary[key])
        return string

    for key in list(record.keys()):
        if isinstance(record[key], str):
            record[key] = _replace(record[key])
        elif isinstance(record[key], dict):
            record[key] = {
                subkey: _replace(value)
                for subkey, value in record[key].items()
            }
        elif isinstance(record[key], list):
            record[key] = [
                _replace(value)
                for value in record[key]
            ]
    return record


def month(record):
    """
    Fix months to full string
    """
    mDict = {
        '1': 'January',
        '2': 'February',
        '3': 'March',
        '4': 'April',
        '5': 'May',
        '6': 'June',
        '7': 'July',
        '8': 'August',
        '9': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December',
        'jan': 'January',
        'feb': 'February',
        'mar': 'March',
        'apr': 'April',
        'may': 'May',
        'jun': 'June',
        'jul': 'July',
        'aug': 'August',
        'sep': 'September',
        'oct': 'October',
        'nov': 'November',
        'dec': 'December',
    }
    if "month" in record:
        if record['month']:
            if record['month'].lower() in mDict:
                record['month'] = mDict[record['month'].lower()]
        else:
            del record['month']
    return record


def getnames(names, last_first=True):
    """
    A direct copy of `getnames` from bibtexparser, but changes format
    """
    tidynames = []
    for namestring in names:
        namestring = namestring.strip()
        if len(namestring) < 1:
            continue
        if ',' in namestring:
            namesplit = namestring.split(',', 1)
            last = namesplit[0].strip()
            firsts = [i.strip() for i in namesplit[1].split()]
        else:
            namesplit = namestring.split()
            last = namesplit.pop()
            firsts = [i.replace('.', '. ').strip() for i in namesplit]
        if last in ['jnr', 'jr', 'junior']:
            last = firsts.pop()
        for item in firsts:
            if item in ['ben', 'van', 'der', 'de', 'la', 'le']:
                last = firsts.pop() + ' ' + last
        if last_first:
            tidynames.append(last + ", " + ' '.join(firsts))
        else:
            tidynames.append(' '.join(firsts) + ' ' + last)
    return tidynames


def page_double_hyphen(record):
    """
    Similar to bibtexparser's version, but with the ability to use html
    """
    output_type = 'html'
    if "pages" in record:
        # hyphen, non-breaking hyphen, en dash, em dash, hyphen-minus,
        # minus sign
        separators = [u'‐', u'‑', u'–', u'—', u'-', u'−']
        for separator in separators:
            if separator in record["pages"]:
                pages = record["pages"].split(separator)
                p = [i.strip().strip(separator) for i in pages]
                if output_type == 'html':
                    record["pages"] = p[0] + '&mdash;' + p[-1]
                else:
                    record["pages"] = p[0] + '--' + p[-1]
    return record


def keyword(record, sep=',|;', joiner=','):
    """
    Splits and joins keywords in order to standardize a little
    """
    if "keyword" in record:
        keywords = re.split(sep, record["keyword"].replace('\n', ''))
        record["keyword"] = joiner.join([i.strip() for i in keywords])

    return record
