pkgs:
	dnf -y install git rpmautospec rpmdevtools wget curl dotnet-sdk-9.0 npm

sources: pkgs
	spectool --gf jellyfin.spec
	./jellyfin-offline.sh

srpm: sources
	git config --global --add safe.directory .
	rpmautospec process-distgit jellyfin.spec jellyfin.spec.new
	mv jellyfin.spec jellyfin.spec.old
	mv jellyfin.spec.new jellyfin.spec
	rpmbuild -bs jellyfin.spec --define "_topdir ." --define "_sourcedir ." --define "_srcrpmdir ."
	cp *.src.rpm $(outdir)
