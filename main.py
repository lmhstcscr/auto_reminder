import pandas as pd
import requests
import json
import copy
import sqlite3
import dateutil
import uuid
from win32com.client import Dispatch
from selenium import webdriver
import time
import datetime
import os
from selenium.webdriver.common.action_chains import ActionChains

QQ_ACCOUNT = '' #BOTQQ
PASSWORD = '' #BOTQQ密码
YOBOT_API = "" #工会YOBOT的API
PLAN_MODE = 2  # 1表示本地文档同步  2表示腾讯文档爬虫同步（想做API可是腾讯在线文档API好像不够用）
SCIPT_DIR = os.path.split(os.path.realpath(__file__))[0]
DB_PATH = SCIPT_DIR + r"\clan_battle_enhance.db"
LOCAL_PLAN_PATH = SCIPT_DIR + r"\双子座-排刀统计.xlsx" #改成排刀用的在线文档的名字
GROUP_ID = ''#目前没啥用
CHANGE_PLAN_COM = 'CHANGE_PLAN'
CHANGE_FINISH_COM = 'CHANGE_FINISHED'
NAMESPACE = uuid.NAMESPACE_URL


def _just_open(filename): #需要服务器装个金山文档，不用爬虫的话不用装
    xlApp = Dispatch("Excel.Application")
    time.sleep(0.5)
    xlApp.Visible = False
    xlBook = xlApp.Workbooks.Open(filename)
    time.sleep(0.5)
    xlBook.Save()
    xlBook.Close()


def _get_today_range():
    now_date = _get_today_pcrdate()
    now_start = datetime.datetime(now_date.year, now_date.month, now_date.day, 5, 0, 0)
    now_end = now_start + datetime.timedelta(days=1)
    return now_start, now_end


def _get_today_pcrdate():
    now_hour = datetime.datetime.now().hour
    if now_hour >= 0 and now_hour < 5:
        now_date = datetime.datetime.now().date() - datetime.timedelta(days=1)
    else:
        now_date = datetime.datetime.now().date()
    return now_date


def _is_today_pcrdate(date_time: datetime.datetime):
    now_start, now_end = _get_today_range()
    if date_time >= now_start and date_time < now_end:
        return True
    else:
        return False


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


def get_plan_excel(): #遇到验证码要手动
    if os.path.exists(LOCAL_PLAN_PATH):  # 如果文件存在
        os.remove(LOCAL_PLAN_PATH)
    options = webdriver.ChromeOptions()
    SCIPT_DIR = os.path.split(os.path.realpath(__file__))[0]
    prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': SCIPT_DIR}
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(30)
    driver.maximize_window()
    doc_path = 'https://docs.qq.com/sheet/DUGtKV014U1B5cUN2'
    driver.get(doc_path)
    driver.find_element_by_id("header-login-btn").click()
    driver.switch_to.frame(driver.find_element_by_id('login_frame'))
    driver.find_element_by_id("switcher_plogin").click()
    login_ac = ActionChains(driver)
    login_ac.send_keys_to_element(driver.find_element_by_xpath('//*[@id="u"]'), QQ_ACCOUNT)
    login_ac.send_keys_to_element(driver.find_element_by_xpath('//*[@id="p"]'), PASSWORD)
    login_ac.click(driver.find_element_by_id('login_button'))
    login_ac.perform()
    driver.switch_to.default_content()
    driver.find_element_by_xpath('//*[@id="header-top"]/div[2]/div[2]/div/div[1]/div/div/div/div/div/div/div').click()
    el = driver.find_element_by_css_selector(
        'body > div.dui-dropdown-content.dui-dropdown-content-bottom.dui-dropdown-content-visible.dui-dropdown-content-no-animation > ul > div:nth-child(6) > div > div > li')
    ac = ActionChains(driver).move_to_element(el)
    ac.perform()
    time.sleep(0.5)
    ac.move_by_offset(-200, 0)
    ac.click()
    ac.perform()
    print('clicked')
    time.sleep(15)
    driver.quit()


