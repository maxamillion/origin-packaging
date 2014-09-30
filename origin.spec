#debuginfo not supported with Go
%global debug_package %{nil}
%global gopath      %{_datadir}/gocode
%global import_path github.com/openshift/origin
%global commit      6d9f1a93aedc3c5dc89cdd2de726a6302b66def0
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           origin
Version:        0
Release:        0.0.4.git%{shortcommit}%{?dist}
Summary:        Open Source Platform as a Service by Red Hat
License:        ASL 2.0
URL:            https://%{import_path}
ExclusiveArch:  x86_64
Source0:        https://%{import_path}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz

# FIXME - Need to add a -devel subpackage to etcd that provides the golang
#         libraries/packages, but this will work for now.
Source1:        etcd-0.4.6.tar.gz
Source10:       origin
Source20:       origin.service

BuildRequires:  gcc
BuildRequires:  git
BuildRequires:  systemd
BuildRequires:  golang >= 1.2-7

# FIXME - All of these are debundled deps that exist upstream in the 
#         Fedora based Atomic-Next COPR but are blocked on EPEL7 because the
#         version of docker is too old.
#           http://copr.fedoraproject.org/coprs/walters/atomic-next/
#         These will be uncommented and will be real build time deps once we 
#         can bring some sanity to this madness.
#BuildRequires:  golang(bitbucket.org/kardianos/osext)
#BuildRequires:  golang(github.com/coreos/go-log/log)
#BuildRequires:  golang(github.com/coreos/go-systemd)
#BuildRequires:  golang(github.com/coreos/go-etcd/etcd)
#BuildRequires:  golang(code.google.com/p/go.net)
#BuildRequires:  golang(code.google.com/p/goauth2)
#BuildRequires:  golang(code.google.com/p/go-uuid)
#BuildRequires:  golang(code.google.com/p/google-api-go-client)
#BuildRequires:  golang(github.com/fsouza/go-dockerclient)
#BuildRequires:  golang(github.com/golang/glog)
#BuildRequires:  golang(gopkg.in/v1/yaml)
#BuildRequires:  golang(github.com/google/cadvisor)

Requires:       /usr/bin/docker

%description
%{summary}

%prep
%autosetup -Sgit -n %{name}-%{commit}

# FIXME - There's a LOT of bundled libs in here we need to get out, a lot of
#         this work has been done for kubernetes packaging:
#               https://github.com/projectatomic/kubernetes-package
#         but that doesn't expose the kubernetes api presently which causes the
#         build to fail. For now we'll leave them in place and deal with it
#         when the other work is done.
#rm -r Godeps

# FIXME (if we can)
# Unable to remove go-dockerclient-copiedstructs because this repository either
# no longer exists or is a private repository.
#

%build
#env GOPATH="${PWD}:%{gopath}" ./hack/build-go.sh

# Don't judge me for this ... it's so bad.
mkdir _build

# FIXME - Horrid hack just to get things working, can remove this once we have
#         time to get the etcd-devel subpackage done.
mkdir -p _build/src/github.com/coreos/etcd
tar -zxvf %{SOURCE1}
mv etcd-0.4.6/* _build/src/github.com/coreos/etcd/

pushd _build
    mkdir -p src/github.com/openshift
    ln -s $(dirs +1 -l) src/%{import_path}
popd


# FIXME - Gaming the GOPATH to include the third party bundled libs at build
#         time. This is bad and I feel bad, but we need a package to start
#         testing things.
mkdir _thirdpartyhacks
pushd _thirdpartyhacks
    ln -s \
        $(dirs +1 -l)/Godeps/_workspace/src/ \
            src
popd
mkdir _thirdthirdpartyhacks
pushd _thirdthirdpartyhacks
    ln -s \
        $(dirs +1 -l)/Godeps/_workspace/src/github.com/GoogleCloudPlatform/kubernetes/third_party/ \
            src
popd
export GOPATH=$(pwd)/_build:$(pwd)/_thirdpartyhacks:$(pwd)/_thirdthirdpartyhacks:%{buildroot}%{gopath}:%{gopath}

# Default to building all of the components
for cmd in openshift
do 
    #go build %{import_path}/cmd/${cmd}
    go build -ldflags \
        "-X github.com/GoogleCloudPlatform/kubernetes/pkg/version.gitCommit 
            %{shortcommit} 
        -X github.com/openshift/origin/pkg/version.commitFromGit 
            %{shortcommit}" %{import_path}/cmd/${cmd}
done

%install

install -d %{buildroot}%{_bindir}
for bin in openshift
do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 ${bin} %{buildroot}%{_bindir}/${bin}
done

install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 -t %{buildroot}%{_unitdir} %{SOURCE20}

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
install -m 0644 -t %{buildroot}%{_sysconfdir}/sysconfig %{SOURCE10}

mkdir -p %{buildroot}/var/log/%{name}

%files
%defattr(-,root,root,-)
%doc README.md LICENSE
%dir /var/log/%{name}
%{_bindir}/openshift
%{_unitdir}/*.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}

%post
%systemd_post %{basename:%{SOURCE20}}

%preun
%systemd_preun %{basename:%{SOURCE20}}

%postun
%systemd_postun

%changelog
* Tue Sep 30 2014 Adam Miller <admiller@redhat.com> - 0-0.0.4.git6d9f1a9
- Add systemd and sysconfig entries from jhonce

* Tue Sep 23 2014 Adam Miller <admiller@redhat.com> - 0-0.0.3.git6d9f1a9
- Update to latest upstream.

* Mon Sep 15 2014 Adam Miller <admiller@redhat.com> - 0-0.0.2.git2647df5
- Update to latest upstream.

* Thu Aug 14 2014 Adam Miller <admiller@redhat.com> - 0-0.0.1.gitc3839b8
- First package
