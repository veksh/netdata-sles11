#
# spec file for package netdata
#
# Copyright (c) 2018 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


%define netdata_user    netdata
%define netdata_group   netdata
%if 0%{?suse_version} > 1220
%bcond_without systemd
%else
%bcond_with    systemd
%endif
Name:           netdata
Version:        1.10.0
Release:        2
Summary:        A system for distributed real-time performance and health monitoring
# netdata is GPL-3.0+ other licenses refer to included third-party software (see LICENSE.md)
License:        GPL-3.0-or-later AND MIT AND BSD-2-Clause AND BSD-3-Clause AND LGPL-2.1-only AND OFL-1.1 AND CC0-1.0
Group:          System/Monitoring
Url:            http://my-netdata.io/
Source0:        https://github.com/firehol/netdata/releases/download/v%{version}/netdata-%{version}.tar.gz
Source1:        netdata.init
Source2:        netdata.alarm-notify.bash3.sh
Patch1:         netdata-automake-no-dist-xz.patch
Patch2:         netdata-python-plugin-sles11.patch
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  dos2unix
BuildRequires:  fdupes
BuildRequires:  libcap-devel
BuildRequires:  libmnl-devel
BuildRequires:  libuuid-devel
BuildRequires:  pkgconfig
BuildRequires:  xz
BuildRequires:  zlib-devel
Requires(pre):  shadow
Requires:       python-ordereddict
Recommends:     PyYAML
Recommends:     curl
Recommends:     iproute-tc
Recommends:     lm_sensors
Recommends:     nmap-ncat
Recommends:     python
Recommends:     python2-PyMySQL
Recommends:     python2-psycopg2
Suggests:       logrotate
Suggests:       nodejs
%if 0%{?sle_version} >= 130000
BuildRequires:  libnetfilter_acct-devel
%endif
BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
netdata is a system for distributed real-time performance and health monitoring.
It provides insights, in real-time, of everything happening on the system it
runs on (including applications such as web and database servers),
using interactive web dashboards.

%prep
%setup -q
#%patch0
%patch1 -p1
%patch2 -p1
dos2unix web/lib/tableExport-1.6.0.min.js
sed -i 's,^#!%{_bindir}/env bash,#!/bin/bash,' plugins.d/* python.d/*.sh

%build
autoreconf -fi
%configure \
  --docdir="%{_docdir}/%{name}-%{version}" \
%if 0%{?sle_version} >= 130000
  --enable-plugin-nfacct \
%endif
  --with-zlib \
  --with-math \
  --with-user=%{netdata_user} \
  %{?conf}
make %{?_smp_mflags}

%install
#rm -rf "${RPM_BUILD_ROOT}"
%make_install
#%{__make} %{?_smp_mflags} DESTDIR="${RPM_BUILD_ROOT}" install
find %{buildroot} -name .keep -delete
install -D -m 0644 system/%{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -D -m 0644 system/%{name}.conf %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf

%if %{with systemd}
install -D -m 0644 system/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
ln -s -f %{_sbindir}/service %{buildroot}%{_sbindir}/rc%{name}
%else
install -D -m 0755 %{SOURCE1} %{buildroot}%{_sysconfdir}/init.d/%{name}
ln -s -f %{_sysconfdir}/init.d/%{name} %{buildroot}%{_sbindir}/rc%{name}
%endif

# sles 11 is too old for bash4 
%if 0%{?suse_version} <= 1220
install -D -m 0755 %{SOURCE2} %{buildroot}%{_libdir}/netdata/plugins.d/alarm-notify.bash3.sh
%endif

%fdupes -s %{buildroot}

%pre
getent group %{netdata_group} >/dev/null || \
  %{_sbindir}/groupadd -r %{netdata_group}
getent passwd %{netdata_user} >/dev/null || \
  %{_sbindir}/useradd -r -g %{netdata_group} -s /bin/false \
  -c "netdata daemon user" -d %{_localstatedir}/lib/empty %{netdata_user}
%{_sbindir}/usermod -g %{netdata_group} %{netdata_user} >/dev/null
%if %{with systemd}
%service_add_pre %{name}.service
%endif

%post
%if %{with systemd}
%service_add_post %{name}.service
%else
%fillup_and_insserv %{name}
%endif

%preun
%if %{with systemd}
%service_del_preun %{name}.service
%else
%stop_on_removal %{name}
%endif

%postun
%if %{with systemd}
%service_del_postun %{name}.service
%else
%restart_on_update %{name}
%insserv_cleanup
%endif

%files
%doc ChangeLog README.md
%if 0%{?sle_version} <= 130000
%doc LICENSE.md COPYING
%else
%license LICENSE.md COPYING
%endif

%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/%{name}/charts.d
%dir %{_sysconfdir}/%{name}/node.d
%config(noreplace) %{_sysconfdir}/%{name}/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/charts.d/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/health.d/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/python.d/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/statsd.d/*.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}

%{_sysconfdir}/%{name}/node.d/*.md

%{_libexecdir}/%{name}

%{_sbindir}/%{name}
%{_sbindir}/rc%{name}

%attr(0750,%{netdata_user},root) %dir %{_localstatedir}/cache/%{name}
%attr(0750,%{netdata_user},root) %dir %{_localstatedir}/log/%{name}
%attr(0750,%{netdata_user},root) %dir %{_localstatedir}/lib/%{name}

%attr(-,root,%{netdata_group}) %dir %{_datadir}/%{name}
%dir %{_sysconfdir}/%{name}/health.d
%dir %{_sysconfdir}/%{name}/python.d
%dir %{_sysconfdir}/%{name}/statsd.d

%if %{with systemd}
%{_unitdir}/%{name}.service
%else
%{_sysconfdir}/init.d/%{name}
%endif

%defattr(0644,root,%{netdata_group},0755)
%{_datadir}/%{name}/web

%changelog
* Thu May 10 2018 alex
  - patch python plugin runner for sles
  - require python-ordereddict for python 2.6 -> 2.7 compatibility
* Thu May  3 2018 alex
  - add alarm-notify.bash3.sh for sles 11
