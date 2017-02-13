Name: tendrl-node-monitoring
Version: 1.2
Release: 1%{?dist}
BuildArch: noarch
Summary: Module for Tendrl Performance Monitoring
Source0: %{name}-%{version}.tar.gz
License: LGPLv2+
URL: https://github.com/Tendrl/performance-monitoring/tree/master/node_monitoring

BuildRequires: pytest
BuildRequires: systemd
BuildRequires: python-mock

Requires: python-jinja2
Requires: tendrl-commons

%description
Python module for Tendrl Node Monitoring

%prep
%setup

# Remove bundled egg-info
rm -rf %{name}.egg-info

%build
%{__python} setup.py build

# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/collectd_template
install -m  0755  --directory $RPM_BUILD_ROOT%{_usr}/lib64/collectd
install -m  0755  --directory $RPM_BUILD_ROOT%{_var}/log/tendrl/node-monitoring
install -Dm 0644 tendrl-node-monitoring.service $RPM_BUILD_ROOT%{_unitdir}/tendrl-node-monitoring.service
install -Dm 0655 etc/tendrl/node-monitoring/node-monitoring.conf.yaml.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/node-monitoring/node-monitoring.conf.yaml
install -Dm 0655 etc/tendrl/node-monitoring/logging.yaml.timedrotation.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/node-monitoring/node-monitoring_logging.yaml
install -Dm 0655 tendrl/node_monitoring/commands/config_manager.py $RPM_BUILD_ROOT/usr/bin/config_manager
install -Dm 0655 tendrl/node_monitoring/templates/*.jinja $RPM_BUILD_ROOT%{_sysconfdir}/collectd_template/.
install -Dm 0655 tendrl/node_monitoring/plugins/* $RPM_BUILD_ROOT/usr/lib64/collectd/.

%post
%systemd_post tendrl-node-monitoring.service

%preun
%systemd_preun tendrl-node-monitoring.service

%postun
%systemd_postun_with_restart tendrl-node-monitoring.service

%check

%files -f INSTALLED_FILES
%dir %{_sysconfdir}/collectd_template
%dir %{_usr}/lib64/collectd/
%dir %{_var}/log/tendrl/node-monitoring
%{_sysconfdir}/collectd_template/
%{_usr}/lib64/collectd/
%{_usr}/bin/config_manager
%config %{_sysconfdir}/tendrl/node-monitoring/node-monitoring.conf.yaml
%config %{_sysconfdir}/tendrl/node-monitoring/node-monitoring_logging.yaml
%{_unitdir}/tendrl-node-monitoring.service

%changelog
* Thu Feb 02 2017 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 1.1-1
- Initial build.
