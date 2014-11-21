%global with_devel_doc 0

Name:           OpenFOAM
Version:        2.3.0
Release:        1%{?dist}
Summary:        The open source CFD toolbox

License:        GPLv3+
URL:            http://www.openfoam.com/
Source0:        http://downloads.sourceforge.net/foam/%{name}-%{version}.tgz

# Ignore failures if directories do not exist (since we do set +x below)
Patch0:         OpenFOAM_docAllwmake.patch
# Use system paraview (note the export PARAVIEW_INC and LD_LIBRARY_PATH in the OpenFOAM-env below)
Patch1:         OpenFOAM_use-system-paraview.patch
# Provide include and library paths for netcdf
# Patch2:         OpenFOAM_netcdf.patch

BuildRequires:  pkgconfig
BuildRequires:  scotch-devel
BuildRequires:  openmpi-devel
BuildRequires:  flex
BuildRequires:  cmake
BuildRequires:  paraview-openmpi-devel
BuildRequires:  paraview-mpich-devel
BuildRequires:  qt-devel
BuildRequires:  qtwebkit-devel
BuildRequires:  python-devel
BuildRequires:  protobuf-devel
BuildRequires:  netcdf-openmpi-devel
BuildRequires:  CGAL-devel
%if %{with_devel_doc}
BuildRequires:  doxygen
BuildRequires:  graphviz
BuildRequires:  tex(latex) tex(epsfig.sty) tex(dvips)
%endif

ExclusiveArch:  %{ix86} x86_64

%filter_provides_in %{_libdir}/%{name}-%{version}/.*\.so$
%filter_from_requires %{_libdir}/%{name}-%{version}/.*\.so$
%filter_setup

%description
OpenFOAM is a free, open source computational fluid dynamcis (CFD) software
package released by the OpenFOAM Foundation. It has a large user base across
most areas of engineering and science, from both commercial and academic
organisations. OpenFOAM has an extensive range of features to solve anything
from complex fluid flows involving chemical reactions, turbulence and heat
transfer, to solid dynamics and electro-magnetics.

Please consult the README.fedora file under /usr/share/docs/%{name}-%{version}.


%package debug
Summary:        %{name} compiled with debug flags
Requires:       %{name}%{_isa} = %{version}-%{release}

%description debug
%{name} compiled with debug flags.


%package prof
Summary:        %{name} compiled with profiling flags
Requires:       %{name}%{_isa} = %{version}-%{release}

%description prof
%{name} compiled with profiling flags.


%if %{with_devel_doc}
%package devel-doc
Summary:        Developer documentation for OpenFOAM.
BuildArch:      noarch
Group:          Documentation
Requires:       %{name} = %{version}-%{release}

%description devel-doc
Developer documentation for OpenFOAM.
%endif


%prep
%setup -q -n %{name}-%{version}
%patch0 -p1
%patch1 -p1

