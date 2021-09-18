.. image:: https://api.codeclimate.com/v1/badges/b4282da53f20d20618aa/maintainability
   :target: https://codeclimate.com/github/snake-soft/django-oscar-product-tables/maintainability
   :alt: Maintainability

==============================
Product Table for Django-Oscar
==============================

This implements a nice and useful table view to manage Products and its data in one big table.
It is designed for the e-commerce framework `Oscar`_.

.. _`Oscar`: https://github.com/django-oscar/django-oscar


Product data that can be used:

* Data that is directly attached to the Product model including foreign key choices
* AttributeValues of the products
* StockRecord entries

With this piece of code you give your Shop managers a perfect overview.


Features
--------

* Load table with Ajax
* Load single form for every table cell that you want to change
* Submits the data with Ajax but shows validation errors to the frontend
* Filter the data by every column is possible (like you know from table calculation software)
* Manage all Data from all products without page reload


Installation
------------

Install using pip:

.. code-block:: bash

	pip install django-oscar-product-tables


.. code-block:: python

   # settings.py
   INSTALLED_APPS = [
       # ...
       'oscar_product_tables.apps.ProductTablesConfig',
       'oscar_product_tables.dashboard.apps.ProductTablesDashboardConfig',
       # ...
   ]

Create urls:

.. code-block:: python

   urlpatterns = [
       # ..
       path('dashboard/product_tables/', apps.get_app_config('product_tables_dashboard').urls),
       # ..
   ]


Add it as first button of catalogue in dashboard:

.. code-block:: python

   # settings.py
   OSCAR_DASHBOARD_NAVIGATION[1]['children'] = [
       {
           'label': _('Producttable'),
           'url_name': 'product_tables_dashboard:product-table',
       },
       *OSCAR_DASHBOARD_NAVIGATION[1]['children'],
   ]


Settings
--------

If you want to add some fields that are directly attached to the Product model:

.. code-block:: python

   # settings.py
   OSCAR_ATTACHED_PRODUCT_FIELDS = ['is_public', 'deposit', 'volume', 'weight',]
