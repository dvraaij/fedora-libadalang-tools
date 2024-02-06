# The test suite is normally run. It can be disabled with "--without=check".
%bcond_without check

# Upstream source information.
%global upstream_owner    AdaCore
%global upstream_name     libadalang-tools
%global upstream_version  24.0.0
%global upstream_gittag   v%{upstream_version}

Name:           libadalang-tools
Version:        %{upstream_version}
Release:        1%{?dist}
Summary:        Tools based on the Ada semantic analysis library

License:        GPL-3.0-or-later

URL:            https://github.com/%{upstream_owner}/%{upstream_name}
Source:         %{url}/archive/%{upstream_gittag}/%{upstream_name}-%{upstream_version}.tar.gz

# [Fedora-specific] Make library name consistent with package name and set the soname.
Patch:          %{name}-rename-lib-and-set-soname.patch

BuildRequires:  gcc-gnat gprbuild make sed
# A fedora-gnat-project-common that contains GPRbuild_flags is needed.
BuildRequires:  fedora-gnat-project-common >= 3.17
BuildRequires:  libadalang-devel
BuildRequires:  libgpr2-devel
BuildRequires:  libvss-devel
BuildRequires:  templates_parser-devel
%if %{with check}
BuildRequires:  aunit-devel
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-e3-testsuite
%endif

# Build only on architectures where GPRbuild is available.
ExclusiveArch:  %{GPRbuild_arches}

# LibVSS fails to build on s390x.
ExcludeArch:    s390x

%description
Tools that are based on libadalang, including a pretty-printer (gnatpp), a
code metric analyzer (gnatmetric), a body stub generator (gnatstub) and a
unit-test skeleton generator and test driver (gnattest).


#############
## Prepare ##
#############

%prep
%autosetup -p1

# Remove the executable bit from some source code files.
find ./src -type f -executable | xargs chmod -x

# Update some release specific information in the source code. The
# substitutions are scoped to specific lines to increase the chance of
# detecting code changes at this point. Sed should exit with exit code 0
# if the substitution succeeds (using `t`, jump to end of script) or exit
# with a non-zero exit code if the substitution fails (using `q1`, quit with
# exit code 1).
sed --in-place \
    --expression="26 { s,dev,%{upstream_version}, ; t; q1 }" \
    --expression="27 { s,unknown,$(date +%Y),     ; t; q1 }" \
    --expression="31 { s,Gnatpro,GPL,             ; t; q1 }" \
    src/utils-versions.ads


###########
## Build ##
###########

%build

# Build the library.
gprbuild %{GPRbuild_flags} \
         -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
         -XVERSION=%{version} \
         -P src/lal_tools.gpr \

# Additional flags to link the executables dynamically with the GNAT runtime
# and make the executables (tools) position independent.
%global GPRbuild_flags_pie -cargs -fPIC -largs -pie -bargs -shared -gargs

# Build the tools.
gprbuild %{GPRbuild_flags} %{GPRbuild_flags_pie} \
         -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
         -XVERSION=%{version} -XLALTOOLS_SET=no-wip \
         -P src/build.gpr


#############
## Install ##
#############

%install

# Install the library.
gprinstall %{GPRinstall_flags} --no-build-var --mode=usage \
           -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
           -XVERSION=%{version} -XLALTOOLS_SET=no-wip \
           -P src/lal_tools.gpr

# Install the tools.
gprinstall %{GPRinstall_flags} --no-build-var --mode=usage \
           -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
           -XVERSION=%{version} -XLALTOOLS_SET=no-wip \
           -P src/build.gpr

# Install the TGen templates.
make install-tgen DESTDIR=%{buildroot}%{_prefix}

# Remove the library symlink, there is no devel package.
rm %{buildroot}%{_libdir}/libadalang_tools.so

# Remove some test executable that lifted along with the build.
rm %{buildroot}%{_bindir}/utils-var_length_ints-test

# Show installed files (to ease debugging based on build server logs).
find %{buildroot} -exec stat --format "%A %n" {} \;
ls -l %{buildroot}%{_libdir}


###########
## Check ##
###########

%if %{with check}
%check

# Make the files installed in the buildroot visible to the testsuite.
export PATH=%{buildroot}%{_bindir}:$PATH
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}:$LD_LIBRARY_PATH

# Build all projects that are part of the testsuite.
for prj in $(find ./testsuite/ada_drivers -name "*.gpr" -type f); do
    gprbuild %{GPRbuild_flags} %{GPRbuild_flags_pie} \
             -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
             -XVERSION=%{version} -XLALTOOLS_SET=no-wip \
             $prj
done

# Run some seperate test not part of the test suite.
bin/utils-var_length_ints-test

# Run the actual testsuite.
%python3 testsuite/testsuite.py \
         --show-error-output \
         --max-consecutive-failures=4 \
         --no-wip

%endif


###########
## Files ##
###########

%files
%license LICENSE
%doc README*
%{_libdir}/libadalang_tools.so.%{version}
%{_bindir}/gnatpp
%{_bindir}/gnatmetric
%{_bindir}/gnatstub
%{_bindir}/gnattest
%{_datadir}/tgen


###############
## Changelog ##
###############

%changelog
* Sun Jan 28 2024 Dennis van Raaij <dvraaij@fedoraproject.org> - 24.0.0-1
- Updated to v24.0.0.

* Sun Oct 30 2022 Dennis van Raaij <dvraaij@fedoraproject.org> - 23.0.0-1
- Updated to v23.0.0.

* Sun Sep 04 2022 Dennis van Raaij <dvraaij@fedoraproject.org> - 22.0.0-1
- New package.
