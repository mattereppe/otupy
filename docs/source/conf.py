# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.insert(0, os.path.abspath('./'))


# -- Project information -----------------------------------------------------

project = "otupy"
copyright = "2024, Matteo Repetto"
author = "Matteo Repetto"


# -- General configuration ---------------------------------------------------
# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
#"sphinx_autodoc_typehints",
#'enum_tools.autoenum',
]

intersphinx_mapping = {
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

autosummary_generate = True  # Turn on sphinx.ext.autosummary
autosummary_filename_map = {'otupy.core.target.Target': 'otupy.core.target.Targetclass',
'otupy.core.target.target': 'otupy.core.target.targetfun',
'otupy.core.transfer.Transfer': 'otupy.core.transfer.Transferclass',
'otupy.core.actuator.actuator': 'otupy.core.actuator.actuatorfun',
}

#autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
autoclass_content = "class"  # Do not add __init__ doc to class summary -> __init__ special member must be added in class template!!!
html_show_sourcelink = False  # Remove 'view source code' from top of page (for html, not python)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
nbsphinx_allow_errors = True  # Continue through Jupyter errors
#autodoc_typehints = "description" # Sphinx-native method. Not as good as sphinx_autodoc_typehints
add_module_names = False # Remove namespaces from class/method signatures


templates_path = ["_templates"]

# -- Options for EPUB output
epub_show_urls = "footnote"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# This is necessary to explicitely document __init__ as s separate method
#autodoc_default_options = {
#    'special-members': '__init__',
##    'exclude-members': '__weakref__'
#}
#autodoc_skip_member = False
#def skip(app, what, name, obj, would_skip, options):
#	if name == "__init__":
#		return False
#	return would_skip
#
#def setup(app):
#	app.connect("autodoc-skip-member", skip)
