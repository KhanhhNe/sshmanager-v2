# SSHManager

An open source tool for SSH managing, checking and setting up port forwarding.

Now you won't have to use `BitviseSSH` or `PuttySSH` to manually connect to an
SSH, set up port forwarding and try until a usable SSH in your list is found;
you can *click, *click, *click and `SSHManager` will do all of that hard work
for you.

<p align="center">
  <!--suppress CheckImageSize -->
  <img src="logo/logo.png" alt="sshmanager logo" width="150"/>
</p>

Features
----

- **Multi-threaded SSH checking**: with the help of `PuttySSH`, `SSHManager`
  ensures the best use of your system resources with optimized asynchronous
  queueing techniques
- **Multi-port SSH port forwarding**: port forwarding using SSH will be easier
  than ever! `SSHManager` provides a simple and intuitive interface to manage
  port forwarding, with live status report of each individual ones
- **Easy API integration**: all application endpoints can be used with simple
  arguments, supplied in `/docs` endpoint of the app with OpenAPI format
- **Open source**: The source code is available for everyone to use and modify
  as needed, and is open to contributions. The executable is, however, paid with
  a small amount of fee to keep the project alive.

Screenshots
----
<p align="center">
  <!--suppress CheckImageSize -->
  <img src="logo/screenshot-1.png" alt="screenshot" width="600"/>
</p>

Usage
----
Buy link (executable
version): <a href="https://taphoammo.net/gian-hang/sshmanager-v2-1">
Link</a> <br>
Download the latest executable release and run `sshmanager-v2.exe`. A browser
tab will open with the app's URL, which is accessible over LAN (local network)
from other devices too.

Build your own SSHManager
----
Requirements: `Windows 11`, `Python 3.9.5`, `NodeJS v14.16.1` (not tested under
other systems)

### Steps:
1. Clone the repository

```bash
https://github.com/KhanhhNe/sshmanager-v2.git
cd sshmanager-v2
```

2. Install needed libraries

```bash
pip install pipenv
pipenv install
npm install
```

3. Run the build script

If possible, run the bellow command as Administrator (highest priviledge) to
avoid directory permission problems.

```bash
pipenv run compile.py
```

A new zip file named `sshmanager-v2.*.*.zip` will be created in the folder and
ready to be used!

Follow me
----
Facebook: https://www.facebook.com/khanh.luong.6 <br>
LinkedIn: https://www.linkedin.com/in/khanh-luong-quang <br>
Linktree: https://linktr.ee/khanhhne