### Why?

Appium每次session start时，都会安装unlock and appium-setting apk, 考虑到一段时间运行用唯一session会有丢失的情况，所以当前的框架是每个用例前都会重新建立一个session, 
这时我们希望每次不安装unlock and appium-setting, 这时需要修改Appium 一些JS脚本，具体修改如下：


### Version 1.6.4

通过npm install -g appium, 会安装最新APPIUM version 1.6.4

+ Appium Setting安装包路径：
 ../node_modules/appium/node_modules/appium-android-driver/node_modules/io.appium.settings/bin/settings_apk-debug.apk
 
+ Unlock安装包路径
../node_modules/appium/node_modules/appium-android-driver/node_modules/appium-unlock/bin/unlock_apk-debug.apk

#### 需要修改下面的两个文件：
+ ../ node_modules/appium/node_modules/appium-android-driver/lib/android-helpers.js

注掉下图中的四行代码
![image](https://github.com/xuxhTest/AutoTestDemo/blob/master/TestTasks/raw/master/screetshots/js1.PNG)
 
+ ../node_modules/appium/node_modules/appium-android-driver/build/lib/android-helpers.js
启动device时会按照下面的case去一条条执行，执行通过了才会执行下一个case。将原return使用//注释掉
然后添加新的return（与case17的一致，相当于跳过该步骤）：return context$1$0.abrupt('return', defaultIME);

![image](https://github.com/xuxhTest/AutoTestDemo/blob/master/TestTasks/raw/master/screetshots/js2.PNG)

### Version 1.4.6
如果是通过EXE安装包安装的appium需要注释这两行
../ node_modules/appium/lib/devices/android/android.js

//this.pushSettingsApp.bind(this), 
//this.pushUnlock.bind(this),