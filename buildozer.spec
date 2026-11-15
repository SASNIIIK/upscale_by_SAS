[app]
title = Fast Image Upscaler
package.name = upscaler
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3, kivy, kivymd==1.1.1, pillow, numpy, opencv
orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES
android.api = 33
android.minapi = 24
android.accept_sdk_license = True
android.enable_androidx = True
android.archs = arm64-v8a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
