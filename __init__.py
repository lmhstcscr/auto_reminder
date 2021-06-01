from .main import *
from hoshino import Service, priv
sv_help = '''
星痕催刀系统帮助
请服务器部署者每日讲今日的排刀表格放置于服务器该脚本目录下
示例：星痕查BOSS,星痕查王,星痕查刀 + 【A1】 查询当前BOSS的出刀情况，任意成员均可
星痕催BOSS,星痕催王,星痕催刀 + 【A1】 直接艾特未出刀成员，需要管理员权限
星痕查询排刀版本,星痕查询排刀信息 无参数，查询当前排刀表版本
星痕排刀更新,星痕更新排刀表 无参数，根据服务器部署者放置在服务器上的当日排刀表更新模块使用的排刀数据，需要管理员权限
星痕查成员 + 【qq号】或者艾特 查询某个成员当前出刀的情况
星痕强制改刀 + 【qq号 C1 C3】  由于程序判定失误或临时出刀变更的调整方法，只有管理员才可进行，生效时间当天，输错请管理员在服务器删除change.txt对应条目，目前没有命令可以删除
'''.strip()
sv = Service(
    name = '星痕催刀',  #功能名
    use_priv = priv.NORMAL, #使用权限
    manage_priv = priv.ADMIN, #管理权限
    visible = True, #False隐藏
    enable_on_default = True, #是否默认启用
    bundle = '会战', #属于哪一类
    help_ = sv_help #帮助文本
    )

@sv.on_fullmatch(("帮助星痕催刀","星痕催刀帮助"))
async def bangzhu(bot, ev):
    await bot.send(ev, sv_help, at_sender=True)

@sv.on_prefix(('星痕查BOSS','星痕查王','星痕查刀'))
async def check_outer(bot,event):
    try:
        input_para=event.message.extract_plain_text()
        msg=check_boss(input_para)
        await bot.send(event,msg, at_sender=True)
    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')

@sv.on_prefix(('星痕催BOSS','星痕催王','星痕催刀'))
async def remind_outer(bot,event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，只有管理员才可以催刀，查询请使用查王/查刀命令')
            return
        input_para=event.message.extract_plain_text()
        name_list,id_list=remind_boss(input_para)
        msg = "尚未出{}的有: \n".format(input_para)
        msg = msg+ ','.join(name_list)
        msg = msg+"\n"
        for ii in id_list:
            msg = msg+f"[CQ:at,qq={ii}]"
        await bot.send(event,msg, at_sender=True)
    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')

@sv.on_prefix(('星痕查成员'))
async def check_member(bot,event):
    try:
        if event.message[0].type == 'at': #如果以艾特形式出现
            input_para = int(event.message[0].data['qq'])
        else:#如果直接输入QQ
            input_para=event.message.extract_plain_text()
        
        msg=describe_member(input_para)
        await bot.send(event,msg, at_sender=True)
    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')

@sv.on_fullmatch(('星痕查询排刀版本','星痕查询排刀信息'))
async def check_plan_time(bot,event):
    try:
        msg=check_plan_date()
        await bot.send(event,msg, at_sender=True)
    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')

@sv.on_fullmatch(('星痕排刀更新','星痕更新排刀表'))
async def update_plan_outer(bot,event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，您无权使用此指令，请联系管理员')
            return
        update_plan()
        await bot.send(event,'排刀表更新完毕！')
    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')

@sv.on_prefix(('星痕强制改刀'))
async def remind_outer(bot,event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，只有管理员才可以催刀，查询请使用查王/差刀命令')
            return
        msg = event.message
        s = ''
        for seg in msg:
            s += ' ' + str(seg).strip()
        s = s.lstrip().split(' ')
        com = change_plan(s[0],s[1],s[2])
        await bot.send(event,f'指令 {com} 插入成功！')

    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')

