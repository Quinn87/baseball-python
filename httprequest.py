import requests
import csv
#from io import StringIO

# URL with placeholders for dates and batter ID
url = 'https://baseballsavant.mlb.com/statcast_search/csv?hfPT=&hfAB=&hfGT=R%7C&hfPR=&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2025%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2025-03-31&game_date_lt=2025-05-07&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc'


# Make the GET request
response = requests.get(url)
#csv_data = StringIO(response.text)

reader = csv.reader(response.text.splitlines())

file = open("data.csv", "a")

writer = csv.writer(file)

for row in reader:
    writer.writerow([row])




# Check if the request was successful
# if response.status_code == 200:
#     # Parse the CSV response
#     csv_data = StringIO(response.text)
#     reader = csv.reader(csv_data)
    
#     # Print each row of the CSV
#     for row in reader:
#         print(row)
# else:
#     print("Failed to fetch data. Status code:", response.status_code)