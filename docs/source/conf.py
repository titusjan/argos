# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Argos'
copyright = '2022, Pepijn Kenter'
author = 'Pepijn Kenter'
release = '0.4.3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',     # Read-the-docs theme
    'sphinx.ext.napoleon',  # Support for Google style docstrings
]

templates_path = ['_templates']
exclude_patterns = []

add_module_names = False
# python_use_unqualified_type_names = True  # Doesn't seem to make a difference.
modindex_common_prefix = ['argos.']

autodoc_class_signature = "separated"
autodoc_typehints = "both"

# Doesn't work nicely with: autodoc_typehints = "both". It duplicates parameters, first with
# description, then with teyp
#napoleon_use_param = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'style_external_links': True}
