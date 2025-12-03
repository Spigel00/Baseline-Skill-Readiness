#Reading the file

path='data/sample.txt'
file = open(path, "r")
content = file.read()
print("Content of the file:")
print(content)


#Counting the number of lines in the file
lines = content.count("\n")
print("\nNumber of lines in the file:")
print(lines)

#Printing the 5 largest word in the file
words = content.split()
words.sort(key=len, reverse=True)
print("\n5 largest words in the file:")
for word in words[:5]:
    print("\n",word)

#Counting the headings in the file
count = 0
for title in words:
    if title.endswith(":"):
        count += 1
print("\nNumber of headings in the file:")
print("\n",count)

# Finding lines mentioning figures or tables
lines = content.split("\n")
print("\nLines mentioning figures or tables:")
for line in lines:
    if "Figure" in line or "Table" in line:
        print("\n",line)

#Using regex to extract the references
import re
references = re.findall(r'(Figure|Table)\s*\d+', content)
figure=0
table=0
for reference in references:
    if "Figure" in reference:
        figure += 1
    elif "Table" in reference:
        table += 1
print("\nReferences:")
print("\n",references)

#Making metadata and saving as JSON file
metadata={
    "number_of_lines":lines,
    "number_of_words":words,
    "number_of_figure_mentions":figure,
    "number_of_table_mentions":table
}
import json
import os
os.makedirs('outputs', exist_ok=True)
with open('outputs/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=4)
print("\nMetadata saved to outputs/metadata.json")

#Renaming files 
import shutil
shutil.copy('data/sample.txt', 'outputs/sample_copy.txt')
print("\nSample.txt copied to outputs/sample_copy.txt")

#Making manifest.csv
import pandas as pd
manifest=pd.DataFrame({
    "file_name":["sample.txt","sample_copy.txt"],
    "headings":5,
    "tables":2,
    "figures":2,
    "lines":14
})
manifest.to_csv('outputs/manifest.csv', index=False)
print("\nManifest.csv saved to outputs/manifest.csv")

