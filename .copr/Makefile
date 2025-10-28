pkgs:
	dnf -y install git rpmautospec rpmdevtools wget curl dotnet-sdk-9.0 npm

sources: pkgs
	wget $$(spectool -S jellyfin.spec 2>/dev/null | grep Source0 | cut -d" " -f 2)
	wget $$(spectool -S jellyfin.spec 2>/dev/null | grep Source1 | cut -d" " -f 2 | head -1)
	./jellyfin-offline.sh

srpm: sources
	git config --global --add safe.directory .
	rpmautospec process-distgit jellyfin.spec jellyfin.spec.new
	mv jellyfin.spec jellyfin.spec.old
	mv jellyfin.spec.new jellyfin.spec
	rpmbuild -bs jellyfin.spec --define "_topdir ." --define "_sourcedir ." --define "_srcrpmdir ."
	cp *.src.rpm $(outdir)
