# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('..'))

project = 'absscpi'
copyright = '2024, Bloomy Controls'
author = 'Bloomy Controls'
release = '1.0.0'

primary_domain = "py"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_copybutton',
]

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
root_doc = 'index'
source_suffix = '.rst'

manpages_url = 'https://www.man7.org/linux/man-pages/man{section}/{page}.{section}.html'

# include documentation from both the class level and __init__
autoclass_content = 'both'

autodoc_typehints = 'both'
autodoc_member_order = 'bysource'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'