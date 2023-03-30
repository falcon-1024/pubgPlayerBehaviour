import time
import sys
import os
import xmltojson
import re
import json
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
import traceback
from selenium.webdriver.firefox.options import Options as FirefoxOptions

options = FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)

# driver = webdriver.Firefox()

links = ['https://pubg.op.gg/leaderboard/?platform=steam&mode=competitive-tpp&queue_size=4',
         'https://pubg.op.gg/leaderboard/?platform=steam&mode=competitive-fpp&queue_size=4',
         'https://pubg.op.gg/leaderboard/?platform=steam&mode=competitive-tpp&queue_size=1',
         'https://pubg.op.gg/leaderboard/?platform=kakoo&mode=competitive-tpp&queue_size=4']

done_user_list = []

def get_match_summary_from_element(element):
    match_summary = i.find_element(By.CLASS_NAME,"matches-item__summary")
    data = {}
    data['type'] = match_summary.find_element(By.CLASS_NAME,"matches-item__mode").text
    data['type2'] = i.find_elements(By.TAG_NAME,"i")[0].get_attribute("class")
    data['time'] = match_summary.find_element(By.CLASS_NAME,"matches-item__reload-time").get_attribute("data-ago-date")
    print(data['time'])
    data['player_survive_time'] = match_summary.find_element(By.CLASS_NAME,"matches-item__time-value").get_attribute("data-game-length")
    data['team_placement'] = match_summary.find_element(By.CLASS_NAME,"matches-item__ranking").text[1:].split("/")[0]
    data['game_size'] = match_summary.find_element(By.CLASS_NAME,"matches-item__ranking").text[1:].split("/")[1]
    data['player_kills'] = match_summary.find_element(By.CLASS_NAME,"matches-item__column--kill").text.split("\n")[0]
    data['player_dmg'] = match_summary.find_element(By.CLASS_NAME,"matches-item__column--damage").text.split("\n")[0]
    data['player_distance_travelled'] = match_summary.find_element(By.CLASS_NAME,"matches-item__column--distance").text.split("\n")[0]
    data['player_team_list'] = '|||'.join(match_summary.find_element(By.CLASS_NAME,"matches-item__column--team").text.split("\n"))
    for j in i.find_elements(By.TAG_NAME,"div"):
        if j.get_attribute("data-u-id") is not None:
            data['match_id'] = j.get_attribute("data-u-id")
            break
    return data

user_q = set()

for i in links:
    driver.get(i)
    time.sleep(1)
    for j in driver.find_elements(By.CLASS_NAME, "leader-board-top3__nickname"):
        tmp = j.get_attribute('href')
        if tmp is not None:
            user_q.add(tmp)
    for j in driver.find_elements(By.CLASS_NAME, "leader-board__nickname"):
        tmp = j.get_attribute('href')
        if tmp is not None:
            user_q.add(tmp)
    break

m_summary = pd.DataFrame()
deaths_df = pd.DataFrame(columns=["killed_by","kill_distance","killer_placement",'killer_name', 'killer_position_x',
       'killer_position_y', 'map', 'match_id', 'time', 'victim_name',
       'victim_placement', 'victim_position_x', 'victim_position_y','extra'])
match_player_details = pd.DataFrame()
cnt=1
try:
    while len(user_q)>0:
        link = user_q.pop()
        print(link)
        driver.get(link)
        for i in range(5):
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(2)
            for j in driver.find_elements(By.TAG_NAME,"button"):
                if j.text == "More":
                    j.click()
                    time.sleep(1)
                    break
        for i in driver.find_elements(By.CLASS_NAME,"matches-item"):
            for j in i.find_elements(By.TAG_NAME,"button"):
                if j.text=='open':
                    j.click()
                    time.sleep(1)
                    break
            match_summary = get_match_summary_from_element(i)
            tmp = pd.read_html(i.find_elements(By.TAG_NAME,"table")[0].get_attribute('outerHTML'))[0]
            tmp['match_id'] = match_summary['match_id']
            match_player_details = pd.concat([match_player_details,tmp],ignore_index=True)
            # match_team_stats = pd.read_html(i.find_elements(By.TAG_NAME,"table")[1].get_attribute('outerHTML'))[0]
            i.find_elements(By.CLASS_NAME,"matches-detail__btn")[2].click()
            time.sleep(3)
            try:
                map_src = i.find_elements(By.CLASS_NAME,"matches-detail__contents")[2].find_element(By.TAG_NAME,"img").get_attribute("src")
            except:
                time.sleep(5)
                map_src = i.find_elements(By.CLASS_NAME,"matches-detail__contents")[2].find_element(By.TAG_NAME,"img").get_attribute("src")
            for j in i.find_element(By.CLASS_NAME,"kill-log__l-map-info").find_elements(By.TAG_NAME,"li"):
                tmp=j.text.split("\n")
                if len(tmp)<3:
                    continue
                tmp1 = j.find_element(By.TAG_NAME,"button").get_attribute('data-pos').replace("|",",").split(",")
                if tmp1[3] == 'me':
                    victom = link.split("/")[-1]
                    killer = tmp1[-1]
                    killer_p = np.nan
                    victom_p = match_summary['team_placement']
                else:
                    victom = tmp1[3]
                    killer = link.split("/")[-1]
                    killer_p = match_summary['team_placement']
                    victom_p = tmp[-2][1:-1]
                deaths_df.loc[len(deaths_df)] = [tmp[-1].split(" ")[0],tmp[2].split("(")[-1][:-1],killer_p,killer,tmp1[5],tmp1[6],map_src,
                                                 match_summary['match_id'],match_summary['time'],victom,victom_p,tmp1[1],tmp1[2],'|||'.join(tmp+tmp1)]
            match_team_summary = i.find_element(By.CLASS_NAME,"matches-detail__l-table").get_attribute("outerHTML")
            match_summary['player_dist_ride'] = match_team_summary.split("Ride Distance")[0].split("km")[-2].split(">")[-1].strip()
            match_summary['player_dist_walk'] = match_team_summary.split("Walk Distance")[0].split("km")[-2].split(">")[-1].strip()
            match_summary['player_dbno'] = match_team_summary.split("DBNO")[0].split("div")[-3].split(">")[-1].split("<")[0]
            match_summary['player_assists'] = match_team_summary.split("Assists")[0].split("div")[-3].split(">")[-1].split("<")[0]
            match_summary['player_name'] = link.split("/")[-1]
            m_summary = pd.concat([m_summary,pd.DataFrame(match_summary,index=[0])],ignore_index=True)
        if(len(m_summary)>10000):
            m_summary.to_csv(f"match_{cnt}.csv",index=False)
            deaths_df.to_csv(f"desth_{cnt}.csv",index=False)
            cnt+=1
            m_summary = pd.DataFrame()
            deaths_df = pd.DataFrame(columns=["killed_by","kill_distance","killer_placement",'killer_name', 'killer_position_x',
                   'killer_position_y', 'map', 'match_id', 'time', 'victim_name', 'victim_placement', 
                      'victim_position_x', 'victim_position_y','extra'])
except Exception as ex:
    print(ex)
    traceback.print_exc()
    m_summary.to_csv(f"match_{cnt}.csv",index=False)
    deaths_df.to_csv(f"desth_{cnt}.csv",index=False)