# Fix permissions
chmod 755 bin/*

# Quit immediately when errors occur
find . -name Allwmake -type f -print0 | xargs -0 sed -i 's|^set -x$|set -x -e|'


%build
# Adjust build dir
sed -i "s|foamInstall=\$HOME/\$WM_PROJECT|foamInstall=%{_builddir}|" etc/bashrc

# Adjust arch
%ifarch %{ix86}
sed -i "s|export WM_ARCH_OPTION=64|export WM_ARCH_OPTION=32|" etc/bashrc
%endif

# Use system openmpi
sed -i "s|export WM_MPLIB=OPENMPI|export WM_MPLIB=SYSTEMOPENMPI|" etc/bashrc

# Create rc for variants
for variant in "Prof" "Debug"; do
cp etc/bashrc etc/bashrc-$variant
sed -i "s|export WM_COMPILE_OPTION=Opt|export WM_COMPILE_OPTION=$variant|" etc/bashrc-$variant
done

%_openmpi_load
for variant in "" "-Prof" "-Debug"; do
  source etc/bashrc-$variant
  export PARAVIEW_INC=$MPI_ARCH_PATH/include/paraview
  export PKG_CONFIG_PATH=$MPI_ARCH_PATH/lib/pkgconfig:$PKG_CONFIG_PATH
  export WM_NCOMPPROCS=%(echo %{?_smp_mflags} | sed -E 's|^.*-j([0-9]+).*$|\1|')
  export GFLAGS="%{optflags}"
  ./Allwmake %{?with_devel_doc:doc}
done
%_openmpi_unload


%install
# Copy tree
install -dm 0755 %{buildroot}%{_libdir}/%{name}-%{version}
cp -a bin etc platforms tutorials %{buildroot}%{_libdir}/%{name}-%{version}

# Environment loaders
install -dm 0755 %{buildroot}%{_bindir}

for variant in "" "-Debug" "-Prof"; do
cat > %{buildroot}%{_sysconfdir}/profile.d/%{name}$variant.sh <<EOF
#!/bin/bash
alias %{name}$variant-env=\$(
export FOAM_INST_DIR=%{_libdir}
foamDotFile=\$FOAM_INST_DIR/%{name}-%{version}/etc/bashrc$variant
source \$foamDotFile
module load mpi/openmpi-%{_arch}
export LD_LIBRARY_PATH=\$MPI_ARCH_PATH/lib/paraview:\$LD_LIBRARY_PATH
)
EOF
done

# README.fedora
cat > README.Fedora <<EOF
To use openFOAM, type
	%{name}-env

To permanently load the OpenFOAM environment, add to $HOME/.bashrc
	%{name}-env

If you installed the %{name}-debug or %{name}-prof packages, you can load
the respective environments by using
	%{name}-{Debug|Prof}-env


You should also create the project directory
	\$HOME/OpenFOAM/\$USER-\$WM_PROJECT_VERSION
and a folder "run" within the project directory for the environment variables
\$WM_PROJECT_USER_DIR, \$FOAM_RUN to point to a valid location.
This can be done by typing
	mkdir -p \$FOAM_RUN
EOF


%files
%doc COPYING README.html README.Fedora doc/Guides-a4/UserGuide.pdf
%config(noreplace) %{_sysconfdir}/profile.d/%{name}.sh
%exclude %{_sysconfdir}/profile.d/%{name}-Debug.sh
%exclude %{_sysconfdir}/profile.d/%{name}-Prof.sh
%{_libdir}/%{name}-%{version}/
%exclude %{_libdir}/%{name}-%{version}/etc/bashrc-Debug
%exclude %{_libdir}/%{name}-%{version}/etc/bashrc-Prof
%exclude %{_libdir}/%{name}-%{version}/platforms/*Debug
%exclude %{_libdir}/%{name}-%{version}/platforms/*Prof
# Following are only used for the release process
%exclude %{_libdir}/%{name}-%{version}/bin/foamPack*
%exclude %{_libdir}/%{name}-%{version}/bin/org-*
%exclude %{_libdir}/%{name}-%{version}/bin/tools
# Following are currently unsupported
%exclude %{_libdir}/%{name}-%{version}/bin/engridFoam

%files debug
%config(noreplace) %{_sysconfdir}/profile.d/%{name}-Debug.sh
%{_libdir}/%{name}-%{version}/etc/bashrc-Debug
%{_libdir}/%{name}-%{version}/platforms/*Debug

%files prof
%config(noreplace) %{_sysconfdir}/profile.d/%{name}-Prof.sh
%{_libdir}/%{name}-%{version}/etc/bashrc-Prof
%{_libdir}/%{name}-%{version}/platforms/*Prof

%if %{with_devel_doc}
%files devel-doc
%doc doc/html
%endif


%changelog
* Sun Oct 13 2013 Sandro Mani <manisandro@gmail.com> - 2.2.1-1
- Initial RPM package
