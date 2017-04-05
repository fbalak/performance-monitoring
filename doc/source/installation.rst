============
Installation
============

Note: node-agent is required for logging(functional dependency)

1. Install performance-monitoring::

   yum install tendrl-performance-monitoring

2. Configure performance-monitoring::

    Open /etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml
   
    update -->

    etcd_connection = <IP of etcd server>

    time_series_db_server = <IP of graphite server>

    api_server_addr = <IP of current node>

3. Initialize and start graphite services::

    /usr/lib/python2.7/site-packages/graphite/manage.py syncdb --noinput

    chown apache:apache /var/lib/graphite-web/graphite.db

    systemctl enable carbon-cache

    systemctl start carbon-cache

4. Restart httpd

    systemctl restart httpd

5. Enable and start performance-monitoring service::

   systemctl enable tendrl-performance-monitoring

   systemctl start tendrl-performance-monitoring

Note: 

For more detailed steps please follow: 
https://github.com/Tendrl/documentation/wiki/Tendrl-Package-Installation-Reference