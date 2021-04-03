import os
import inspect
import re
import copy

"""
bibtexparser is a library which converts .bib files to python data structures
so that we can more easily handle them.

Documentation for bibtexparser
    https://bibtexparser.readthedocs.io/en/master/index.html
"""
import bibtexparser
from bibtexparser.bparser import BibTexParser
from customizations import customizations

from py_func import get_file_contents, put_file_contents

"""
The following are variables you are allowed to edit.
"""
# Format of how you want things to appear. If something is not present it is
#   replaced with the empty string. Check `type_reqs` for which fields are
#   required and which types are allowed.
# There is no default. If a format is present, the program will tell you so
#   and won't add the bib to the outputted data
formats = {
    'article': '{ID} {author}. {title}. {journaltitle}, {volume}{number}'
               + '{pages}, {month} {year}{note}',
    'book': '{ID} {author}. {title}. {series}{publisher}, {edition}{month} '
            + '{year}{note}',
    'incollection': '{ID} {author}. {title}. In {booktitle}. {publisher}, '
                    + '{month} {year}{note}',
    'inproceedings': '{ID} {author}. {title}. {booktitle}. {publisher}, '
                     + '{volume}{number} {month}, {year}{note}',
    'thesis': '{ID} {author}. {title}. {institution}. {month} {year}{note}',
    'phdthesis': '{ID} {author}. {title}. {institution}. {month} {year}{note}',
    'mastersthesis': '{ID} {author}. {title}. {institution}. {month} '
                     + '{year}{note}',
    'techreport': '{ID} {author}. {title}. {institution}. {volume}{number} '
                  + '{month} {year}{note}',
    'misc': '{ID} {author}. {title}. {howpublished} {year}{note}',
    'unpublished': '{author}. {title}. {howpublished} {year}{note}',
}


# Prepend and append are variables for what to prepend/append into each of
#   variables in the `formats` variable above.
# For example if `key_prepend[author] = 'Auth:'` then '{author}' will be
#   replaced with 'Auth:{author}'. Similarly for key_append. This is a
#   good place to put things in case a variable is not present without adding
#   to much empty punctuation.
key_prepend = {
    'ID': '<span class="cite-ID">[',
    'number': '<span class="cite-number">(',
    'pages': '<span class="cite-pages":',
}

key_append = {
    'edition': ' edition,</span>',
    'ID': ']</span>',
    'number': ')</span>',
    'series': ', </span>',
    'year': '. </span>',
}

# What text to encapsulate each citation. The variable '{ID}' may be used
#   to grab the ID of the citation.
cite_prepend = ''
cite_append = ''

# What text to encapsulate everything with.
global_prepend = ''
global_append = ''

# Allows for some "standard" prepends/appends to be created. Also, dictates
#   the output filetype. The following are
#   currently what we have:
#   'html' - key_prepend/key_append: Every key gets prepended with
#               '<span class="cite-{key}">' and appended with '</span>'.
#            cite_prepend/cite_append: Every citation gets prepended with
#               '<li class="citation" id="{key}">' and appended with '</li>'.
#            global_prepend/global_append: Every section gets prepended with
#               '<ul class="citations" id="citations">' and appended with
#               '</ul>'
#            All settings can be overriden above.
#            Outputs .html file
#   'markdown' - Same as default, but outputs .md file
#   '' - Default. Keeps everything empty. Outputs .txt file
output_type = 'html'

"""
Here are all bib types present in bibtex (ex: @article) with a list of what
fields are required for each. Note that aliases are built *into* this system
to allow different formatting if desired.

Here is the documentation for biblatex:
    http://ctan.mirror.globo.tech/macros/latex/contrib/biblatex/doc/biblatex.pdf
"""
type_reqs = {
    'article': ['author', 'title', 'journaltitle', ['year', 'date']],
    'book': ['author', 'title', ['year', 'date']],
    'mvbook': ['author', 'title', ['year', 'date']],
    'inbook': ['author', 'title', 'booktitle', ['year', 'date']],
    'bookinbook': ['author', 'title', 'booktitle', ['year', 'date']],
    'suppbook': ['author', 'title', 'booktitle', ['year', 'date']],
    'booklet': [['author', 'editor'], 'title', ['year', 'date']],
    'collection': ['editor', 'title', ['year', 'date']],
    'mvcollection': ['editor', 'title', ['year', 'date']],
    'incollection': ['author', 'title', 'booktitle', ['year', 'date']],
    'suppcollection': ['author', 'title', 'booktitle', ['year', 'date']],
    'dataset': [['author', 'editor'], 'title', ['year', 'date']],
    'manual': [['author', 'editor'], 'title', ['year', 'date']],
    'misc': [['author', 'editor'], 'title', ['year', 'date']],
    'online': [['author', 'editor'], 'title', ['year', 'date'],
               ['doi', 'eprint', 'url']],
    'electronic': [['author', 'editor'], 'title', ['year', 'date'],
                   ['doi', 'eprint', 'url']],
    'www': [['author', 'editor'], 'title', ['year', 'date'],
            ['doi', 'eprint', 'url']],
    'patent': ['author', 'title', 'number', ['year', 'date']],
    'periodical': ['editor', 'title', ['year', 'date']],
    'suppperiodical': [['author', 'editor'], 'title', ['year', 'date']],
    'proceedings': ['title', ['year', 'date']],
    'mvproceedings': ['title', ['year', 'date']],
    'inproceedings': ['author', 'title', 'booktitle', ['year', 'date']],
    'conference': ['author', 'title', 'booktitle', ['year', 'date']],
    'reference': ['editor', 'title', ['year', 'date']],
    'mvreference': ['editor', 'title', ['year', 'date']],
    'inreference': ['author', 'title', 'booktitle', ['year', 'date']],
    'report': ['author', 'title', 'type', 'institution', ['year', 'date']],
    'techreport': ['author', 'title', 'institution', ['year', 'date']],
    'thesis': ['author', 'title', 'type', 'institution', ['year', 'date']],
    'mastersthesis': ['author', 'title', 'institution', ['year', 'date']],
    'phdthesis': ['author', 'title', 'institution', ['year', 'date']],
    'software': [['author', 'editor'], 'title', ['year', 'date']],
    'unpublished': ['author', 'title', ['year', 'date']],
}