class PlanCollector:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS plan_table(qqid VARCHAR(20) NOT NULL, pcrdate DATE NOT NULL,qqname TEXT, first_dao TEXT ,second_dao TEXT,third_dao TEXT, PRIMARY KEY(qqid,pcrdate))"
            )
            conn.commit()

    def update_plan(self, js_dict: dict):
        today_date = _get_today_pcrdate()
        dict_date = dateutil.parser.parse(js_dict.get('update_date'))
        js_data = js_dict.get('data')
        if not _is_today_pcrdate(dict_date):
            raise Exception('排刀表时间过旧')
        with self.connect() as conn:
            for ii in js_data.values():
                qq_name = ii.get('群昵称')
                qqid = ii.get('QQ号')
                first = ii.get('第一刀')
                second = ii.get('第二刀')
                third = ii.get('第三刀')
                conn.execute(
                    "INSERT OR REPLACE INTO plan_table(qqid , qqname , pcrdate ,first_dao, second_dao, third_dao) "
                    "VALUES('{}','{}','{}','{}','{}','{}')".format(qqid, qq_name, today_date, first, second, third))
            conn.commit()

    def get_plan(self, qqid):
        today_pcrdate = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT first_dao,second_dao,third_dao FROM plan_table where qqid='{}' AND pcrdate='{}'".format(qqid,
                                                                                                                today_pcrdate))
            data_list = cursor.fetchall()
            return data_list

    def get_member(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT qqid,qqname from plan_table")
            member_list = cursor.fetchall()
            return member_list

    def get_name_from_id(self, qqid):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT qqname from plan_table where qqid={}".format(str(qqid)))
            member_list = cursor.fetchall()
            return member_list[0][0]


class PlanChanger:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS plan_change(comid VARCHAR(20) NOT NULL PRIMARY KEY ,qqid VARCHAR(20) NOT NULL, pcrdate DATE NOT NULL,qqname TEXT,"
                " boss_name1 VARCHAR(20) NOT NULL, boss_name2 VARCHAR(20) NOT NULL)"
            )
            conn.commit()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def add_change(self, qqid, boss_name1, boss_name2):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        qqname = plan_db.get_name_from_id(qqid)
        uuid_code = uuid.uuid3(NAMESPACE, str(qqid) + pcr_date + boss_name1 + boss_name2)
        with self.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO plan_change(comid,qqid,pcrdate,qqname,boss_name1,boss_name2)"
                         " VALUES('{}','{}','{}','{}','{}','{}')".format(uuid_code, qqid, pcr_date, qqname, boss_name1,
                                                                         boss_name2))
            conn.commit()

    def del_change(self, comid):
        with self.connect() as conn:
            res = self.com_query_com_id(comid)
            if not res:
                raise ValueError('不存在该指令ID')
            conn.execute("DELETE from plan_change where comid='{}'".format(comid))
            conn.commit()

    def com_query_id(self, qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT *  from plan_change where qqid='{}' and pcrdate='{}'".format(qqid, pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def com_query_com_id(self, comid):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT *  from plan_change where comid='{}' ".format(comid))
            member_list = cursor.fetchall()
            return member_list

    def com_query(self):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT *  from plan_change where  pcrdate='{}'".format(pcr_date))
            member_list = cursor.fetchall()
            return member_list


