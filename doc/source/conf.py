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
sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'redvypr'
copyright = '2021, Peter Holtermann'
author = 'Peter Holtermann'

# The full version, including alpha/beta/rc tags
release = '0.3.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# Peter: from here https://pypi.org/project/sphinx-autopackagesummary/
#extensions = ['sphinx.ext.napoleon','sphinx.ext.autosectionlabel','sphinx.ext.autosummary', 'sphinx_autopackagesummary','sphinx.ext.autodoc',]
extensions = ['sphinx.ext.napoleon','sphinx.ext.autosectionlabel','sphinx.ext.autosummary', 'sphinx.ext.autodoc',]


autosummary_generate = True

autodoc_mock_imports = ["time", "serial","serial.tools","datetime","logging","queue","yaml","PyQt5","pkg_resources","pyqtgraph","numpy","inspect","threading","multiprocessing","socket","argparse","importlib","glob","pathlib","signal","QtWidgets", "QtCore", "QtGui","netCDF4","copy","threading","socket","serial.tools.list_ports"]#,"redvypr.devices"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['~']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