def var_replacer(string, replacers):
    retstr = copy.copy(string)

    # Look for anything with {text} for replacement
    matches = re.findall(r'(\{[^}]*})', retstr)
    for m in matches:
        # replace {key} with replacers[key]
        key = m[1:-1]
        s = ''
        if key in replacers:
            s = replacers[key]
        retstr = retstr.replace(m, s)
    return retstr


def format_bibtex(bib, ID, bibtype):
    """
    Uses the `formats` variable to create a string based on the bib. This
    assumes that the bib has already been through a processor
    """
    if bibtype not in type_reqs:
        bibtype = 'misc'

    for key in type_reqs[bibtype]:
        if isinstance(key, str):
            if key not in bib:
                print(f"Missing {key} from bib {ID}.")
                print("Not including entry.")
                return ''
        elif isinstance(key, list):
            not_found = True
            for i in key:
                if i in bib:
                    not_found = False
                    break
            if not_found:
                keys = ' or '.join(key)
                print(f"Missing {keys} from bib {ID}. Not including entry.")
                return ''

    if bibtype in formats:
        return var_replacer(formats[bibtype], bib)
    else:
        print(f"The format {bibtype} was never specified. Please create.")
        return ''


field_aliases = {
    'address': 'location',
    'annote': 'annotation',
    'archiveprefix': 'eprinttype',
    'journal': 'journaltitle',
    'key': 'sortkey',
    'pdf': 'file',
    'primaryclass': 'eprintclass',
    'school': 'institution',
}


if output_type == 'html':
    cite_prepend = '<li class="citation" id="{ID}">'
    cite_append = '</li>'
    global_prepend = '<ul class="citations" id="citations">'
    global_append = '</ul>'


def bibtex_to_string(bib, key_prepend, key_append, output_type=''):
    '''
    bib is a dict with the following keys:
        authors, title, year,note,
        journal, publisher, pages, eprint,
        month, volume, number, school, doi,series,
        edition, booktitle, institution, howpublished,
        ID, ENTRYTYPE
    '''

    bibstrd = {}

    for key in bib:
        val = copy.copy(bib[key])

        # Skip empty entries
        if val:
            # If we are using an alias, replace it
            if key in field_aliases:
                key = field_aliases[key]

            bibstrd[key] = ''
            if key in key_prepend:
                bibstrd[key] += key_prepend[key]
            elif output_type == 'html':
                bibstrd[key] += f'<span class="cite-{key}">'

            bibstrd[key] += val
            if key in key_append:
                bibstrd[key] += key_append[key]
            elif output_type == 'html':
                bibstrd[key] += '</span>'

    return bibstrd


# Get absolute path of this file
fn = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(fn))

# Get bib parser
parser = BibTexParser(common_strings=True)
parser.homogenize_fields = True
parser.ignore_nonstandard_types = False
parser.customization = customizations

# Go through every .bib file
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith(".bib"):
            bibfilename = file
            bibfilepath = os.path.join(root, file)

            # get file contents
            contents = get_file_contents(bibfilepath)

            retstr = global_prepend

            bibtex = bibtexparser.loads(contents, parser=parser)
            for i in bibtex.entries:
                bibstrings = bibtex_to_string(i, key_prepend, key_append, output_type)
                bibs = format_bibtex(bibstrings, i['ID'], i['ENTRYTYPE'])
                if bibs:
                    retstr += var_replacer(cite_prepend, i)
                    retstr += bibs
                    retstr += var_replacer(cite_append, i)
            retstr += global_append

            if output_type == 'html':
                output_filename = bibfilename.replace('.bib', '.html')
            elif output_type == 'markdown':
                output_filename = bibfilename.replace('.bib', '.md')
            else:
                output_filename = bibfilename.replace('.bib', '.txt')
            put_file_contents(path + "/" + output_filename, retstr)
