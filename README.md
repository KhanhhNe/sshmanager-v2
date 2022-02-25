# SSHManager

An open source tool for managing, checking and connecting to your SSH proxy

<div style="text-align: center;">
  <!--suppress CheckImageSize -->
  <img src="logo/logo.png" alt="sshmanager logo" width="200"/>
</div>

Features
----

- **Multi-threaded SSH checking** using BitviseSSH with queued SSH check,
  ensuring fastest checking speed with lowest system impact
- **Multi-port SSH port forwarding** with simple and intuitive management
  interface and real-time update on external IP of each port
- **Multi-device support** (coming soon)
- **Simple API** with HTTP API support for controlling all aspects of the tool,
  with OpenAPI documentation at http://your-app.url/docs

Usage
----
Download the latest release, run sshmanager-v2.exe and that's it! A browser tab
will open with the app's URL, and it is accessible over LAN network from other
devices too.

Building your own sshmanager
----
Requirements: `Windows 8.1+`, `Python 3.9.5`, `NodeJS v14.16.1` (not tested
under other systems)

Steps:

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

Remember to remove dist/ and app_dist/ folder prior to running build commands to
avoid permission bugs

```bash
npm run build
pipenv run compile.py
```

A new file named `sshmanager-v2.zip` will be generated and is ready to use!
