from pathlib import Path
import os,json

file_list = list(Path("C:/Users/sarim/OneDrive/Desktop/project2/transistordatabase/transistordatabase/tdb_example_downloaded").glob("*.json"))
#print(file_list)
for i in file_list:
    print(type(Path(i).stem))



""" path_to_json = "C:/Users/sarim/OneDrive/Desktop/project2/transistordatabase/transistordatabase/tdb_example_downloaded/"

for file_name in [file for file in os.listdir(path_to_json) if file.endswith('.json')]:
  with open(path_to_json + file_name) as json_file:
    print(json_file) """