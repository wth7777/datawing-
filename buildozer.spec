[buildozer]
log_level = 2

[app]
title = DataWing
package.name = datawing
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg
version = 1.0
requirements = pygame
orientation = landscape
fullscreen = 1

[android]
permissions = INTERNET
api = 31
minapi = 21
accept_sdk_license = True
android.build_tools_version = 37.0.0

[global]
pip_args = --break-system-packages
python = /usr/bin/python3