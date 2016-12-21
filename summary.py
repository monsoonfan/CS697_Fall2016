#!/usr/local/bin/python3

import csv
import getopt
import sys

buildings = {}
dupes = {}
meeting_issues = []
consent_issues = []
variable_issues = []

#with open('ScheduleOfClassesSample.csv', 'r') as csvfile:
with open('solution.csv', 'r') as csvfile:
    classreader = csv.DictReader(csvfile)
    for row in classreader:

        if "Cancel" in row["Status"]:
            continue
        if "Tentative" in row["Status"]:
            continue

        if (row["Class Subject + Nbr"].startswith("CS ") or
            row["Class Subject + Nbr"].startswith("EE ")):
            pass
        else:
            continue

        if row["Class Nbr"] in dupes:
            continue
        dupes[row["Class Nbr"]] = True

        number = row["Class Subject + Nbr"].split(" ")[1]
        if number == "699" or number == "485" or number == "497":
            continue

        building = row["Facility ID"].split("-")[0]

        if building not in buildings:
            buildings[building] = []

        rooms = buildings[building]
        rooms.append(row["Class Subject + Nbr"] + " " + row["Class Nbr"])

        meetings = 0
        for day in [("Sunday", "U"), ("Monday", "M"), ("Tuesday", "T"), ("Wednesday", "W"), 
                    ("Thursday", "R"), ("Friday", "F"), ("Saturday", "S")]:
            if row["Meets on " + day[0]] == "Y":
                meetings += 1

        regular_class = not("408" in row["Class Subject + Nbr"] or 
                         "485" in row["Class Subject + Nbr"] or 
                         "497" in row["Class Subject + Nbr"] or 
                         "685" in row["Class Subject + Nbr"] or             
                         "697" in row["Class Subject + Nbr"] or 
                         "699" in row["Class Subject + Nbr"] or
                         "Online" in row["Campus"])

        if int(row["Maximum Units"]) != int(row["Minimum Units"]) and (regular_class or ("Online" in row["Campus"])):
            variable_issues.append("{} ({}): Unexpected variable number of units from {} to {}".format(
                    row["Class Subject + Nbr"],
                    row["Class Nbr"],
                    int(row["Minimum Units"]),
                    int(row["Maximum Units"])))

        if row["Component Cd"].strip() == "LEC":
            if row["Start Time"].strip() != "" and row["End Time"].strip() != "":
                (end_h, end_m) = row["End Time"].strip().split(":")
                (start_h, start_m) = row["Start Time"].strip().split(":")
                delta_h = int(end_h) - int(start_h)
                delta_m = int(end_m) - int(start_m)
                total_time = (delta_h * 60 + delta_m) * meetings
                if total_time != 50 * int(row["Maximum Units"]):
                    meeting_issues.append("{} ({}): Expected {} minutes but found {} minutes".format(
                            row["Class Subject + Nbr"],
                            row["Class Nbr"],
                            int(row["Maximum Units"]) * 50,
                            total_time))
                    print(delta_h, delta_m, meetings, row["Class Subject + Nbr"])

        if meetings == 0 and regular_class:
            meeting_issues.append("{} ({}): has no meeting days.".format(
                    row["Class Subject + Nbr"],
                    row["Class Nbr"]))

        if row["Start Time"].strip() == "" and regular_class:
            meeting_issues.append("{} ({}): has no Start Time.".format(
                    row["Class Subject + Nbr"],
                    row["Class Nbr"]))

        if row["End Time"].strip() == "" and regular_class:
            meeting_issues.append("{} ({}): has no End Time.".format(
                    row["Class Subject + Nbr"],
                    row["Class Nbr"]))

        if regular_class or "Online" in row["Campus"]:
            if row["Consent Required"] != "N":
                consent_issues.append("{} ({}): Expected consent 'N' but found consent '{}'.".format(
                        row["Class Subject + Nbr"],
                        row["Class Nbr"],
                        row["Consent Required"]))
        else:
            if row["Consent Required"] != "I":
                consent_issues.append("{} ({}): Expected consent 'I' but found consent '{}'.".format(
                        row["Class Subject + Nbr"],
                        row["Class Nbr"],
                        row["Consent Required"]))

print("# Building summary")
for b in buildings.keys():
    buildings[b].sort()
    for c in buildings[b]:
        print("* {}: {}".format(b, c))
print("")

print("# Meeting time issues")
for issue in meeting_issues:
    print("* " + issue)
if len(meeting_issues) == 0:
    print("* None")
print("")

print("# Variable unit issues")
for issue in variable_issues:
    print("* " + issue)
if len(variable_issues) == 0:
    print("* None")
print("")

print("# Consent issues")
for issue in consent_issues:
    print("* " + issue)
print("")