class PlanExchanger:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()
        self.exchange_list = self.update_exchange()

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS plan_exchange(exid VARCHAR(20) NOT NULL PRIMARY KEY , pcrdate DATE NOT NULL,"
                " boss_name1 VARCHAR(20) NOT NULL, boss_name2 VARCHAR(20) NOT NULL)"
            )
            conn.commit()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def add_change(self, boss_name1, boss_name2):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        uuid_code = uuid.uuid3(NAMESPACE, pcr_date + boss_name1 + boss_name2)
        with self.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO plan_exchange(exid,pcrdate,boss_name1,boss_name2)"
                         " VALUES('{}','{}','{}','{}')".format(uuid_code, pcr_date, boss_name1, boss_name2))
            conn.commit()

    def com_query(self):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT *  from plan_exchange where  pcrdate='{}'".format(pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def com_query_id(self, exid):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT *  from plan_exchange where  exid='{}'".format(exid))
            member_list = cursor.fetchall()
            return member_list

    def del_exchange(self, comid):
        with self.connect() as conn:
            res = self.com_query_id(comid)
            if not res:
                raise ValueError('不存在该ID')
            conn.execute("DELETE from plan_exchange where exid='{}'".format(comid))
            conn.commit()

    def update_exchange(self):
        exchange_list = []
        raw_list = self.com_query()
        for ii in raw_list:
            exchange_list.append((ii[2], ii[3]))
        self.exchange_list = exchange_list


