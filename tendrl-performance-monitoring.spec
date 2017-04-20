Name: tendrl-performance-monitoring
Version: 1.2.3
Release: 1%{?dist}
BuildArch: noarch
Summary: Module for Tendrl Performance Monitoring
Source0: %{name}-%{version}.tar.gz
License: LGPLv2+
URL: https://github.com/Tendrl/performance-monitoring

BuildRequires: python-gevent
BuildRequires: pytest
BuildRequires: systemd
BuildRequires: python-mock
BuildRequires: python-six
BuildRequires: python-urllib3

Requires: graphite-web >= 0.9.15
Requires: python-flask >= 0.10.1
Requires: python-carbon >= 0.9.15
Requires: python-urllib3
Requires: python-whisper >= 0.9.15
Requires: tendrl-commons

%description
Python module for Tendrl Performance Monitoring

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
install -m  0755  --directory $RPM_BUILD_ROOT%{_var}/log/tendrl/performance-monitoring
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/performance-monitoring
install -Dm 0644 tendrl-performance-monitoring.service $RPM_BUILD_ROOT%{_unitdir}/tendrl-performance-monitoring.service
install -Dm 0644 etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/performance-monitoring/performance-monitoring.conf.yaml
install -Dm 0644 etc/tendrl/performance-monitoring/logging.yaml.timedrotation.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/performance-monitoring/performance-monitoring_logging.yaml
install -Dm 0644 etc/tendrl/performance-monitoring/monitoring_defaults.yaml $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/performance-monitoring/monitoring_defaults.yaml
install -Dm 0644 etc/tendrl/performance-monitoring/graphite-web.conf.sample $RPM_BUILD_ROOT%{_sysconfdir}/performance-monitoring/graphite-web.conf
install -Dm 0644 etc/tendrl/performance-monitoring/carbon.conf.sample $RPM_BUILD_ROOT%{_sysconfdir}/performance-monitoring/carbon.conf

%post
%systemd_post tendrl-performance-monitoring.service
if [ $1 -eq 1 ] ; then
    mv /etc/carbon/carbon.conf /etc/carbon/carbon.conf.%{name}
    mv /etc/httpd/conf.d/graphite-web.conf /etc/httpd/conf.d/graphite-web.conf.%{name}
    ln -s /etc/performance-monitoring/carbon.conf /etc/carbon/carbon.conf
    ln -s /etc/performance-monitoring/graphite-web.conf /etc/httpd/conf.d/graphite-web.conf
fi

%preun
%systemd_preun tendrl-performance-monitoring.service
if [ "$1" = 0 ] ; then
    rm -fr etc/carbon/carbon.conf /etc/httpd/conf.d/graphite-web.conf > /dev/null 2>&1
    mv /etc/carbon/carbon.conf.%{name} /etc/carbon/carbon.conf
    mv /etc/httpd/conf.d/graphite-web.conf.%{name} /etc/httpd/conf.d/graphite-web.conf
fi

%postun
%systemd_postun_with_restart tendrl-performance-monitoring.service

%check
py.test -v tendrl/performance_monitoring/tests || :

%files -f INSTALLED_FILES
%dir %{_var}/log/tendrl/performance-monitoring
%dir %{_sysconfdir}/tendrl/performance-monitoring
%config %{_sysconfdir}/tendrl/performance-monitoring/monitoring_defaults.yaml
%config %{_sysconfdir}/tendrl/performance-monitoring/performance-monitoring.conf.yaml
%config %{_sysconfdir}/tendrl/performance-monitoring/performance-monitoring_logging.yaml
%config(noreplace) %{_sysconfdir}/performance-monitoring/graphite-web.conf
%config(noreplace) %{_sysconfdir}/performance-monitoring/carbon.conf
%doc README.rst
%license LICENSE
%{_unitdir}/tendrl-performance-monitoring.service

%changelog
* Thu Apr 20 2017 Rohan Kanade <rkanade@redhat.com> - 1.2.3-1
- Release tendrl-performance-monitoring v1.2.3

* Wed Apr 05 2017 Rohan Kanade <rkanade@redhat.com> - 1.2.2-1
- Release tendrl-performance-monitoring v1.2.2

* Wed Jan 18 2017 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 0.0.1-1
- Initial build.
