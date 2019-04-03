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

1\. Add [Whonix's Signing Key](https://www.whonix.org/wiki/Whonix_Signing_Key).

```
sudo apt-key --keyring /etc/apt/trusted.gpg.d/whonix.gpg adv --keyserver hkp://ipv4.pool.sks-keyservers.net:80 --recv-keys 916B8D99C38EAF5E8ADC7A2A8D66066A2EEACCDA
```

3\. Add Whonix's APT repository.

```
echo "deb http://deb.whonix.org buster main" | sudo tee /etc/apt/sources.list.d/whonix.list
```

4\. Update your package lists.

```
sudo apt-get update
```

5\. Install `sdwdate`.

```
sudo apt-get install sdwdate
```

## How to Build deb Package ##

Replace `apparmor-profile-torbrowser` with the actual name of this package with `sdwdate` and see [instructions](https://www.whonix.org/wiki/Dev/Build_Documentation/apparmor-profile-torbrowser).

## Contact ##

* [Free Forum Support](https://forums.whonix.org)
* [Professional Support](https://www.whonix.org/wiki/Professional_Support)

## Payments ##

`sdwdate` requires [payments](https://www.whonix.org/wiki/Payments) to stay alive!
