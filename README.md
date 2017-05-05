### 目标
+ 支持ANDROID手机上的基本的UI操作
+ 支持ANDROIO手机上的基本性能数据的收集
+ 测试日志及截图收集
+ 测试用例及测试参数可灵活配置
+ 支持多台手机的并行运行
### 测试环境相关
+ UI框架使用了APPIUM以支持UI操作，因此需要在PC机上配置相关的环境，包括NODE,JDK,ANDROID-SDK等等
+ PYTHON 2.7+, 不要装3.0以上版本，以及相关的module
+ 被测手机需要ROOT（脚本中尽量使用SHELL命令代替手机的点击动作，为了保证SHELL命令成功执行，所以要ROOT)
### 脚本结构

![image](https://github.com/xuxhTest/TestTasks/blob/master/raw/master/screetshots/structure.PNG)

+ testcases/test_schedule.py: 测试用例是继承了unittest.TestCase,与操作流程相关的公共方法也会放在对应的文件中
+ public/*: 根据功能不同的不同，把一些通用的方法封装成类以支持测试用例的执行
+ log: 保存测试日志，目录的结构是DATE--DEVICENAME+DATE.log, 稍后目录结构更新为DATE--DEVICENAME--TIMESTAMP--文本日志及截图文件夹
+ apps: 目前读取APK文件都是从该文件夹的读取，稍后应该根据实际情况配置网络路径或者直接从GIT上获取
+ run.py: 是程序运行的主文件，会根据参数配置验证测试环境是否READY,以及运行哪些测试用例。 当同时运行多台手机时，通过运行多个带不同参数的RUN程序实现