class TreeController:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        '''
        state = 1:正在出刀
        state = 2:挂着
        :return:
        '''
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS tree_control(pcrdate DATE NOT NULL, target_qqid VARCHAR(20) NOT NULL, "
                "play_qqid VARCHAR(20), state INT NOT NULL, damage INT, primary key(pcrdate,target_qqid)) "
            )
            conn.commit()

    def query_tree_target(self, target_qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT *  from tree_control where  target_qqid='{}' and pcrdate='{}'".format(target_qqid, pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def query_tree_target_on_play(self, target_qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT *  from tree_control where  target_qqid='{}' and pcrdate='{}' and state=1".format(target_qqid,
                                                                                                          pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def query_tree_play(self, play_qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT *  from tree_control where  play_qqid='{}' and pcrdate='{}'".format(play_qqid, pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def query_tree_play_on_play(self, play_qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT *  from tree_control where  play_qqid='{}' and pcrdate='{}' and state=1".format(play_qqid,
                                                                                                        pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def add_tree(self, target_qqid, play_qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            if self.query_tree_target(target_qqid):
                raise ValueError('目标已经在树上!')
            conn.execute(
                f"INSERT INTO tree_control (pcrdate, target_qqid ,play_qqid,state) "
                f"VALUES('{pcr_date}','{target_qqid}','{play_qqid}',1)")
            conn.commit()

    def delete_tree_with_target(self, target_qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            if not self.query_tree_target(target_qqid):
                raise ValueError('目前没有出刀/被代刀!')
            else:
                conn.execute(
                    f"DELETE FROM tree_control where pcrdate = '{pcr_date}' and target_qqid='{target_qqid}'")
                conn.commit()

    def delete_tree_with_play(self, play_qqid):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            if not self.query_tree_play(play_qqid):
                raise ValueError('目前没有出刀/代刀!')
            else:
                conn.execute(
                    f"DELETE FROM tree_control where pcrdate = '{pcr_date}' and play_qqid='{play_qqid}'")
                conn.commit()

    def query_on_tree(self):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT *  from tree_control where  pcrdate='{}' and state=2".format(pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def query_on_play(self):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT *  from tree_control where  pcrdate='{}' and state=1".format(pcr_date))
            member_list = cursor.fetchall()
            return member_list

    def add_damage_with_play(self, target_qqid, play_qqid, damage):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            if not self.query_tree_target(target_qqid):
                self.add_tree(target_qqid,play_qqid)
            conn.execute(
                f"UPDATE tree_control SET damage={damage},state=2 where target_qqid='{target_qqid}' and play_qqid='{play_qqid}' and pcrdate='{pcr_date}'")
            conn.commit()

    def delete_whole_tree(self):
        pcr_date = _get_today_pcrdate().strftime('%Y-%m-%d')
        with self.connect() as conn:
            conn.execute(f"DELETE FROM tree_control where pcrdate='{pcr_date}'")
            conn.commit()


plan_db = PlanCollector(db_path=DB_PATH)
plan_change = PlanChanger(db_path=DB_PATH)
plan_exchange = PlanExchanger(db_path=DB_PATH)
tree_control = TreeController(db_path=DB_PATH)


class MemberState:
    def __init__(self, member_id, member_name):
        self.member_id = int(member_id)
        self.member_name = member_name
        self.plan = []
        self.finished = []
        self.conflict = []
        self.not_finished = []
        self.weidao = ()
        self.exchange = []

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
        if boss_name in self.not_finished:
            return True
        else:
            return False

    def update_plan(self):
        data_list = plan_db.get_plan(self.member_id)
        change_plan_list = plan_change.com_query_id(self.member_id)
        if data_list:
            plan_list = [data_list[0][0], data_list[0][1], data_list[0][2]]
            self.plan = plan_list
            if change_plan_list:
                for ii in change_plan_list:
                    if ii[4] in self.plan:
                        self.plan.remove(ii[4])
                        self.plan.append(ii[5])
            return
        else:
            return

    def update_finished(self, finish_dict):
        challenges = finish_dict.get('challenges')
        if len(challenges) == 0:
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
                                                 'damage': ii.get('damage'),
                                                 'health_remain': ii.get('health_ramain')})  # YOBOT的开发人员把单词拼错了
            # 注意yobot一定是正序出json的
            final_challenges = []
            for ii in today_challenges:
                if ii.get('is_continue'):  # 是补偿刀
                    if ii.get('damage') >= self.weidao[1]:  # 补偿刀伤害高
                        final_challenges.append(ii.get('boss_name'))  # 算补偿的王
                        self.weidao = ()
                    else:
                        final_challenges.append(self.weidao[0])
                        self.weidao = ()
                elif int(ii.get('health_remain')) == 0:  # 是尾刀
                    self.weidao = (ii.get('boss_name'), ii.get('damage'))
                else:
                    final_challenges.append(ii.get('boss_name'))

            self.finished = final_challenges
        # 根据指令进行调整
        return

    def update_not_finished(self):
        not_finished = copy.copy(self.plan)
        for ii in self.finished:
            if ii in not_finished:
                not_finished.remove(ii)
            else:
                is_exchange = False
                for jj in plan_exchange.exchange_list:
                    if ii == jj[0] and jj[1] in not_finished:  # 出现在互通列表中
                        not_finished.remove(jj[1])
                        self.exchange.append(jj)
                        is_exchange = True
                    elif ii == jj[1] and jj[0] in not_finished:
                        not_finished.remove(jj[0])
                        self.exchange.append(jj)
                        is_exchange = True
                if not is_exchange:
                    self.conflict.append(ii)

        self.not_finished = not_finished


def update_plan():
    if PLAN_MODE == 1:
        plan_df = pd.read_excel(LOCAL_PLAN_PATH, sheet_name='报名统计', usecols='A:F', skiprows=[0])
        plan_df.dropna(how='all', inplace=True)
        plan_df['QQ号'] = plan_df['QQ号'].apply(lambda x: str(int(x)))
    elif PLAN_MODE == 2:
        get_plan_excel()
        _just_open(LOCAL_PLAN_PATH)
        plan_df = pd.read_excel(LOCAL_PLAN_PATH, sheet_name='报名统计', usecols='A:F', skiprows=[0])
        plan_df.dropna(how='all', inplace=True)
        plan_df['QQ号'] = plan_df['QQ号'].apply(lambda x: str(int(x)))
    else:
        raise ValueError('PLAN_MODE 错误')

    plan_json = {'update_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'group_id': GROUP_ID,
                 'data': plan_df.loc[:, ['群昵称', 'QQ号', '第一刀', '第二刀', '第三刀']].to_dict(orient='index')}
    with open(SCIPT_DIR + '\\plan.json', 'w') as f:
        json.dump(plan_json, f)
    plan_db.update_plan(plan_json)
    return


def load_plan():
    try:
        with open(SCIPT_DIR + '\\plan.json', 'r') as f:
            plan_json = json.load(f)
    except:
        raise Exception('请先更新排刀信息！')
        return
    return plan_json


def change_plan(member_id, bossname1, bossname2):
    plan_change.add_change(member_id, bossname1, bossname2)


def _load_finished():
    try:
        yobot_res = requests.get(YOBOT_API)
        res_json = json.loads(yobot_res.text)
    except:
        raise Exception('同步出刀数据失败')
    return res_json


def check_boss(boss_name):
    # 查王，返回字符串
    member_list = init_member()
    boss_miss_name = []
    boss_miss_id = []
    compensate = {}
    exchange_boss = ''
    exchange_list = plan_exchange.com_query()
    for ii in exchange_list:
        if ii[2] == boss_name:
            exchange_boss = ii[3]
        elif ii[3] == boss_name:
            exchange_boss = ii[2]
    for ii in member_list:
        if ii.check_remind(boss_name):
            boss_miss_name.append(ii.member_name)
            boss_miss_id.append(ii.member_id)
        if ii.weidao:
            if ii.weidao[0] == boss_name:
                compensate[ii.member_name] = ii.weidao[1]
    msg = "尚未出{}的有: \n".format(boss_name)
    member_str = ','.join(boss_miss_name)
    member_str += '\n'
    if compensate:
        weidao_str = '卡该王尾刀的有：'
        for name, damage in compensate.items():
            weidao_str += (name + ',尾刀伤害为' + str(damage) + '；')
    else:
        weidao_str = ''
    exchange_str = ''
    if exchange_boss:
        if exchange_boss:
            exchange_str = f"\n该王有互通，为{exchange_boss}，可以补充催刀或查刀。"
    return msg + member_str + weidao_str + exchange_str


def remind_boss(boss_name):
    # 查王，返回id列表，方便艾特
    member_list = init_member()
    boss_miss_name = []
    boss_miss_id = []
    compensate = {}
    exchange_boss = ''
    exchange_list = plan_exchange.com_query()
    for ii in exchange_list:
        if ii[2] == boss_name:
            exchange_boss = ii[3]
        elif ii[3] == boss_name:
            exchange_boss = ii[2]
    for ii in member_list:
        if ii.check_remind(boss_name):
            boss_miss_name.append(ii.member_name)
            boss_miss_id.append(ii.member_id)
        if ii.weidao:
            if ii.weidao[0] == boss_name:
                compensate[ii.member_name] = ii.weidao[1]
    return boss_miss_name, boss_miss_id, compensate, exchange_boss


def describe_member(member_id):
    member_list = init_member()
    for ii in member_list:
        if str(ii.member_id) == str(member_id):

            msg = "{}的今日排刀是: {} \n".format(ii.member_name, ' '.join(ii.plan))
            msg = msg + "已经出的刀是：{} \n".format(' '.join(ii.finished))
            msg = msg + "尚未出的刀是：{}".format(' '.join(ii.not_finished))
            if ii.exchange:
                for jj in ii.exchange:
                    msg = msg + f"（受到'{jj[0]}'互通'{jj[1]}'的影响）"
            msg += '\n'
            if ii.weidao:
                msg = msg + f"卡'{ii.weidao[0]}'尾刀，刀伤为{ii.weidao[1]}"
            else:
                msg = msg + "没有补偿刀"
            return msg


def init_member():
    plan_exchange.update_exchange()
    member_list = []
    member_data = plan_db.get_member()
    for ii in member_data:
        member_list.append(MemberState(ii[0], ii[1]))
    finished_data = _load_finished()  # 载入出刀数据
    # 根据排刀和出刀情况更新成员状态
    for ii in member_list:
        ii.update_plan()
        ii.update_finished(finished_data)
        ii.update_not_finished()
    return member_list


def check_plan_date():
    plan_data = load_plan()
    return "当前排刀表更新时间为：{}".format(plan_data.get('update_date'))


def check_plan_change():
    res = plan_change.com_query()
    msg = ''
    for ii in res:
        msg += f"命令ID:{ii[0]}----将{ii[3]}的'{ii[4]}'刀强制改为'{ii[5]}'刀 \n"
    return msg


def del_plan_change(uuid):
    plan_change.del_change(uuid)


def check_compensate():
    member_list = init_member()
    msg = '目前的补偿刀有：'
    buchang_str = ''
    for ii in member_list:
        if ii.weidao:
            buchang_str += f"{ii.member_name}的'{ii.weidao[0]}'尾刀，刀伤为{ii.weidao[1]}；"
    if len(buchang_str) == 0:
        buchang_str = '！！目前补偿清空了'
    msg += buchang_str
    return msg


def add_exchange(boss_name1, boss_name2):
    plan_exchange.add_change(boss_name1, boss_name2)


def check_plan_exchange():
    res = plan_exchange.com_query()
    msg = ''
    for ii in res:
        msg += f"命令ID:{ii[0]}----{ii[2]}'刀与'{ii[3]}'刀互通 \n"
    if len(msg) == 0:
        msg += '本日没有互通'
    return msg


def del_plan_exchange(exid):
    plan_exchange.del_exchange(exid)


def check_conflict():
    member_list = init_member()
    msg = ''
    for ii in member_list:
        if ii.conflict:
            msg += f'{ii.member_name}的'
            for jj in ii.conflict:
                msg += f"'{jj}'刀，"
            msg += '与排刀冲突，请注意原因。\n'
    if len(msg) == 0:
        msg += '没有冲突的成员！'
    return msg


def check_tree_state():
    onplay = tree_control.query_on_play()
    ontree = tree_control.query_on_tree()
    msg = ''
    for ii in onplay:
        if ii[1] == ii[2]:  # 自己出
            msg += f"{plan_db.get_name_from_id(ii[2])}正在出自己的刀\n"
        else:
            msg += f"{plan_db.get_name_from_id(ii[2])}正在代{plan_db.get_name_from_id(ii[1])}的刀\n"
    for ii in ontree:
        if ii[1] == ii[2]:  # 自己出
            msg += f"{plan_db.get_name_from_id(ii[2])}挂自己刀，伤害为{str(ii[4])} \n"
        else:
            msg += f"{plan_db.get_name_from_id(ii[2])}正在挂{plan_db.get_name_from_id(ii[1])}的刀，伤害为{str(ii[4])} \n"
    if not msg:
        msg += '目前没有人出刀挂树'
    return msg


def add_tree(target_qqid, play_qqid):
    tree_control.add_tree(target_qqid, play_qqid)


def add_damage(target_qqid, play_qqid, damage):
    tree_control.add_damage_with_play(target_qqid, play_qqid, damage)


def delete_tree_target(target_qqid):
    tree_control.delete_tree_with_target(target_qqid)


def delete_tree_play(play_qqid):
    tree_control.delete_tree_with_play(play_qqid)


def delete_tree():
    tree_control.delete_whole_tree()


if __name__ == '__main__':
    # _just_open(LOCAL_PLAN_PATH)
    # update_plan()
    change_plan('173587464', 'C1', 'C4')
    MB = describe_member('453300604')
    CB = check_boss('C1')
    BC = check_compensate()
    add_exchange('C1', 'C5')
    # del_plan_exchange('e8e9bf67-26b7-36d8-8848-226d26518ba0')
    EX = check_plan_exchange()
    delete_tree()
    add_tree('173587464', '453300604')
    add_tree('2772791540', '453300604')
    add_damage('173587464', '453300604', 123456)
    TS = check_tree_state()
    delete_tree_play('453300604')
    TS2 = check_tree_state()
