[app]

title = My Application
package.name = myapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy==2.2.1,git+https://github.com/kivymd/KivyMD.git@master
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.release_artifact = aab
android.debug_artifact = apk

[buildozer]

log_level = 2
warn_on_root = 1
