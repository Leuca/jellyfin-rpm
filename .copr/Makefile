pkgs:
	dnf -y install fedpkg rpmdevtools wget curl dotnet-sdk-8.0 npm

sources: pkgs
	wget $$(spectool -S jellyfin.spec 2>/dev/null | grep Source0 | cut -d" " -f 2)
	wget $$(spectool -S jellyfin.spec 2>/dev/null | grep Source1 | cut -d" " -f 2 | head -1)
	./jellyfin-offline.sh

srpm: sources
	fedpkg --release f40 srpm
	cp *.src.rpm $(outdir)
