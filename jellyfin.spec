# NuGet packages are stripped packages and no debug info for .NET binaries at this time
%global         debug_package %{nil}

# Set .NET runtime identitfier string on non-Fedora platforms
%if !0%{?fedora}
%if 0%{?rhel}
%if "%{dist_name}" == "Red Hat Enterprise Linux"
%define dotnet_os rhel
%else
%define dotnet_os centos
%endif
%define dotnet_os_ver .%{rhel}
%else
%define dotnet_os linux
%endif
%ifarch aarch64
%define dotnet_arch arm64
%else
%define dotnet_arch x64
%endif
%define dotnet_runtime_id %{dotnet_os}%{dotnet_os_ver}-%{dotnet_arch}
%endif

Name:           jellyfin
Version:        10.10.1
Release:        %autorelease
Summary:        The Free Software Media System
License:        GPL-2.0-only
URL:            https://jellyfin.org
Source0:        https://github.com/jellyfin/jellyfin/archive/v%{version}/%{name}-%{version}.tar.gz
Source1:        https://github.com/jellyfin/jellyfin-web/archive/v%{version}/%{name}-web-%{version}.tar.gz
Source2:        %{name}-nupkgs.tar.xz
Source3:        %{name}-nupkgs-system.tar.xz
Source4:        %{name}-npm.tar.xz
Source5:        %{name}-web-package-lock.json
# Jellyfin uses dotnet and npm that both need the Internet to download dependencies.
# Koji / Mock disable Internet access by default so download the required dependencies beforehand.
# The following script requires the 'dotnet-sdk-8.0' and 'npm' packages be installed to run.
Source10:       %{name}-offline.sh
Source11:       %{name}.service
Source12:       %{name}.env
Source13:       %{name}.sudoers
Source14:       %{name}.override.conf
Source15:       %{name}-firewalld.xml
Source16:       %{name}-server-lowports.conf
Source17:       %{name}.sysusers

# dotnet does not offer a runtime on ppc
ExcludeArch:    %{power64} ppc64le %{arm}

%{?systemd_requires}
%{?sysusers_requires_compat}
BuildRequires:  firewalld-filesystem
BuildRequires:  fontconfig
BuildRequires:  systemd-rpm-macros
BuildRequires:  dotnet-sdk-8.0

# jellyfin-web
BuildRequires:  npm >= 8

Requires: %{name}-server = %{version}-%{release}
Requires: %{name}-web = %{version}-%{release}
# /etc/sudoers.d/
Requires: sudo
Requires: (%{name}-firewalld = %{version}-%{release} if firewalld)


%description
Jellyfin is a free software media system that puts you in control of managing 
and streaming your media.


%package firewalld
Summary: FirewallD metadata files for Jellyfin
Requires: firewalld-filesystem
Requires(post): firewalld-filesystem
BuildArch:      noarch


%description firewalld
This package contains FirewallD files for Jellyfin.


%package server
# RPMfusion free
Summary:        The Free Software Media System Server backend
Requires:       at
Requires:       ffmpeg
Requires:       aspnetcore-runtime-8.0
Requires:       dotnet-runtime-8.0


%description server
The Jellyfin media server backend.


%package server-lowports
# RPMfusion free
Summary:        The Free Software Media System Server backend.  Low-port binding.
Requires:       jellyfin-server = %{version}-%{release}
BuildArch:      noarch


%description server-lowports
The Jellyfin media server backend low port binding package.  This package
enables binding to ports < 1024.  You would install this if you want
the Jellyfin server to bind to ports 80 and/or 443 for example.


%package web
# RPMfusion free
Summary:        The Free Software Media System Server frontend
Requires:       jellyfin-server = %{version}-%{release}
BuildArch:      noarch


%description web
The Jellyfin media server web frontend.


%prep
%autosetup -p1 -b 1
pushd ..
tar xf %{SOURCE2}
tar xf %{SOURCE3}
tar xf %{SOURCE4}
cp -p %{SOURCE5} %{name}-web-%{version}/package-lock.json
popd

dotnet nuget add source %{_builddir}/jellyfin-nupkgs -n jellyfin-nupkgs
dotnet nuget add source %{_builddir}/jellyfin-nupkgs-system -n jellyfin-nupkgs-system
dotnet nuget disable source nuget


%build
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
# https://bugzilla.rpmfusion.org/show_bug.cgi?id=6944
export DOTNET_NUGET_SIGNATURE_VERIFICATION=false
mkdir build-server
dotnet publish --configuration Release \
               --output="build-server" \
               --self-contained false \
               --runtime %{dotnet_runtime_id} \
               "-p:DebugSymbols=false;DebugType=none" \
               Jellyfin.Server
cd ../%{name}-web-%{version}
npm config set offline=true
npm config set cache ../jellyfin-npm
npm ci
npm run build:production


