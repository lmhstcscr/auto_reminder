from .main import *
from hoshino import Service, priv
import math

sv_help = '''
星痕会战增强系统帮助
请服务器部署者每日讲今日的排刀表格放置于服务器该脚本目录下
示例：星痕查BOSS,星痕查王,星痕查刀 + 【A1】 查询当前BOSS的出刀情况，任意成员均可
星痕催BOSS,星痕催王,星痕催刀 + 【A1】 直接艾特未出刀成员，需要管理员权限
星痕查询排刀版本,星痕查询排刀信息 无参数，查询当前排刀表版本
星痕排刀更新，星痕更新排刀表，星痕更新排刀 无参数，根据服务器部署者放置在服务器上的当日排刀表更新模块使用的排刀数据，需要管理员权限
星痕查成员 + 【qq号】或者艾特 查询某个成员当前出刀的情况
星痕强制改刀 + 【qq号 C1 C3】 临时强制更改某个成员的排刀，需要管理员权限
星痕改刀查询，星痕查询改刀 无参数，返回当天强制改刀情况
星痕改刀删除，星痕删除改刀 + 命令id 根据命令id删除某一条改刀指令，需要管理员权限
星痕查补偿,星痕查尾刀,星痕查询补偿,星痕查询尾刀,星痕查补偿刀 查询目前有哪些成员有尾刀，尾刀伤害是多少
星痕互通 + BOSS1 + BOSS2 设定阵容相同或者配置可以互换的王，便于筛刀改刀和卡刀救人，需要管理员权限
星痕查询互通，星痕互通查询 查询当日互通信息
星痕删除互通，星痕互通删除 + 命令id 删除制定互通权限，需要管理员权限
###下面是筛刀增强
开始出刀，进到 +艾特或不艾特  表明开始进了，注意不要卡住代刀角色
报树 +艾特或者不艾特  报伤害病挂树
撤树 +艾特或者不艾特  撤销自己或者代理的他人的上树
报刀 +艾特或者不艾特  联动yobot 下树
尾刀 +艾特或者不艾特  联动yobot 直接砍树
状态，差树  联动yobot，观察当前树的情况，防止撞号
目前查询都只查询当天的情况，因此管理员应当定时清理过时数据以免垃圾指令和数据堆叠
'''.strip()
sv = Service(
    name='星痕会战增强',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # False隐藏
    enable_on_default=True,  # 是否默认启用
    bundle='会战',  # 属于哪一类
    help_=sv_help  # 帮助文本
)


@sv.on_fullmatch(("帮助星痕会战增强", "星痕会战增强帮助"))
async def bangzhu(bot, ev):
    await bot.send(ev, sv_help, at_sender=True)


@sv.on_prefix(('星痕查BOSS', '星痕查王', '星痕查刀'))
async def check_outer(bot, event):
    try:
        input_para = event.message.extract_plain_text()
        msg = check_boss(input_para)
        await bot.send(event, msg, at_sender=True)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_prefix(('星痕催BOSS', '星痕催王', '星痕催刀'))
