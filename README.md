# auto_reminder
依赖pandas,openpyxl,requests,基本上任何版本都可以就不做requirements了
需要每天手动在auto_reminder目录下放置plan.xlsx，要求表格文件中存在“报名统计”sheet，且A2到F31符合特定格式，参考样例excel
（主要是没有在线文档的api，也不太会写在线文档这种强鉴权的爬虫emmm），或者直接改main.py中update_plan即可
因为数据和指令的量不大，就没用sqlite处理了，所以还是有些不方便的，但是懒得改了【笑哭】。
异常处理等其他细节基本就没做，希望有大佬指点！
参数：
就填写一个yobot API，就不单独拉一个配置参数文件了，在main.py中填写
使用方法：
标准的module添加方式，项目文件夹添加进module中，__bot__.py添加auto_reminder