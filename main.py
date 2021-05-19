import pandas  as pd
import requests
import os
import json
import datetime

YOBOT_API = ""
PLAN_MODE = 1  # 1表示本地文档同步  2表示腾讯文档API同步
SCIPT_DIR = os.path.split(os.path.realpath(__file__))[0]
LOCAL_PLAN_PATH = SCIPT_DIR + r"\plan.xlsx"
GROUP_ID = '417488094'
CHANGE_PLAN_COM = 'CHANGE_PLAN'
CHANGE_FINISH_COM = 'CHANGE_FINISHED'

class MemberState:
    def __init__(self, member_id, member_name):
        self.member_id = int(member_id)
        self.member_name = member_name
        self.plan = []
        self.finished = []

    def check_boss_is_planed(self, boss_name):
        if boss_name in self.plan:
            return True
        else:
            return False

    def check_boss_is_finished(self, boss_name):
        if boss_name in self.finished:
            return True
        else:
            return False

    def check_remind(self, boss_name):
        if self.check_boss_is_planed(boss_name) and not self.check_boss_is_finished(boss_name):
            return True
        else:
            return False

    def update_plan(self, plan_dict):
        plan_data = plan_dict.get('data')
        for ii in plan_data.keys():
            if plan_data.get(ii).get('QQ号') == str(self.member_id):
                self.plan = [plan_data.get(ii).get('第一刀'), plan_data.get(ii).get('第二刀'), plan_data.get(ii).get('第三刀')]
        # 下面为临时该排刀留空间
        with open(SCIPT_DIR+r'\\change.txt','r') as f:
            command_lines=f.readlines()
        start_date,end_date=_get_today_range()
        for ii in command_lines:
            com_list=ii.split(' ')
            if len(ii)<=2:
                continue
            if str(com_list[2])==str(self.member_id):
                if com_list[0]==CHANGE_PLAN_COM \
                        and (datetime.datetime.fromtimestamp(float(com_list[1]))>=start_date
                             and datetime.datetime.fromtimestamp(float(com_list[1]))<=end_date):#找到了对应id需要的变换排刀指令
                    new_plan=[]
                    is_changed=False
                    for jj in self.plan:
                        if jj == com_list[3] and not is_changed:
                            new_plan.append(com_list[4]) #确定了就换
                            is_changed=True
                        else:
                            new_plan.append(jj)
                    self.plan=new_plan
            return

    def update_finished(self, finish_dict):
        challenges = finish_dict.get('challenges')
        if len(challenges) == 0:
            print('没有出刀记录！')
            return
        else:
            now_start, now_end = _get_today_range()
            today_challenges = []
            for ii in challenges:
                cha_date = datetime.datetime.fromtimestamp(ii.get('challenge_time'))
                if cha_date >= now_start and cha_date <= now_end:  # 今日出刀
                    if ii.get('qqid') == self.member_id:  # 本成员刀型
                        today_challenges.append({'boss_name': _yoboss2myboss(ii.get('cycle'), ii.get('boss_num')),
                                                 'cha_time': datetime.datetime.fromtimestamp(ii.get('challenge_time')),
                                                 'is_continue': ii.get('is_continue'),
                                                 'damage': ii.get('damage')})
            # 注意yobot一定是倒序出json的，所以已经排好序了
            today_challenges.reverse()
            final_challenges = []
            is_continue = False
            temp_damage = 0
            temp_boss = ''
            for ii in today_challenges:
                if is_continue == True:  # 如果上一个记录是补偿刀
                    this_damage = int(ii.get('damage'))
                    if this_damage > temp_damage:  # 如果尾刀伤害比补偿刀高
                        final_challenges.append(ii.get('boss_name'))
                        is_continue = False  # 复原标记
                    else:
                        final_challenges.append(temp_boss)  # 如果补偿刀刀伤高，记补偿刀的BOSS
                        is_continue = False  # 复原标记
                    continue

                if ii.get('is_continue'):  # 如果是补偿刀
                    is_continue = True  # 补偿刀标记启用
                    temp_damage = int(ii.get('damage'))
                    temp_boss = ii.get('boss_name')
                else:  # 如果不是补偿刀
                    final_challenges.append(ii.get('boss_name'))
            self.finished = final_challenges
        #根据指令进行调整
        with open(SCIPT_DIR+r'\\change.txt','r') as f:
            command_lines=f.readlines()
        start_date,end_date=_get_today_range()
        for ii in command_lines:
            com_list=ii.split(' ')
            if len(ii)<=2:
                continue
            if str(com_list[2])==str(self.member_id):
                if com_list[0]==CHANGE_FINISH_COM \
                        and (datetime.datetime.fromtimestamp(float(com_list[1]))>=start_date
                             and datetime.datetime.fromtimestamp(float(com_list[1]))<=end_date):#找到了对应id需要的变换排刀指令
                    new_finish=[]
                    is_changed=False
                    for jj in self.finished:
                        if jj == com_list[3] and not is_changed:
                            new_finish.append(com_list[4]) #确定了就换
                            is_changed=True
                        else:
                            new_finish.append(jj)
                    self.finished=new_finish
        return