async def remind_outer(bot, event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，只有管理员才可以催刀，查询请使用查王/查刀命令')
            return
        input_para = event.message.extract_plain_text()
        name_list, id_list, compensate, exchange_boss = remind_boss(input_para)
        msg = "尚未出{}的有: \n".format(input_para)
        msg = msg + ','.join(name_list)
        msg = msg + "\n"
        for ii in id_list:
            msg = msg + f"[CQ:at,qq={ii}]"
        if compensate:
            msg += '\n卡该王尾刀的有：'
            for name, damage in compensate.items():
                msg += (name + ',尾刀伤害为' + str(damage) + '；')
            msg += '\n补偿刀请根据实际情况手动补艾特'
        if exchange_boss:
            msg += f"\n该王有互通，为{exchange_boss}，可以补充催刀或查刀。"
        await bot.send(event, msg, at_sender=True)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_prefix(('星痕查成员'))
async def check_member(bot, event):
    try:
        if event.message[0].type == 'at':  # 如果以艾特形式出现
            input_para = int(event.message[0].data['qq'])
        else:  # 如果直接输入QQ
            input_para = event.message.extract_plain_text()

        msg = describe_member(input_para)
        await bot.send(event, msg, at_sender=True)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_fullmatch(('星痕查询排刀版本', '星痕查询排刀信息'))
async def check_plan_time(bot, event):
    try:
        msg = check_plan_date()
        await bot.send(event, msg, at_sender=True)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_fullmatch(('星痕排刀更新', '星痕更新排刀表','星痕更新排刀'))
async def update_plan_outer(bot, event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，您无权使用此指令，请联系管理员')
            return
        await bot.send(event, '爬虫更新排刀表，BOT30s左右无反应！')
        update_plan()
        await bot.send(event, '排刀表更新完毕！')
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_prefix(('星痕强制改刀'))
async def change_plan_outer(bot, event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，只有管理员才可以催刀，查询请使用查王/差刀命令')
            return
        msg = event.message
        s = ''
        for seg in msg:
            s += ' ' + str(seg).strip()
        s = s.lstrip().split(' ')
        change_plan(s[0], s[1], s[2])
        await bot.send(event, f'指令插入成功！')

    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_fullmatch(('星痕改刀查询', '星痕查询改刀'))
async def check_change_plan_outer(bot, event):
    try:
        msg = main.check_plan_change()
        await bot.send(event, msg)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_prefix(('星痕删除改刀', '星痕改刀删除'))
async def del_change_plan_outer(bot, event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，您无权使用此指令，请联系管理员')
            return
        msg = event.message
        del_plan_change(msg)
        await bot.send(event, '指令删除成功')
    except:
        await bot.send(event, '指令id不正确，或者程序有BUG')


@sv.on_fullmatch(('星痕查补偿', '星痕查尾刀', '星痕查询补偿', '星痕查询尾刀', '星痕查补偿刀'))
async def outer_check_compensate(bot, event):
    try:
        msg = check_compensate()
        await bot.send(event, msg)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_prefix(('星痕互通'))
async def exchange_plan_outer(bot, event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，只有管理员才可以催刀，查询请使用查王/差刀命令')
            return
        msg = event.message
        s = ''
        for seg in msg:
            s += ' ' + str(seg).strip()
        s = s.lstrip().split(' ')
        add_exchange(s[0], s[1])
        await bot.send(event, f'指令插入成功！')

    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_fullmatch(('星痕互通查询', '星痕查询互通'))
async def check_exchange_plan_outer(bot, event):
    try:
        msg = main.check_plan_exchange()
        await bot.send(event, msg)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_prefix(('星痕删除互通', '星痕互通删除'))
async def del_exchange_plan_outer(bot, event):
    try:
        if not priv.check_priv(event, priv.ADMIN):
            await bot.send(event, '抱歉，您无权使用此指令，请联系管理员')
            return
        msg = event.message
        del_plan_exchange(msg)
        await bot.send(event, '指令删除成功')
    except:
        await bot.send(event, '指令id不正确，或者程序有BUG')


@sv.on_fullmatch(('星痕冲突查询', '星痕查询冲突', '星痕查冲突'))
async def check_conflict_outer(bot, event):
    try:
        msg = main.check_conflict()
        await bot.send(event, msg)
    except:
        await bot.send(event, '请注意输入格式，或者程序有BUG')


@sv.on_rex('^尾刀 ?(?:\[CQ:at,qq=(\d+)\])? *(昨[日天])? *(?:[\:：](.*))?$')
async def end_tree(bot,event):
    try:
        delete_tree()
        await bot.send(event, '结束挂树筛刀，本轮记录删除')
    except:
        await bot.send(event, '查询命令格式，或者程序有BUG')

@sv.on_rex('^报刀 ?(\d+)([Ww万Kk千])? *(?:\[CQ:at,qq=(\d+)\])? *(昨[日天])? *(?:[\:：](.*))?$')
async def baodao(bot,event):
    try:
        gid = str(event['group_id'])
        play_id = str(event['user_id'])
        target_id = str(event['user_id'])
        play_name=await bot.get_group_member_info(group_id=gid, user_id=play_id)
        play_name = play_name['nickname']
        at_name=''
        for m in event['message']:
            if m['type'] == 'at' and m['data']['qq'] != 'all':
                # 检查消息有没有带@信息，有的话target_id改为@的QQ号
                target_id= str(m['data']['qq'])
                at_name = await bot.get_group_member_info(group_id=gid, user_id=target_id)
                at_name = at_name['nickname']
        if at_name:
            delete_tree_target(target_id)
            await  bot.send(event, f'{play_name}代{at_name}的刀下树')
        else:
            delete_tree_target(target_id)
            await  bot.send(event, f'{play_name}的刀下树')

    except ValueError:
        return

    except Exception:
        await bot.send(event, '查询命令格式，或者程序有BUG')

@sv.on_prefix(('开始出刀','进刀'))
async def start_dao(bot,event):
    try:
        gid = str(event['group_id'])
        play_id = str(event['user_id'])
        target_id = str(event['user_id'])
        play_name = await bot.get_group_member_info(group_id=gid, user_id=play_id)
        play_name = play_name['nickname']
        at_name = ''
        for m in event['message']:
            if m['type'] == 'at' and m['data']['qq'] != 'all':
                # 检查消息有没有带@信息，有的话target_id改为@的QQ号
                target_id = str(m['data']['qq'])
                at_name = await bot.get_group_member_info(group_id=gid, user_id=target_id)
                at_name = at_name['nickname']
        if at_name:
            add_tree(target_id,play_id)
            await  bot.send(event, f'{play_name}代{at_name}开始筛刀')
        else:
            add_tree(target_id,play_id)
            await  bot.send(event, f'{play_name}开始筛刀')
    except ValueError:
        await bot.send(event, '该成员已经在树上，下次请先查看状态，不会撞刀了吧，不会吧不会吧')
    except:
        await bot.send(event, '查询命令格式，或者程序有BUG')

@sv.on_prefix(('报树'))
async def baoshu(bot,event):
    try:
        damage = int(event.message.extract_plain_text())
        gid = str(event['group_id'])
        play_id = str(event['user_id'])
        target_id = str(event['user_id'])
        play_name = await bot.get_group_member_info(group_id=gid, user_id=play_id)
        play_name = play_name['nickname']
        at_name = ''
        for m in event['message']:
            if m['type'] == 'at' and m['data']['qq'] != 'all':
                # 检查消息有没有带@信息，有的话target_id改为@的QQ号
                target_id = str(m['data']['qq'])
                at_name = await bot.get_group_member_info(group_id=gid, user_id=target_id)
                at_name = at_name['nickname']
        if at_name:
            add_damage(target_id,play_id,damage)
            await  bot.send(event, f"{play_name}代{at_name},刀伤'{str(damage)} 上树'")
        else:
            add_damage(target_id,play_id,damage)
            await  bot.send(event, f"{play_name},刀伤'{str(damage)} 上树'")
    except:
        await bot.send(event, '查询命令格式，或者程序有BUG')

@sv.on_prefix('撤树')
async def cancle_tree(bot,event):
    try:
        gid = str(event['group_id'])
        play_id = str(event['user_id'])
        target_id = str(event['user_id'])
        play_name = await bot.get_group_member_info(group_id=gid, user_id=play_id)
        play_name = play_name['nickname']
        at_name = ''
        for m in event['message']:
            if m['type'] == 'at' and m['data']['qq'] != 'all':
                # 检查消息有没有带@信息，有的话target_id改为@的QQ号
                target_id = str(m['data']['qq'])
                at_name = await bot.get_group_member_info(group_id=gid, user_id=target_id)
                at_name = at_name['nickname']
        if at_name:
            delete_tree_target(target_id)
            await  bot.send(event, f"撤销{play_name}代{at_name}的挂树'")
        else:
            delete_tree_target(target_id)
            await  bot.send(event, f"撤销{play_name}的挂树'")
    except ValueError:
        await bot.send(event, f'目前没有在树上的记录')
    except:
        await bot.send(event, '查询命令格式，或者程序有BUG')


@sv.on_fullmatch(('状态', '查树'))
async def tree_state_outer(bot,event):
    try:
        msg=check_tree_state()
        await bot.send(event, msg)
    except:
        await bot.send(event, '查询命令格式，或者程序有BUG')


@sv.on_prefix('合刀')
async def hedao(bot, event):
    shanghai = event.message.extract_plain_text().strip()
    shanghai = shanghai.split()
    if not shanghai:
        msg = '请输入：合刀 刀1伤害 刀2伤害 剩余血量\n如：合刀 50 60 70'
        await bot.finish(event, msg)
    if len(shanghai) != 3:
        return
    if is_number(shanghai[0]) is False:
        return
    if is_number(shanghai[1]) is False:
        return
    if is_number(shanghai[2]) is False:
        return
    dao_a = int(shanghai[0])
    dao_b = int(shanghai[1])
    current_hp = int(shanghai[2])
    if dao_a + dao_b < current_hp:
        await bot.finish(event, '当前合刀造成的伤害不能击杀boss')
    # a先出
    a_out = current_hp - dao_a
    a_per = a_out / dao_b
    a_t = (1 - a_per) * 90 + 10
    a_result = math.ceil(a_t)
    if a_result > 90:
        a_result = 90
    # b先出
    b_out = current_hp - dao_b
    b_per = b_out / dao_a
    b_t = (1 - b_per) * 90 + 10
    b_result = math.ceil(b_t)
    if b_result > 90:
        b_result = 90
    msg = f'{dao_a}先出，另一刀可获得{a_result}秒补偿刀\n{dao_b}先出，另一刀可获得{b_result}秒补偿刀'
    await bot.send(event, msg)


def is_number(s):
    '''判断是否是数字'''
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False