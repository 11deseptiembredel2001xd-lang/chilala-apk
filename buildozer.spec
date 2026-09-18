[app]
# App metadata
title = Chilala VS Jeyson
package.name = chilala
package.domain = org.chilala
source.dir = .
source.include_exts = py,wav,json
source.exclude_exts = pyc,pyo,pyd
version = 1.0.0
requirements = python3,pygame-ce
p4a.local_recipes = %(source.dir)s/p4a-recipes
orientation = landscape
fullscreen = 1

# Android build
android.api = 36
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.debug_artifact = apk
android.release_artifact = aab
android.copy_libs = 1

# Packaging behavior
presplash_color = #0c1123

[buildozer]
log_level = 2
warn_on_root = 1
