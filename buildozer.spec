[app]

title = 合约滚仓计算器
package.name = trade_calculator
package.domain = org.tradeapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0

requirements = python3,kivy==2.2.0,plyer

orientation = portrait

osx.python_version = 3
osx.kivy_version = 2.3.0

fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE
android.archs = arm64-v8a,armeabi-v7a
android.minapi = 21

android.allow_backup = True

p4a.bootstrap = sdl2
