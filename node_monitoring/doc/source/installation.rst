===========
Environment
===========

1. Install collectd and collectd-ping


============
Installation
============

Since there is no stable release yet, the only option is to install the project
from the source. This needs to be installed on tendrl monitored nodes.

Development version from the source
-----------------------------------

1. Install http://github.com/tendrl/commons from the source code::

    Please find commons installation steps at: https://github.com/Tendrl/commons/blob/master/doc/source/installation.rst

2. Then install node_monitoring itself::

    $ git clone https://github.com/Tendrl/performance-monitoring.git
    $ cd performance_monitoring/node_monitoring
    $ python setup.py install
    $ mkvirtualenv node-monitoring
    $ pip install .

3. Copy ``node_monitoring/tendrl/node_monitoring/commands/config_manager.py`` to ``/usr/bin/config_manager``
   Assign 555 permissions to the copied files
   
   ``cp node_monitoring/tendrl/node_monitoring/commands/config_manager.py /usr/bin/config_manager``

4. Create a folder ``/etc/collectd_template/``

   ``mkdir /etc/collectd_template/``

5. Copy the contents of ``node_monitoring/tendrl/node_monitoring/templates/`` to ``/etc/collectd_template/``
   Assign 644 permission to whole ``/etc/collectd_template/`` directory

   ``cp node_monitoring/tendrl/node_monitoring/templates/ /etc/collectd_template/``

6. Copy the contents of ``node_monitoring/tendrl/node_monitoring/plugins/`` to ``/usr/lib64/collectd/``
   Assign 555 permissions to the copied files

7. Create the following directories::

    $ mkdir -p /var/log/tendrl/node-monitoring/
    $ mkdir $HOME/.tendrl/node-monitoring/
    $ mkdir -p /etc/tendrl/node-monitoring/

8. Create the following config files::

    $ cp etc/tendrl/node-monitoring/node-monitoring.conf.yaml.sample /etc/tendrl/node-monitoring/node-monitoring.conf.yaml
    $ cp etc/tendrl/node-monitoring/logging.yaml.timedrotation.sample /etc/tendrl/node-monitoring/node-monitoring_logging.yaml

9. Create a user tendrl-user with sudo permissions

10. Run::

    $ tendrl-node-monitoring
