"""Scrapes PitchFX data from MLB site and combines with other game info.

Copyright (C) 2015
Author: John Choiniere

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from bs4 import BeautifulSoup

import datetime
import os
import re

from urllib.error import HTTPError
from urllib.request import urlopen


def ballcode_out(description):
    """Return the ballcode for an out by the batter."""
    if description.lower().count("grounds") > 0:
        battedball_cd = "G"
    elif description.lower().count("lines") > 0:
        battedball_cd = "L"
    elif description.lower().count("flies") > 0:
        battedball_cd = "F"
    elif description.lower().count("pops") > 0:
        battedball_cd = "P"
    else:
        battedball_cd = ""
    return battedball_cd


def ballcode_hit(description):
    """Determine the ball code for a hit event."""
    if description.count("line drive") > 0:
        battedball_cd = "L"
    elif description.count("fly ball") > 0:
        battedball_cd = "F"
    elif description.count("ground ball") > 0:
        battedball_cd = "G"
    elif description.count("pop up") > 0:
        battedball_cd = "P"
    else:
        battedball_cd = ""
    return battedball_cd

# Open files for output of data.
pitch_outfile = open("pitch_table.csv", "a+", encoding='utf-8')
atbat_outfile = open("atbat_table.csv", "a+", encoding='utf-8')

# Determine start and end date of data scrape. Unused function at start
# to pick up where the file left off removed.
# file_cont = ""
# while file_cont!="yes" and file_cont!="no":
# file_cont = input("Continue files from previous spot? Type yes/no: ")'''

# if file_cont == "yes":
#    ll_retroid = pitch_outfile.readlines()[-1:][0].split(",")[0]
#    startdate = datetime.date(
#        int(ll_retroid[0:4]), int(ll_retroid[4:6]), int(ll_retroid[6:8])
#        ) + datetime.timedelta(days=1)
# else:
startdate_choice_fl = ""
while startdate_choice_fl != "yes" and startdate_choice_fl != "no":
    startdate_choice_fl = input("Choose starting date? Type yes or no: ")

if startdate_choice_fl == "yes":
    start_year = int(input("Starting year: "))
    start_month = int(input("Starting month: "))
    start_day = int(input("Starting day: "))
    startdate = datetime.date(start_year, start_month, start_day)
else:
    startdate = datetime.date(2008, 1, 1)

enddate_choice_fl = ""
while enddate_choice_fl != "yes" and enddate_choice_fl != "no":
    enddate_choice_fl = input("Choose ending date? Type yes or no: ")

if enddate_choice_fl == "yes":
    end_year = int(input("Ending year: "))
    end_month = int(input("Ending month: "))
    end_date = int(input("Ending day: "))
    enddate = datetime.date(end_year, end_month, end_date)
else:
    enddate = datetime.date.today() - datetime.timedelta(days=1)

if os.stat("pitch_table.csv").st_size == 0:
    pitch_outfile.write("""retro_game_id,year,st_fl,regseason_fl,playoffs_fl,game_type,game_type_des,game_id,home_team_id,home_team_lg,away_team_id,away_team_lg,interleague_fl,inning,bat_home_id,park_id,park_name,park_lock,pit_id,bat_id,pit_hand_cd,bat_hand_cd,pa_ball_ct,pa_strike_ct,outs_ct,pitch_seq,pa_terminal_fl,pa_event_cd,start_bases_cd,end_bases_cd,event_outs_ct,ab_number,pitch_res,pitch_des,pitch_id,x,y,start_speed,end_speed,sz_top,sz_bot,pfx_x,pfx_z,px,pz,x0,y0,z0,vx0,vy0,vz0,ax,ay,az,break_y,break_angle,break_length,pitch_type,pitch_type_seq,type_conf,zone,spin_dir,spin_rate,sv_id\n""")

if os.stat("atbat_table.csv").st_size == 0:
    atbat_outfile.write("""retro_game_id,year,month,day,st_fl,regseason_fl,playoff_fl,game_type,game_type_des,local_game_time,game_id,home_team_id,away_team_id,home_team_lg,away_team_lg,interleague_fl,park_id,park_name,park_location,inning_number,bat_home_id,inn_outs,ab_number,pit_mlbid,pit_hand_cd,bat_mlbid,bat_hand_cd,ball_ct,strike_ct,pitch_seq,pitch_type_seq,event_outs_ct,ab_des,event_tx,event_cd,battedball_cd,start_bases_cd,end_bases_cd\n""")

# Base URL for data scrape. Updated to non gd2 server.
base_url = "http://gd.mlb.com/components/game/mlb/"

delta = enddate - startdate
prior_d_url = ""

for i in range(delta.days+1):
    active_date = (startdate + datetime.timedelta(days=i))
    dt_url = (base_url + "year_" + str(
        (startdate + datetime.timedelta(days=i)).year) + "/month_" +
        active_date.strftime('%m') + "/day_" + active_date.strftime('%d'))

    print(dt_url + "/")
    try:
        urlopen(dt_url)  # Removed slash based on issues with MLB site.
        d_url = dt_url

    except Exception:
        print("excepted")
        d_url = prior_d_url

    if d_url != prior_d_url:
        day_soup = BeautifulSoup(urlopen(d_url))
        for game in day_soup.find_all('a', href=re.compile("gid_.*")):
            g = game.get_text().strip()
            if isinstance(g[len(g)-2:len(g)-1], int):
                game_number = g[len(g)-2:len(g)-1]
            else:
                game_number = 1
            g_url = d_url + "/" + g
            print(g)
            st_fl = "F"
            regseason_fl = "F"
            playoff_fl = "F"

# Attempt to parse game.xml file. Changed to try loop to handle errors.
            try:
                detail_soup = BeautifulSoup(urlopen(g_url+"game.xml"),
                                            "lxml-xml")
                if 'type' in detail_soup.game.attrs:
                    game_type = detail_soup.game["type"]
                else:
                    game_type = "U"
                if game_type == "S":
                    game_type_des = "Spring Training"
                    st_fl = "T"
                elif game_type == "R":
                    game_type_des = "Regular Season"
                    regseason_fl = "T"
                elif game_type == "F":
                    game_type_des = "Wild-card Game"
                    playoff_fl = "T"
                elif game_type == "D":
                    game_type_des = "Divisional Series"
                    playoff_fl = "T"
                elif game_type == "L":
                    game_type_des = "LCS"
                    playoff_fl = "T"
                elif game_type == "W":
                    game_type_des = "World Series"
                    playoff_fl = "T"
                else:
                    game_type_des = "Unknown"
                if 'local_game_time' in detail_soup.game.attrs:
                    local_game_time = detail_soup.game["local_game_time"]
                else:
                    local_game_time = "Unknown"
                if 'game_pk' in detail_soup.game.attrs:
                    game_id = detail_soup.game["game_pk"]
                else:
                    game_id = "unknown"
                if detail_soup.find("team"):
                    home_team_id = detail_soup.find("team",
                                                    type="home")["code"]
                    away_team_id = detail_soup.find("team",
                                                    type="away")["code"]
                    home_team_lg = detail_soup.find("team",
                                                    type="home")["league"]
                    away_team_lg = detail_soup.find("team",
                                                    type="away")["league"]
                else:
                    home_team_id = "unknown"
                    away_team_id = "unknown"
                    home_team_lg = "unknown"
                    away_team_lg = "unknown"

                if home_team_lg == away_team_lg:
                    interleague_fl = "F"
                else:
                    interleague_fl = "T"
                if detail_soup.find("stadium"):
                    park_id = detail_soup.stadium["id"]
                    park_name = detail_soup.stadium["name"]
                    park_loc = detail_soup.stadium["location"]
                else:
                    park_id = "unknown"
                    park_name = "unknown"
                    park_loc = "unknown"
            except Exception:
                print("Issue processing game file.")
                st_fl = "U"
                regseason_fl = "U"
                playoff_fl = "U"
                game_type = "U"
                game_type_des = "Unknown"
                local_game_time = "Unknown"
                game_id = "Unknown"
                home_team_id = "Unknown"
                away_team_id = "Unknown"
                home_team_lg = "Unknown"
                away_team_lg = "Unknown"
                interleague_fl = "U"
                park_id = "Unknown"
                park_name = "Unknown"
                park_loc = "Unknown"
            retro_game_id = (home_team_id.upper() + str(active_date.year) +
                             str(active_date.strftime('%m')) +
                             str(active_date.strftime('%d')) +
                             str(int(game_number)-1))
            inn_url = g_url+"inning/"
            inning_pattern = 'inning_\d*.xml'
            try:
                for inning in BeautifulSoup(
                    urlopen(inn_url)).find_all('a',
                                               href=re.compile(
                                                   'inning_\d*.xml')):
                    inn_soup = BeautifulSoup(
                        urlopen(inn_url+inning.get_text().strip()), "lxml-xml")
                    inning_number = inn_soup.inning["num"]
                    top_outs = 0
                    bottom_outs = 0
                    if inn_soup.inning.find("top"):
                        for ab in inn_soup.inning.top.find_all("atbat"):
                            pitch_type_seq = ""
                            battedball_cd = ""
                            base1 = "_"
                            base2 = "_"
                            base3 = "_"
                            ball_tally = 0
                            strike_tally = 0
                            base_states = {'___': '0', '1__': '1', '_2_': '2',
                                           '12_': '3', '__3': '4', '1_3': '5',
                                           '_23': '6', '123': '7'}
                            pitch_seq = ""
                            if 'b' in ab.attrs:
                                ball_ct = ab["b"]
                            else:
                                ball_ct = ""
                            if 's' in ab.attrs:
                                strike_ct = ab["s"]
                            else:
                                strike_ct = ""
                            if 'o' in ab.attrs:
                                event_outs_ct = str(int(ab["o"])-top_outs)
                            else:
                                event_outs_ct = ""
                            bat_home_id = 0
                            if 'batter' in ab.attrs:
                                bat_mlbid = ab["batter"]
                            else:
                                bat_mlbid = ""
                            if 'stand' in ab.attrs:
                                bat_hand_cd = ab["stand"]
                            else:
                                bat_hand_cd = ""
                            if 'pitcher' in ab.attrs:
                                pit_mlbid = ab["pitcher"]
                            else:
                                pit_mlbid = ""
                            if 'p_throws' in ab.attrs:
                                pit_hand_cd = ab["p_throws"]
                            else:
                                pit_hand_cd = ""
                            if 'des' in ab.attrs:
                                ab_des = ab["des"]
                            else:
                                ab_des = ""
                            if 'num' in ab.attrs:
                                ab_number = ab["num"]
                            else:
                                ab_number = ""
                            if 'event' in ab.attrs:
                                event_tx = ab["event"]
                            else:
                                event_tx = ""
                            event_cd = ""
                            flyout = ['Flyout', 'Fly Out', 'Sac Fly',
                                      'Sac Fly DP']
                            lineout = ['Lineout', 'Line Out', 'Bunt Lineout']
                            popout = ['Pop out', 'Pop Out', 'Bunt Pop Out']
                            groundout = ['Groundout', 'Ground Out', 'Sac Bunt',
                                         'Bunt Groundout', 'Grounded Into DP']
                            mult_out = ['Double Play', 'Triple Play',
                                        'Sacrifice Bunt D']
                            strikeout = ['Strikeout', 'Strikeout - DP']
                            fielders_choice = ['Fielders Choice Out',
                                               'Fielders Choice']
                            if event_tx in flyout:
                                event_cd = 2
                                battedball_cd = "F"
                            elif event_tx in lineout:
                                event_cd = 2
                                battedball_cd = "L"
                            elif event_tx in popout:
                                event_cd = 2
                                battedball_cd = "P"
                            elif event_tx in groundout:
                                event_cd = 2
                                battedball_cd = "G"
                            elif event_tx == "Forceout":
                                event_cd = 2
                                battedball_cd = ballcode_out(ab_des)
                            elif event_tx in mult_out:
                                event_cd = 2
                                battedball_cd = ballcode_out(ab_des)
                            elif event_tx in strikeout:
                                event_cd = 3
                            elif event_tx == "Walk":
                                event_cd = 14
                            elif event_tx == "Intent Walk":
                                event_cd = 15
                            elif event_tx == "Hit By Pitch":
                                event_cd = 16
                            elif event_tx.lower().count("interference") > 0:
                                event_cd = 17
                            elif event_tx[-5:] == "Error":
                                event_cd = 18
                            elif event_tx in fielders_choice:
                                event_cd = 19
                            elif event_tx == "Single":
                                event_cd = 20
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Double":
                                event_cd = 21
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Triple":
                                event_cd = 22
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Home Run":
                                event_cd = 23
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Runner Out":
                                if ab_des.lower().count("caught stealing") > 0:
                                    event_cd = 6
                                elif ab_des.lower().count("picks off") > 0:
                                    event_cd = 8
                            else:
                                event_cd = 99
                            if ab.find("runner", start="1B"):
                                base1 = "1"
                            if ab.find("runner", start="2B"):
                                base2 = "2"
                            if ab.find("runner", start="3B"):
                                base3 = "3"
                            base_state_tx = base1+base2+base3
                            if base_states[base_state_tx]:
                                start_bases_cd = base_states[base_state_tx]
                            else:
                                start_bases_cd = "9"
                            base1, base2, base3 = "_", "_", "_"
                            if ab.find("runner", end="1B"):
                                base1 = "1"
                            if ab.find("runner", end="2B"):
                                base2 = "2"
                            if ab.find("runner", end="3B"):
                                base3 = "3"
                            base_state_tx = base1+base2+base3
                            if base_states[base_state_tx]:
                                end_bases_cd = base_states[base_state_tx]
                            else:
                                end_bases_cd = "9"
                            for pitch in ab.find_all("pitch"):
                                pa_terminal_fl = "U"
                                comp_ct = 0
                                if 'type' in pitch.attrs:
                                    pitch_res = pitch["type"]
                                    comp_ct += 1
                                else:
                                    pitch_res = ""
                                if 'des' in pitch.attrs:
                                    pitch_des = pitch["des"]
                                    comp_ct += 1
                                else:
                                    pitch_des = ""
                                if pitch_des == "Foul":
                                    pitch_res = "F"
                                if pitch_des == "Called Strike":
                                    pitch_res = "C"
                                if 'id' in pitch.attrs:
                                    pitch_id = pitch["id"]
                                    comp_ct += 1
                                else:
                                    pitch_id = ""
                                pitch_seq += pitch_res
                                if (pitch_res == "X" or
                                    ((pitch_res == "S" or pitch_res == "C") and
                                     event_cd == 3 and strike_tally == 2) or
                                    (ball_tally == 3 and pitch_res == "B" and
                                     (event_cd == 14 or event_cd == 15))):
                                        pa_terminal_fl = "T"
                                else:
                                    pa_terminal_fl = "F"
                                if 'x' in pitch.attrs:
                                    x = pitch["x"]
                                    comp_ct += 1
                                else:
                                    x = ""
                                if 'y' in pitch.attrs:
                                    pitch_y = pitch["y"]
                                    comp_ct += 1
                                else:
                                    pitch_y = ""
                                if 'sv_id' in pitch.attrs:
                                    sv_id = pitch["sv_id"]
                                    comp_ct += 1
                                else:
                                    sv_id = ""
                                if 'start_speed' in pitch.attrs:
                                    start_speed = pitch["start_speed"]
                                    comp_ct += 1
                                else:
                                    start_speed = ""
                                if 'end_speed' in pitch.attrs:
                                    end_speed = pitch["end_speed"]
                                    comp_ct += 1
                                else:
                                    end_speed = ""
                                if 'sz_top' in pitch.attrs:
                                    sz_top = pitch["sz_top"]
                                    comp_ct += 1
                                else:
                                    sz_top = ""
                                if 'sz_bot' in pitch.attrs:
                                    sz_bot = pitch["sz_bot"]
                                    comp_ct += 1
                                else:
                                    sz_bot = ""
                                if 'pfx_x' in pitch.attrs:
                                    pfx_x = pitch["pfx_x"]
                                    comp_ct += 1
                                else:
                                    pfx_x = ""
                                if 'pfx_z' in pitch.attrs:
                                    pfx_z = pitch["pfx_z"]
                                    comp_ct += 1
                                else:
                                    pfx_z = ""
                                if 'px' in pitch.attrs:
                                    px = pitch["px"]
                                    comp_ct += 1
                                else:
                                    px = ""
                                if 'pz' in pitch.attrs:
                                    pz = pitch["pz"]
                                    comp_ct += 1
                                else:
                                    pz = ""
                                if 'x0' in pitch.attrs:
                                    x0 = pitch["x0"]
                                    comp_ct += 1
                                else:
                                    x0 = ""
                                if 'y0' in pitch.attrs:
                                    y0 = pitch["y0"]
                                    comp_ct += 1
                                else:
                                    y0 = ""
                                if 'z0' in pitch.attrs:
                                    z0 = pitch["z0"]
                                    comp_ct += 1
                                else:
                                    z0 = ""
                                if 'vx0' in pitch.attrs:
                                    vx0 = pitch["vx0"]
                                    comp_ct += 1
                                else:
                                    vx0 = ""
                                if 'vy0' in pitch.attrs:
                                    vy0 = pitch["vy0"]
                                    comp_ct += 1
                                else:
                                    vy0 = ""
                                if 'vz0' in pitch.attrs:
                                    vz0 = pitch["vz0"]
                                    comp_ct += 1
                                else:
                                    vz0 = ""
                                if 'ax' in pitch.attrs:
                                    ax = pitch["ax"]
                                    comp_ct += 1
                                else:
                                    ax = ""
                                if 'ay' in pitch.attrs:
                                    ay = pitch["ay"]
                                    comp_ct += 1
                                else:
                                    ay = ""
                                if 'az' in pitch.attrs:
                                    az = pitch["az"]
                                    comp_ct += 1
                                else:
                                    az = ""
                                if 'break_y' in pitch.attrs:
                                    break_y = pitch["break_y"]
                                    comp_ct += 1
                                else:
                                    break_y = ""
                                if 'break_angle' in pitch.attrs:
                                    break_angle = pitch["break_angle"]
                                    comp_ct += 1
                                else:
                                    break_angle = ""
                                if 'break_length' in pitch.attrs:
                                    break_length = pitch["break_length"]
                                    comp_ct += 1
                                else:
                                    break_length = ""
                                if 'pitch_type' in pitch.attrs:
                                    pitch_type = pitch["pitch_type"]
                                    comp_ct += 1
                                else:
                                    pitch_type = ""
                                if pitch_type_seq == "":
                                    pitch_type_seq += pitch_type
                                else:
                                    pitch_type_seq += ("|"+pitch_type)
                                if 'type_confidence' in pitch.attrs:
                                    type_conf = pitch["type_confidence"]
                                    comp_ct += 1
                                else:
                                    type_conf = ""
                                if 'zone' in pitch.attrs:
                                    zone = pitch["zone"]
                                    comp_ct += 1
                                else:
                                    zone = ""
                                if 'spin_dir' in pitch.attrs:
                                    spin_dir = pitch["spin_dir"]
                                    comp_ct += 1
                                else:
                                    spin_dir = ""
                                if 'spin_rate' in pitch.attrs:
                                    spin_rate = pitch["spin_rate"]
                                    comp_ct += 1
                                else:
                                    spin_rate = ""
                                pitch_outfile.write(
                                    str(retro_game_id) + "," +
                                    str(active_date.year) + "," + str(st_fl) +
                                    "," + str(regseason_fl) + "," +
                                    str(playoff_fl) + "," + str(game_type) +
                                    "," + str(game_type_des) + "," +
                                    str(game_id) + "," + str(home_team_id) +
                                    "," + str(home_team_lg) + "," +
                                    str(away_team_id) + "," +
                                    str(away_team_lg) + "," +
                                    str(interleague_fl) + "," +
                                    str(inning_number) + "," +
                                    str(bat_home_id) + "," + str(park_id) +
                                    "," + str(park_name) + ",\"" +
                                    str(park_loc) + "\"," + str(pit_mlbid) +
                                    "," + str(bat_mlbid) + "," +
                                    str(pit_hand_cd) + "," + str(bat_hand_cd) +
                                    "," + str(ball_tally) + "," +
                                    str(strike_tally) + "," + str(top_outs) +
                                    "," + str(pitch_seq) + "," +
                                    str(pa_terminal_fl) + "," + str(event_cd) +
                                    "," + str(start_bases_cd) + "," +
                                    str(end_bases_cd) + "," +
                                    str(event_outs_ct) + "," + str(ab_number) +
                                    "," + str(pitch_res) + ",\"" +
                                    str(pitch_des) + "\"," + str(pitch_id) +
                                    "," + str(x) + "," + str(pitch_y) + "," +
                                    str(start_speed) + "," + str(end_speed) +
                                    "," + str(sz_top) + "," + str(sz_bot) +
                                    "," + str(pfx_x) + "," + str(pfx_z) + "," +
                                    str(px) + "," + str(pz) + "," + str(x0) +
                                    "," + str(y0) + "," + str(z0) + "," +
                                    str(vx0) + "," + str(vy0) + "," +
                                    str(vz0) + "," + str(ax) + "," + str(ay) +
                                    "," + str(az) + "," + str(break_y) +
                                    "," + str(break_angle) + "," +
                                    str(break_length) + "," + str(pitch_type) +
                                    "," + str(pitch_type_seq) + "," +
                                    str(type_conf) + "," + str(zone) + "," +
                                    str(spin_dir) + "," + str(spin_rate) +
                                    "," + str(sv_id) + "\n")
                                if pitch_res == "B":
                                    if ball_tally < 4:
                                        ball_tally += 1
                                elif pitch_res in ['S', 'C', 'X']:
                                    if strike_tally < 3:
                                        strike_tally += 1
                                elif pitch_res == "F":
                                    if strike_tally < 2:
                                        strike_tally += 1
                            atbat_outfile.write(
                                str(retro_game_id) + "," +
                                str(active_date.year) + "," +
                                str(active_date.month) + "," +
                                str(active_date.day) + "," + str(st_fl) +
                                "," + str(regseason_fl) + "," +
                                str(playoff_fl) + "," + str(game_type) + "," +
                                str(game_type_des) + "," +
                                str(local_game_time) + "," + str(game_id) +
                                "," + str(home_team_id) + "," +
                                str(away_team_id) + "," + str(home_team_lg) +
                                "," + str(away_team_lg) + "," +
                                str(interleague_fl) + "," + str(park_id) +
                                "," + str(park_name) + ",\"" + str(park_loc) +
                                "\"," + str(inning_number) + "," +
                                str(bat_home_id) + "," + str(top_outs) + "," +
                                str(ab_number) + "," + str(pit_mlbid) + "," +
                                str(pit_hand_cd) + "," + str(bat_mlbid) + "," +
                                str(bat_hand_cd) + "," + str(ball_ct) + "," +
                                str(strike_ct) + "," + str(pitch_seq) + "," +
                                str(pitch_type_seq) + "," +
                                str(event_outs_ct) + ",\"" + str(ab_des) +
                                "\"," + str(event_tx) + "," + str(event_cd) +
                                "," + str(battedball_cd) + "," +
                                str(start_bases_cd) + "," + str(end_bases_cd) +
                                "\n")
                            top_outs += int(event_outs_ct)
                    if inn_soup.inning.find("bottom"):
                        for ab in inn_soup.inning.bottom.find_all("atbat"):
                            pitch_type_seq = ""
                            battedball_cd = ""
                            base1 = "_"
                            base2 = "_"
                            base3 = "_"
                            ball_tally = 0
                            strike_tally = 0
                            base_states = {'___': '0', '1__': '1', '_2_': '2',
                                           '12_': '3', '__3': '4', '1_3': '5',
                                           '_23': '6', '123': '7'}
                            pitch_seq = ""
                            if 'b' in ab.attrs:
                                ball_ct = ab["b"]
                            else:
                                ball_ct = ""
                            if 's' in ab.attrs:
                                strike_ct = ab["s"]
                            else:
                                strike_ct = ""
                            if 'o' in ab.attrs:
                                event_outs_ct = str(int(ab["o"])-bottom_outs)
                            else:
                                event_outs_ct = ""
                            bat_home_id = 1
                            if 'batter' in ab.attrs:
                                bat_mlbid = ab["batter"]
                            else:
                                bat_mlbid = ""
                            if 'stand' in ab.attrs:
                                bat_hand_cd = ab["stand"]
                            else:
                                bat_hand_cd = ""
                            if 'pitcher' in ab.attrs:
                                pit_mlbid = ab["pitcher"]
                            else:
                                pit_mlbid = ""
                            if 'p_throws' in ab.attrs:
                                pit_hand_cd = ab["p_throws"]
                            else:
                                pit_hand_cd = ""
                            if 'des' in ab.attrs:
                                ab_des = ab["des"]
                            else:
                                ab_des = ""
                            if 'num' in ab.attrs:
                                ab_number = ab["num"]
                            else:
                                ab_number = ""
                            if 'event' in ab.attrs:
                                event_tx = ab["event"]
                            else:
                                event_tx = ""
                            flyout = ['Flyout', 'Fly Out', 'Sac Fly',
                                      'Sac Fly DP']
                            lineout = ['Lineout', 'Line Out', 'Bunt Lineout']
                            popout = ['Pop out', 'Pop Out', 'Bunt Pop Out']
                            groundout = ['Groundout', 'Ground Out', 'Sac Bunt',
                                         'Bunt Groundout', 'Grounded Into DP']
                            mult_out = ['Double Play', 'Triple Play',
                                        'Sacrifice Bunt D']
                            strikeout = ['Strikeout', 'Strikeout - DP']
                            fielders_choice = ['Fielders Choice Out',
                                               'Fielders Choice']
                            if event_tx in flyout:
                                event_cd = 2
                                battedball_cd = "F"
                            elif event_tx in lineout:
                                event_cd = 2
                                battedball_cd = "L"
                            elif event_tx in popout:
                                event_cd = 2
                                battedball_cd = "P"
                            elif event_tx in groundout:
                                event_cd = 2
                                battedball_cd = "G"
                            elif event_tx in ['Forceout', 'Force Out']:
                                event_cd = 2
                                battedball_cd = ballcode_out(ab_des)
                            elif event_tx in mult_out:
                                event_cd = 2
                                battedball_cd = ballcode_out(ab_des)
                            elif event_tx in strikeout:
                                event_cd = 3
                            elif event_tx == "Walk":
                                event_cd = 14
                            elif event_tx == "Intent Walk":
                                event_cd = 15
                            elif event_tx == "Hit By Pitch":
                                event_cd = 16
                            elif event_tx.lower().count("interference") > 0:
                                event_cd = 17
                            elif event_tx[-5:] == "Error":
                                event_cd = 18
                            elif event_tx in fielders_choice:
                                event_cd = 19
                            elif event_tx == "Single":
                                event_cd = 20
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Double":
                                event_cd = 21
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Triple":
                                event_cd = 22
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Home Run":
                                event_cd = 23
                                battedball_cd = ballcode_hit(ab_des)
                            elif event_tx == "Runner Out":
                                if ab_des.lower().count("caught stealing") > 0:
                                    event_cd = 6
                                elif ab_des.lower().count("picks off") > 0:
                                    event_cd = 8
                            else:
                                event_cd = 99
                            if ab.find("runner", start="1B"):
                                base1 = "1"
                            if ab.find("runner", start="2B"):
                                base2 = "2"
                            if ab.find("runner", start="3B"):
                                base3 = "3"
                            base_state_tx = base1+base2+base3
                            if base_states[base_state_tx]:
                                start_bases_cd = base_states[base_state_tx]
                            else:
                                start_bases_cd = "9"
                            base1 = "_"
                            base2 = "_"
                            base3 = "_"
                            if ab.find("runner", end="1B"):
                                base1 = "1"
                            if ab.find("runner", end="2B"):
                                base2 = "2"
                            if ab.find("runner", end="3B"):
                                base3 = "3"
                            base_state_tx = base1+base2+base3
                            if base_states[base_state_tx]:
                                end_bases_cd = base_states[base_state_tx]
                            else:
                                end_bases_cd = "9"
                            for pitch in ab.find_all("pitch"):
                                pa_terminal_fl = "U"
                                comp_ct = 0
                                if 'type' in pitch.attrs:
                                    pitch_res = pitch["type"]
                                    comp_ct += 1
                                else:
                                    pitch_res = ""
                                if 'des' in pitch.attrs:
                                    pitch_des = pitch["des"]
                                    comp_ct += 1
                                else:
                                    pitch_des = ""
                                if pitch_des == "Foul":
                                    pitch_res = "F"
                                if pitch_des == "Called Strike":
                                    pitch_res = "C"
                                if 'id' in pitch.attrs:
                                    pitch_id = pitch["id"]
                                    comp_ct += 1
                                else:
                                    pitch_id = ""
                                pitch_seq += pitch_res
                                if (pitch_res == "X" or
                                    ((pitch_res == "S" or pitch_res == "C") and
                                     event_cd == 3 and strike_tally == 2) or
                                    (ball_tally == 3 and pitch_res == "B" and
                                     (event_cd == 14 or event_cd == 15))):
                                        pa_terminal_fl = "T"
                                else:
                                    pa_terminal_fl = "F"
                                if 'x' in pitch.attrs:
                                    x = pitch["x"]
                                    comp_ct += 1
                                else:
                                    x = ""
                                if 'y' in pitch.attrs:
                                    pitch_y = pitch["y"]
                                    comp_ct += 1
                                else:
                                    pitch_y = ""
                                if 'sv_id' in pitch.attrs:
                                    sv_id = pitch["sv_id"]
                                    comp_ct += 1
                                else:
                                    sv_id = ""
                                if 'start_speed' in pitch.attrs:
                                    start_speed = pitch["start_speed"]
                                    comp_ct += 1
                                else:
                                    start_speed = ""
                                if 'end_speed' in pitch.attrs:
                                    end_speed = pitch["end_speed"]
                                    comp_ct += 1
                                else:
                                    end_speed = ""
                                if 'sz_top' in pitch.attrs:
                                    sz_top = pitch["sz_top"]
                                    comp_ct += 1
                                else:
                                    sz_top = ""
                                if 'sz_bot' in pitch.attrs:
                                    sz_bot = pitch["sz_bot"]
                                    comp_ct += 1
                                else:
                                    sz_bot = ""
                                if 'pfx_x' in pitch.attrs:
                                    pfx_x = pitch["pfx_x"]
                                    comp_ct += 1
                                else:
                                    pfx_x = ""
                                if 'pfx_z' in pitch.attrs:
                                    pfx_z = pitch["pfx_z"]
                                    comp_ct += 1
                                else:
                                    pfx_z = ""
                                if 'px' in pitch.attrs:
                                    px = pitch["px"]
                                    comp_ct += 1
                                else:
                                    px = ""
                                if 'pz' in pitch.attrs:
                                    pz = pitch["pz"]
                                    comp_ct += 1
                                else:
                                    pz = ""
                                if 'x0' in pitch.attrs:
                                    x0 = pitch["x0"]
                                    comp_ct += 1
                                else:
                                    x0 = ""
                                if 'y0' in pitch.attrs:
                                    y0 = pitch["y0"]
                                    comp_ct += 1
                                else:
                                    y0 = ""
                                if 'z0' in pitch.attrs:
                                    z0 = pitch["z0"]
                                    comp_ct += 1
                                else:
                                    z0 = ""
                                if 'vx0' in pitch.attrs:
                                    vx0 = pitch["vx0"]
                                    comp_ct += 1
                                else:
                                    vx0 = ""
                                if 'vy0' in pitch.attrs:
                                    vy0 = pitch["vy0"]
                                    comp_ct += 1
                                else:
                                    vy0 = ""
                                if 'vz0' in pitch.attrs:
                                    vz0 = pitch["vz0"]
                                    comp_ct += 1
                                else:
                                    vz0 = ""
                                if 'ax' in pitch.attrs:
                                    ax = pitch["ax"]
                                    comp_ct += 1
                                else:
                                    ax = ""
                                if 'ay' in pitch.attrs:
                                    ay = pitch["ay"]
                                    comp_ct += 1
                                else:
                                    ay = ""
                                if 'az' in pitch.attrs:
                                    az = pitch["az"]
                                    comp_ct += 1
                                else:
                                    az = ""
                                if 'break_y' in pitch.attrs:
                                    break_y = pitch["break_y"]
                                    comp_ct += 1
                                else:
                                    break_y = ""
                                if 'break_angle' in pitch.attrs:
                                    break_angle = pitch["break_angle"]
                                    comp_ct += 1
                                else:
                                    break_angle = ""
                                if 'break_length' in pitch.attrs:
                                    break_length = pitch["break_length"]
                                    comp_ct += 1
                                else:
                                    break_length = ""
                                if 'pitch_type' in pitch.attrs:
                                    pitch_type = pitch["pitch_type"]
                                    comp_ct += 1
                                else:
                                    pitch_type = ""
                                if pitch_type_seq == "":
                                    pitch_type_seq += pitch_type
                                else:
                                    pitch_type_seq += ("|"+pitch_type)
                                if 'type_confidence' in pitch.attrs:
                                    type_conf = pitch["type_confidence"]
                                    comp_ct += 1
                                else:
                                    type_conf = ""
                                if 'zone' in pitch.attrs:
                                    zone = pitch["zone"]
                                    comp_ct += 1
                                else:
                                    zone = ""
                                if 'spin_dir' in pitch.attrs:
                                    spin_dir = pitch["spin_dir"]
                                    comp_ct += 1
                                else:
                                    spin_dir = ""
                                if 'spin_rate' in pitch.attrs:
                                    spin_rate = pitch["spin_rate"]
                                    comp_ct += 1
                                else:
                                    spin_rate = ""
                                pitch_outfile.write(
                                    str(retro_game_id) + "," +
                                    str(active_date.year) + "," + str(st_fl) +
                                    "," + str(regseason_fl) + "," +
                                    str(playoff_fl) + "," + str(game_type) +
                                    "," + str(game_type_des) + "," +
                                    str(game_id) + "," + str(home_team_id) +
                                    "," + str(home_team_lg) + "," +
                                    str(away_team_id) + "," +
                                    str(away_team_lg) + "," +
                                    str(interleague_fl) + "," +
                                    str(inning_number) + "," +
                                    str(bat_home_id) + "," + str(park_id) +
                                    "," + str(park_name) + ",\"" +
                                    str(park_loc) + "\"," + str(pit_mlbid) +
                                    "," + str(bat_mlbid) + "," +
                                    str(pit_hand_cd) + "," + str(bat_hand_cd) +
                                    "," + str(ball_tally) + "," +
                                    str(strike_tally) + "," + str(top_outs) +
                                    "," + str(pitch_seq) + "," +
                                    str(pa_terminal_fl) + "," + str(event_cd) +
                                    "," + str(start_bases_cd) + "," +
                                    str(end_bases_cd) + "," +
                                    str(event_outs_ct) + "," + str(ab_number) +
                                    "," + str(pitch_res) + ",\"" +
                                    str(pitch_des) + "\"," + str(pitch_id) +
                                    "," + str(x) + "," + str(pitch_y) + "," +
                                    str(start_speed) + "," + str(end_speed) +
                                    "," + str(sz_top) + "," + str(sz_bot) +
                                    "," + str(pfx_x) + "," + str(pfx_z) + "," +
                                    str(px) + "," + str(pz) + "," + str(x0) +
                                    "," + str(y0) + "," + str(z0) + "," +
                                    str(vx0) + "," + str(vy0) + "," +
                                    str(vz0) + "," + str(ax) + "," + str(ay) +
                                    "," + str(az) + "," + str(break_y) +
                                    "," + str(break_angle) + "," +
                                    str(break_length) + "," + str(pitch_type) +
                                    "," + str(pitch_type_seq) + "," +
                                    str(type_conf) + "," + str(zone) + "," +
                                    str(spin_dir) + "," + str(spin_rate) +
                                    "," + str(sv_id) + "\n")
                                if pitch_res == "B":
                                    if ball_tally < 4:
                                        ball_tally += 1
                                elif pitch_res in ['S', 'C', 'X']:
                                    if strike_tally < 3:
                                        strike_tally += 1
                                elif pitch_res == "F":
                                    if strike_tally < 2:
                                        strike_tally += 1
                            atbat_outfile.write(
                                str(retro_game_id) + "," +
                                str(active_date.year) + "," +
                                str(active_date.month) + "," +
                                str(active_date.day) + "," + str(st_fl) +
                                "," + str(regseason_fl) + "," +
                                str(playoff_fl) + "," + str(game_type) + "," +
                                str(game_type_des) + "," +
                                str(local_game_time) + "," + str(game_id) +
                                "," + str(home_team_id) + "," +
                                str(away_team_id) + "," + str(home_team_lg) +
                                "," + str(away_team_lg) + "," +
                                str(interleague_fl) + "," + str(park_id) +
                                "," + str(park_name) + ",\"" + str(park_loc) +
                                "\"," + str(inning_number) + "," +
                                str(bat_home_id) + "," + str(top_outs) + "," +
                                str(ab_number) + "," + str(pit_mlbid) + "," +
                                str(pit_hand_cd) + "," + str(bat_mlbid) + "," +
                                str(bat_hand_cd) + "," + str(ball_ct) + "," +
                                str(strike_ct) + "," + str(pitch_seq) + "," +
                                str(pitch_type_seq) + "," +
                                str(event_outs_ct) + ",\"" + str(ab_des) +
                                "\"," + str(event_tx) + "," + str(event_cd) +
                                "," + str(battedball_cd) + "," +
                                str(start_bases_cd) + "," + str(end_bases_cd) +
                                "\n")
                            bottom_outs += int(event_outs_ct)
            except HTTPError:
                print("Error processing inning data.")
                continue
    prior_d_url = d_url
