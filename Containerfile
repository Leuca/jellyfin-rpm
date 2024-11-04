FROM fedora

# Install tools
RUN dnf install -y rpm-build rpmdevtools rpmautospec wget git curl dotnet-sdk-8.0 npm

# Setup the RPM build tree
RUN rpmdev-setuptree

# Download sources
WORKDIR /root/rpmbuild/SOURCES
RUN wget $(spectool -S /project/jellyfin.spec 2>/dev/null | grep Source0 | cut -d" " -f 2)
RUN wget $(spectool -S /project/jellyfin.spec 2>/dev/null | grep Source1 | cut -d" " -f 2 | head -1)
RUN /project/jellyfin-offline.sh

# Generate specfile with correct versioning
WORKDIR /project
RUN git config --global --add safe.directory /project
RUN git status
RUN rpmautospec process-distgit jellyfin.spec /root/rpmbuild/SPECS/jellyfin.spec

# Copy sources
RUN cp -rf /project/* /root/rpmbuild/SOURCES
RUN rm /root/rpmbuild/SOURCES/jellyfin.spec

WORKDIR /root/rpmbuild

# Run container until stopped
CMD exec /bin/bash -c "trap : TERM INT; sleep infinity & wait"
