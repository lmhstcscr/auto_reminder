from .main import *
from hoshino import Service, priv
sv_help = '''
帮助文档稍后再写
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

@sv.on_fullmatch(["帮助星痕催刀"])
async def bangzhu(bot, ev):
    await bot.send(ev, sv_help, at_sender=True)

@sv.on_prefix(('星痕催刀'))
async def set_temp(bot,event):
    try:
        input_para=event.message.extract_plain_text()
        msg=check_boss(input_para)
        await bot.send(event,msg, at_sender=True)
    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')
        
@sv.on_prefix(('星痕查询'))
async def set_temp(bot,event):
    try:
        input_para=event.message.extract_plain_text()
        msg=describe_member(input_para)
        await bot.send(event,msg, at_sender=True)
    except :
        await bot.send(event, '请注意输入格式，或者程序有BUG')