#!/usr/bin/env python

import gedcom

project = 'gedcom'
copyright = '2018, Dave Shawley'
version = gedcom.version
release = '.'.join(str(c) for c in gedcom.version_info[:2])

needs_sphinx = '1.0'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]
source_suffix = '.rst'
master_doc = 'index'
pygments_style = 'sphinx'
html_theme = 'alabaster'
html_sidebars = {
    '**': ['about.html', 'navigation.html', 'searchbox.html'],
}
html_theme_options = {
    'github_user': 'dave-shawley',
    'github_repo': 'gedcom',
    'github_banner': True,
}
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}
