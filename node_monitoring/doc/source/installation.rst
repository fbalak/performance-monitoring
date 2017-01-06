============
Installation
============

Since there is no stable release yet, the only option is to install the project
from the source. This needs to be installed on tendrl monitored nodes.

Development version from the source
-----------------------------------

1. First install https://github.com/Tendrl/common from the source code::

    $ git clone https://github.com/Tendrl/common.git
    $ cd common
    $ mkvirtualenv common
    $ pip install .

2. Then install node_monitoring itself::

    $ git clone https://github.com/Tendrl/performance_monitoring.git
    $ cd performance_monitoring
    $ python setup.py install
    $ pip install .

3. Move ``node_monitoring/tendrl/node_monitoring/commands/config_manager.py`` to ``/usr/bin/config_manager``
   
   ``mv node_monitoring/tendrl/node_monitoring/commands/config_manager.py /usr/bin/config_manager``

4. Create a folder ``/etc/collectd_template/``

   ``mkdir /etc/collectd_template/``

5. Copy the contents of ``node_monitoring/tendrl/node_monitoring/templates/`` to ``/etc/collectd_template/``

   ``cp node_monitoring/tendrl/node_monitoring/templates/ /etc/collectd_template/``

