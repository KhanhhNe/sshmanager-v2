# SSHManager

An open source tool for managing, checking and connecting to your SSH proxy

<center><img src="logo.png" alt="sshmanager logo" width="200"/></center>

Features
----
- **Multi-threaded SSH checking** using BitviseSSH with queued SSH check, ensuring fastest checking speed with lowest system impact
- **Multi-port SSH port forwarding** with simple and intuitive management interface and real-time update on external IP of each port
- **Multi-device support** (coming soon)
- **Simple API** with HTTP API support for controlling all aspects of the tool, with OpenAPI documentation at http://your-app.url/docs

Usage
----
Download the latest release, run sshmanager-2.0.0.exe and that's it! A browser tab will open with the app's URL, and it is accessible over LAN network from other devices too.

Building your own sshmanager
----
Requirements: `Windows 8.1+`, `Python 3.9.5`

Steps:

1. Clone the repository
```bash
https://github.com/KhanhhNe/sshmanager-2.0.0.git
cd sshmanager-2.0.0
```
2. Install needed libraries
```bash
pip install pipenv
pipenv install
```
3. Run the build script
```bash
# Remove old build dir if it exists
rmdir -recursive -force app_dist
python compile.py
```
A new file named `sshmanager-2.0.0.zip` will be generated and is ready to use!