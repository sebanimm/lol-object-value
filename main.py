import requests
import pandas as pd

API_KEY = "RGAPI-b9a15cb5-9306-4214-b9ac-cee804eb3178"
REGION = "kr"

유충먹은경우 = {i: [] for i in range(1, 7)}
용먹은경우 = {i: [] for i in range(1, 7)}


def get_master_plus_summoners():
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["entries"]


summoners = get_master_plus_summoners()


def get_puuid(summoner_id):
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["puuid"]


def get_match_ids(puuid, start=0, count=5):
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}&type=ranked&api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()


def get_match_details(match_id):
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()


def collect_match_data(summoners, num_summoners=5, num_matches=5):
    all_matches = []

    for summoner in summoners[:num_summoners]:
        summoner_id = summoner["summonerId"]
        puuid = get_puuid(summoner_id)

        if not puuid:
            continue

        match_ids = get_match_ids(puuid, num_matches)

        for match_id in match_ids:
            match_details = get_match_details(match_id)

            if not match_details or match_details["info"]["gameMode"] == "CHERRY":
                continue

            all_matches.append(match_details)

    return all_matches


match_details_list = collect_match_data(summoners, 10, 10)
count = 0

for match_detail in match_details_list:
    for team in match_detail["info"]["teams"]:
        유충 = team["objectives"]["horde"]

        if 유충["first"]:
            유충먹은경우[유충["kills"]].append(team)

        용 = team["objectives"]["dragon"]

        if 용["first"]:
            용먹은경우[용["kills"]].append(team)

        count += 1


horde_data = []
for kills, teams in 유충먹은경우.items():
    for team in teams:
        horde_data.append(
            {
                "kills": kills,
                "teamId": team["teamId"],
                "win": team["win"],
                "first": team["objectives"]["horde"]["first"],
            }
        )

dragon_data = []
for kills, teams in 용먹은경우.items():
    for team in teams:
        dragon_data.append(
            {
                "kills": kills,
                "teamId": team["teamId"],
                "win": team["win"],
                "first": team["objectives"]["dragon"]["first"],
            }
        )

df_horde = pd.DataFrame(horde_data)
df_dragon = pd.DataFrame(dragon_data)

# Filter data for specific conditions
df_horde_filtered = df_horde[df_horde["kills"].isin([4, 5, 6])]
df_dragon_filtered = df_dragon[
    df_dragon["kills"] > 0
]  # To capture teams that killed at least one dragon

# Calculate win rate for horde kills (4, 5, 6)
horde_win_rate = df_horde_filtered.groupby("kills")["win"].mean()

# Calculate win rate for first dragon kill
first_dragon_win_rate = df_dragon_filtered.groupby("kills")["win"].mean().get(1, 0)

# Calculate win rate for second dragon kill
second_dragon_win_rate = df_dragon_filtered.groupby("kills")["win"].mean().get(2, 0)

# Calculate win rate for first horde kill
first_horde_win_rate = df_horde[df_horde["first"] == True]["win"].mean()

print("유충을 먼저 먹은 경우 승률: ", first_horde_win_rate)
print("유충을 4개 먹은 경우 승률: ", horde_win_rate.get(4, 0))
print("유충을 5개 먹은 경우 승률: ", horde_win_rate.get(5, 0))
print("유충을 6개 먹은 경우 승률: ", horde_win_rate.get(6, 0))
print("첫번째 용을 먹은 경우 승률: ", first_dragon_win_rate)
print("두번째 용을 먹은 경우 승률: ", second_dragon_win_rate)
