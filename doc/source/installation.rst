===========
Environment
===========

1. Install Etcd>=2.3.x && <3.x (https://github.com/coreos/etcd/releases/tag/v2.3.7)


============
Installation
============

Since there is no stable release yet, the only option is to install the project
from the source.

Development version from the source
-----------------------------------

1. Install http://github.com/tendrl/commons from the source code::

    Please find commons installation steps at: https://github.com/Tendrl/commons/blob/master/doc/source/installation.rst

2. Install performance monitoring itself::

    $ git clone https://github.com/Tendrl/performance-monitoring.git
    $ cd performance-monitoring
    $ mkvirtualenv performance-monitoring
    $ pip install .

Note that we use virtualenvwrapper_ here to activate ``performance-monitoring`` `python
virtual enviroment`_. This way, we install *performance monitoring* into the same virtual
enviroment which we have created during installation of *integration common*.

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/
.. _`python virtual enviroment`: https://virtualenv.pypa.io/en/stable/

3. Create the following directories::

    $ mkdir /var/log/tendrl/performance-monitoring
    $ mkdir $HOME/.tendrl/performance-monitoring/
    $ mkdir -p /etc/tendrl/performance-monitoring/

4. Create the following config files::

    $ cp etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml.sample /etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml
    $ cp etc/tendrl/performance-monitoring/logging.yaml.timedrotation.sample /etc/tendrl/performance-monitoring/performance-monitoring_logging.yaml
    $ cp etc/tendrl/performance-monitoring/monitoring_defaults.yaml /etc/tendrl/performance-monitoring/monitoring_defaults.yaml
    $ cp etc/tendrl/performance-monitoring/graphite-web.conf.sample /etc/httpd/conf.d/graphite-web.conf
    $ cp etc/tendrl/performance-monitoring/carbon.conf.sample /etc/carbon/carbon.conf

5. Edit ``/etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml`` as below

    Set the value of ``etcd_connection`` to the interface address on which etcd is accessible

    Set the value of ``etcd_port`` to the port on which etcd is accessible

    Set the value of ``time_series_db_server`` to the ip address of system on which time-series db(graphite) is installed

    Set the value of ``time_series_db_port`` to the port on which time-series db rest apis are accessible(default for graphite as configured by tendrl is 10080)

    Note: time_series_db_server and time_series_db_port are included in configuration because this provides an option for time-series db to not necessarily be co-resident with performance-monitoring. However, if its not co-resident with performance-monitoring, it needs to be configured manually.

6. Init graphite-db using ::

    /usr/lib/python2.7/site-packages/graphite/manage.py syncdb --noinput
    
7. Allow httpd access to graphite.db ::

    chown apache:apache /var/lib/graphite-web/graphite.db

8. Start carbon-cache and httpd ::

    service carbon-cache start
    service httpd restart

9. Run::

    $ tendrl-performance-monitoring

