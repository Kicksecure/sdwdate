# Readme Version #

Genric Readme Version 0.1

# Cooperating Anonymity Distributions #

This is only a generic readme, until a real gets written. If you want to know more about the functionality of this particular package see the `Description:` field in `debian/control` or have a look into the `man` sub folder (if available).

The functionality of this package was once exclusively available in the [Whonix](https://www.whonix.org) ([github](https://github.com/Whonix/Whonix)) anonymity distribution.

Since multiple projects and individuals stated interest in various of Whonix's functionality (examples: [Qubes OS](http://qubes-os.org/trac) ([discussion](https://groups.google.com/forum/#!topic/qubes-devel/jxr89--oGs0)); [piratelinux](https://github.com/piratelinux) ([discussion](https://github.com/adrelanos/VPN-Firewall/commit/6147f0e606377f5a801e98daf22e24ba2c750a21#commitcomment-6360713))) and because it's better to share certain characteristics [(such as /etc/hostname etc.) among all anonymity distributions](https://mailman.boum.org/pipermail/tails-dev/2013-January/002457.html)), as much source code as possible, Whonix [is split](https://github.com/Whonix/Whonix/issues/40) into [multiple standalone packages](https://github.com/Whonix) ([list](https://github.com/Whonix/Whonix/issues/40#issuecomment-44753572)).

# Work in Progress #

While the functionality of the original source code of this package has been tested and found to be stable in Whonix, it still is a work in progress. Split of Whonix is not done yet. Packaging is unfinished. Functionality has not been tested outside of Whonix yet. This is a fully untested early pre-release allowing further [discussion](https://github.com/Whonix/Whonix/issues/40) on how various anonymity distributions can be best standardized and share as much source code as possible.

# Generic Packaging #
Files in `etc/...` in root source folder will be installed to `/etc/...`, files in `usr/...` will be installed to `/usr/...` and so forth. This should make renaming, moving files around, packaging, etc. very simple. Packaging of most packages looks very similar.

# How to use outside of Debian or derivatives #

Although probably due to generic packaging not very hard. Still, this requires developer skills. [Ports](https://en.wikipedia.org/wiki/Porting) welcome!

# How to Build deb Package #

See comments below and [instructions](https://www.whonix.org/wiki/Dev/Build_Documentation/apparmor-profile-torbrowser).

* Replace `apparmor-profile-torbrowser` with the actual name of this package (equals the root source folder name of this package after you git cloned it).
* You only need [config-package-dev](https://packages.debian.org/wheezy/config-package-dev), when it is listed in the `Build-Depends:` field in `debian/control`.
* Many packages do not have signed git tags yet. You may request them if desired.
* We might later use a [documentation template](https://www.whonix.org/wiki/Template:Build_Documentation_Build_Package).

# How to install in Debian using apt-get #

Binary packages will later be available in Whonix's APT repository. By no means you're required to use the binary version of this package. This might be interesting for users of Debian and derivatives.

# Cooperation #

Most welcome. [Ports](https://en.wikipedia.org/wiki/Porting), distribution maintainers, developers, patches, forks, testers, comments, etc. all welcome.

# Contact

* Professional Support: https://www.whonix.org/wiki/Support#Professional_Support
* Free Forum Support: https://www.whonix.org/forum
* Github Issues
* twitter: https://twitter.com/Whonix

# Donate

* [Donate](https://www.whonix.org/wiki/Donate)