%install
# Jellyfin files
mkdir -p %{buildroot}%{_libdir}
cp -rp build-server %{buildroot}%{_libdir}/jellyfin
chmod 644 %{buildroot}%{_libdir}/jellyfin/*.dll
chmod 644 %{buildroot}%{_libdir}/jellyfin/*.so
mkdir -p %{buildroot}%{_bindir}
tee %{buildroot}%{_bindir}/jellyfin << EOF
#!/bin/sh
exec %{_libdir}/jellyfin/jellyfin \${@}
EOF
chmod +x %{buildroot}%{_bindir}/jellyfin

# Jellyfin config
install -p -m 644 -D Jellyfin.Server/Resources/Configuration/logging.json %{buildroot}%{_sysconfdir}/jellyfin/logging.json
install -p -m 644 -D %{SOURCE12} %{buildroot}%{_sysconfdir}/sysconfig/jellyfin

# system config
install -p -m 644 -D %{SOURCE15} %{buildroot}%{_prefix}/lib/firewalld/services/jellyfin.xml
install -p -m 640 -D %{SOURCE13} %{buildroot}%{_sysconfdir}/sudoers.d/jellyfin-sudoers
install -p -m 644 -D %{SOURCE14} %{buildroot}%{_sysconfdir}/systemd/system/jellyfin.service.d/override.conf
install -p -m 644 -D %{SOURCE11} %{buildroot}%{_unitdir}/jellyfin.service
install -p -m 644 -D %{SOURCE17} %{buildroot}%{_sysusersdir}/jellyfin.conf

# empty directories
mkdir -p %{buildroot}%{_sharedstatedir}/jellyfin
mkdir -p %{buildroot}%{_sysconfdir}/jellyfin
mkdir -p %{buildroot}%{_localstatedir}/cache/jellyfin
mkdir -p %{buildroot}%{_localstatedir}/log/jellyfin

# jellyfin-server-lowports subpackage
install -p -m 644 -D %{SOURCE16} %{buildroot}%{_unitdir}/jellyfin.service.d/jellyfin-server-lowports.conf

cd ../%{name}-web-%{version}
# move web licenses prior to installation
mv dist/*.js.LICENSE.txt ../jellyfin-%{version}/
mv dist/libraries/*.js.LICENSE.txt ../jellyfin-%{version}/
mkdir -p %{buildroot}%{_datadir}/
mv dist %{buildroot}%{_datadir}/jellyfin-web/
# allow easier usage outside service file
ln -s %{_datadir}/jellyfin-web %{buildroot}%{_libdir}/jellyfin/jellyfin-web


%check
for TEST in Api Common Controller Extensions LiveTv MediaEncoding.Hls MediaEncoding.Keyframes MediaEncoding Model Naming Providers Server.Implementations Server.Integration Server XbmcMetadata
do
  dotnet test tests/Jellyfin.$TEST.Tests/Jellyfin.$TEST.Tests.csproj \
            --configuration Release \
            --collect:"XPlat Code Coverage" \
            --settings tests/coverletArgs.runsettings 
done


%files
# empty as this is just a meta-package


%files firewalld
%license LICENSE
%{_prefix}/lib/firewalld/services/jellyfin.xml


%files server
%license LICENSE
# Jellyfin files
%{_bindir}/jellyfin
# Needs 755 else only root can run it since binary build by dotnet is 722
%{_libdir}/jellyfin/

# Jellyfin config
%config(noreplace) %attr(644,jellyfin,jellyfin) %{_sysconfdir}/jellyfin/logging.json
# user should override systemd service instead so the following will NOT be (noreplace)
%config %{_sysconfdir}/sysconfig/jellyfin

# system config
%{_unitdir}/jellyfin.service
%config(noreplace) %{_sysconfdir}/sudoers.d/jellyfin-sudoers
%dir %{_sysconfdir}/systemd/system/jellyfin.service.d/
%config(noreplace) %{_sysconfdir}/systemd/system/jellyfin.service.d/override.conf
%{_sysusersdir}/jellyfin.conf

# empty directories
%attr(750,jellyfin,jellyfin) %dir %{_sharedstatedir}/jellyfin
%attr(755,jellyfin,jellyfin) %dir %{_sysconfdir}/jellyfin
%attr(750,jellyfin,jellyfin) %dir %{_localstatedir}/cache/jellyfin
%attr(-,  jellyfin,jellyfin) %dir %{_localstatedir}/log/jellyfin


%files server-lowports
%dir %{_unitdir}/jellyfin.service.d/
%{_unitdir}/jellyfin.service.d/jellyfin-server-lowports.conf


%files web
%license *.js.LICENSE.txt
%{_datadir}/jellyfin-web


%post firewalld
%firewalld_reload


%pretrans server
# handle upgrade path from upstream
if [ -d %{_libdir}/jellyfin/jellyfin-web ] && [ ! -L %{_libdir}/jellyfin/jellyfin-web ]
then
  mv %{_libdir}/jellyfin/jellyfin-web/ %{_libdir}/jellyfin/jellyfin-web.tmp/
fi


%pre server
%sysusers_create_compat %{SOURCE17}


%post server
%systemd_post jellyfin.service
# handle upgrade path from upstream
if [ -d %{_libdir}/jellyfin/jellyfin-web.tmp ] && [ ! -L %{_libdir}/jellyfin/jellyfin-web.tmp ]
then
  mv %{_libdir}/jellyfin/jellyfin-web %{_libdir}/jellyfin/jellyfin-web.tmplink
  mv %{_libdir}/jellyfin/jellyfin-web.tmp/ %{_libdir}/jellyfin/jellyfin-web/
fi


%posttrans server
# handle upgrade path from upstream
if [ -d %{_libdir}/jellyfin/jellyfin-web ] && [ ! -L %{_libdir}/jellyfin/jellyfin-web ]
then
  rm -rf %{_libdir}/jellyfin/jellyfin-web/
  mv %{_libdir}/jellyfin/jellyfin-web.tmplink %{_libdir}/jellyfin/jellyfin-web
fi


%preun server
%systemd_preun jellyfin.service


%postun server
%systemd_postun_with_restart jellyfin.service


%post server-lowports
%systemd_post jellyfin.service


%preun server-lowports
%systemd_preun jellyfin.service


%postun server-lowports
%systemd_postun_with_restart jellyfin.service


%changelog
%autochangelog
