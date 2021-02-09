# Secure Distributed Network Time Synchronization #

Time keeping is crucial for security, privacy, and anonymity. Sdwdate is a Tor
friendly replacement for rdate and ntpdate that sets the system's clock by
communicating via onion encrypted TCP with Tor onion webservers.

At randomized intervals, sdwdate connects to a variety of webservers and
extracts the time stamps from http headers (RFC 2616).
Using sclockadj option, time is gradually adjusted preventing bigger clock
jumps that could confuse logs, servers, Tor, i2p, etc.

This package contains the sdwdate time fetcher and daemon. No
installation on remote servers required. To avoid conflicts, this daemon
should not be enabled together with ntp or tlsdated.
## How to install `sdwdate` using apt-get ##

1\. Download Whonix's Signing Key.

```
wget https://www.whonix.org/patrick.asc
```

Users can [check Whonix Signing Key](https://www.whonix.org/wiki/Whonix_Signing_Key) for better security.

2\. Add Whonix's signing key.

```
sudo apt-key --keyring /etc/apt/trusted.gpg.d/derivative.gpg add ~/patrick.asc
```

3\. Add Whonix's APT repository.

```
echo "deb https://deb.whonix.org buster main contrib non-free" | sudo tee /etc/apt/sources.list.d/derivative.list
```

4\. Update your package lists.

```
sudo apt-get update
```

5\. Install `sdwdate`.

```
sudo apt-get install sdwdate
```

## How to Build deb Package from Source Code ##

Can be build using standard Debian package build tools such as:

```
dpkg-buildpackage -b
```

See instructions. (Replace `generic-package` with the actual name of this package `sdwdate`.)

* **A)** [easy](https://www.whonix.org/wiki/Dev/Build_Documentation/generic-package/easy), _OR_
* **B)** [including verifying software signatures](https://www.whonix.org/wiki/Dev/Build_Documentation/generic-package)

## Contact ##

* [Free Forum Support](https://forums.whonix.org)
* [Professional Support](https://www.whonix.org/wiki/Professional_Support)

## Donate ##

`sdwdate` requires [donations](https://www.whonix.org/wiki/Donate) to stay alive!
