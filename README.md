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

1\. Download the APT Signing Key.

```
wget https://www.kicksecure.com/keys/derivative.asc
```

Users can [check the Signing Key](https://www.kicksecure.com/wiki/Signing_Key) for better security.

2\. Add the APT Signing Key.

```
sudo cp ~/derivative.asc /usr/share/keyrings/derivative.asc
```

3\. Add the derivative repository.

```
echo "deb [signed-by=/usr/share/keyrings/derivative.asc] https://deb.kicksecure.com bookworm main contrib non-free" | sudo tee /etc/apt/sources.list.d/derivative.list
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

See instructions.

NOTE: Replace `generic-package` with the actual name of this package `sdwdate`.

* **A)** [easy](https://www.kicksecure.com/wiki/Dev/Build_Documentation/generic-package/easy), _OR_
* **B)** [including verifying software signatures](https://www.kicksecure.com/wiki/Dev/Build_Documentation/generic-package)

## Contact ##

* [Free Forum Support](https://forums.kicksecure.com)
* [Premium Support](https://www.kicksecure.com/wiki/Premium_Support)

## Donate ##

`sdwdate` requires [donations](https://www.kicksecure.com/wiki/Donate) to stay alive!