def _get_today_range():
    now_date=datetime.datetime.now().date()
    now_start = datetime.datetime(now_date.year, now_date.month, now_date.day, 5, 0, 0)
    now_end = now_start + datetime.timedelta(days=1)
    return now_start, now_end


def _yoboss2myboss(cycle, bossnum):
    """
    将来肯定要改，四阶段的时候。用于根据圈数转化为标准王字符
    :param cycle:
    :param bossnum:
    :return:
    """
    cycle = int(cycle)
    if cycle >= 1 and cycle <= 3:
        return 'A' + str(bossnum)
    elif cycle >= 4 and cycle <= 10:
        return 'B' + str(bossnum)
    else:
        return 'C' + str(bossnum)


def update_plan():
    if PLAN_MODE == 1:
        plan_df = pd.read_excel(LOCAL_PLAN_PATH, sheet_name='报名统计', usecols='A:F', skiprows=[0], data_only=True)
        plan_df.dropna(how='all', inplace=True)
        plan_df['QQ号'] = plan_df['QQ号'].apply(lambda x: str(int(x)))

    plan_json = {'update_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'group_id': GROUP_ID,
                 'data': plan_df.loc[:, ['群昵称', 'QQ号', '第一刀', '第二刀', '第三刀']].to_dict(orient='index')}
    with open(SCIPT_DIR + '\\plan.json', 'w') as f:
        json.dump(plan_json, f)
    return


def load_plan():
    try:
        with open(SCIPT_DIR + '\\plan.json', 'r') as f:
            plan_json = json.load(f)
    except:
        raise Exception('请先更新排刀信息！')
        return
    return plan_json


def change_plan(member_id,bossname1,bossname2):
    now_time=datetime.datetime.now()
    now_time=now_time-datetime.timedelta(5)
    now_time=now_time.timestamp()
    change_str= "{} {} {} {} {}\n".format(CHANGE_PLAN_COM,now_time,member_id,bossname1,bossname2)
    with open(SCIPT_DIR+r'\\change.txt','a') as f:
        f.write(change_str)
    return

def change_finished(member_id,bossname1,bossname2):
    now_time = datetime.datetime.now()
    now_time = now_time - datetime.timedelta(5)
    now_time = now_time.timestamp()
    change_str="{} {} {} {} {}\n".format(CHANGE_FINISH_COM,now_time,member_id,bossname1,bossname2)
    with open(SCIPT_DIR+r'\\change.txt','a') as f:
        f.write(change_str)
    return


def load_finished():
    try:
        yobot_res = requests.get(YOBOT_API)
        res_json = json.loads(yobot_res.text)
    except:
        raise Exception('同步出刀数据失败')
    return res_json


def check_boss(boss_name):
    member_list=init_member()
    boss_miss_name = []
    boss_miss_id = []
    for ii in member_list:
        if ii.check_remind(boss_name):
            boss_miss_name.append(ii.member_name)
            boss_miss_id.append(ii.member_id)
    msg = "尚未出{}的有: \n".format(boss_name)
    member_str = ','.join(boss_miss_name)
    return msg + member_str

def describe_member(member_id):
    member_list = init_member()
    for ii in member_list:
        if str(ii.member_id)==str(member_id):
            plan_set=set(ii.plan)
            finished_set=set(ii.finished)
            not_finished=list(plan_set-finished_set)
            msg="{}的今日排刀是: {} \n".format(ii.member_name,' '.join(ii.plan))
            msg=msg+"已经出的刀是：{} \n".format(' '.join(ii.finished))
            msg=msg+"尚未出的刀是：{}".format(' '.join(not_finished))
            return msg


def init_member():
    member_list = []
    plan_data = load_plan()  # 载入排刀数据
    print(plan_data.get('update_date'))
    for ii in plan_data.get('data').values():
        id = ii.get('QQ号')
        name = ii.get('群昵称')
        member_list.append(MemberState(id, name))
    finished_data = load_finished()  # 载入出刀数据
    # 根据排刀和出刀情况更新成员状态
    for ii in member_list:
        ii.update_plan(plan_data)
        ii.update_finished(finished_data)
    return member_list

def check_plan_date():
    plan_data = load_plan()
    return "当前排刀表更新时间为：{}".format(plan_data.get('update_date'))


