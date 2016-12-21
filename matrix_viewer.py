#!/cygdrive/c/Python35/python

import csv
import getopt
import sys

prefix_colors = {"CS": "FFFF47",
                 "CENE": "B5D086",
                 "EGR": "A28DBC",
                 "CM": "FACBA3",
                 "EE": "7FC2D5",
                 "ME": "B8B183"}

lab_dept = {"069-118": "EGR",
            "069-119": "EGR",
            "069-106": "CS",
            "069-111": "ME",
            "069-116": "CENE",
            "069-234": "EE",
            "069-245": "CENE",
            "069-317": "CENE"}

standard_times = ["TR8:00",
                  "TR9:35",
                  "TR11:10",
                  "TR12:45",
                  "TR14:20",
                  "TR16:00",
                  "TR17:30",
                  "MWF8:00",
                  "MWF9:10",
                  "MWF10:20",
                  "MWF11:30",
                  "MWF12:40",
                  "MWF14:20",
                  "MWF16:00",
                  "MWF17:30",
                  "MWF18:45"]

rooms = {}
times = {}
room_names = {}
dupes = {}

try:
    opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "output="])
except getopt.GetoptError as err:
    print("Bad args")
    sys.exit(2)

facility = args[0] # e.g., 069
pattern = args[1] # e.g., MWF TR
if facility == "TBD":
    filters = args[2].split(":")

num_rows = 0
#with open('ScheduleOfClassesSample.csv', 'r') as csvfile:
with open('solution.csv', 'r') as csvfile:
    classreader = csv.DictReader(csvfile)
    for row in classreader:
        num_rows += 1
        if "cancel" in row["Status"].lower():
            continue
        
#        print("DBG[1]: facility ID=", row["Facility ID"])
        if row["Facility ID"].startswith(facility + "-") or (facility == "TBD" and row["Facility ID"].strip() == ""):
#            print("DBG  dbg[1] passing...")
            pass
        else:
#            print("DBG  dbg[1] continuing...")
            continue

        if facility == "TBD":
            row["Facility ID"] = "TBD-TBD"

            skip = True
#            print("DBG   skip is true")
            for filter in filters:
                if row["Class Subject + Nbr"].startswith(filter + " "):
                    skip = False
            if skip:
                continue

#        print("DBG: checkpoint.. facility=", facility)
#        print("DBG   start time:", row["Start Time"])
#        print("DBG   end time:", row["End Time"])
        if row["Start Time"].strip() == "":
            row["Start Time"] = "TBD TBD:TBD:TBD"

        if row["End Time"].strip() == "":
            row["End Time"] = "TBD TBD:TBD:TBD"

        # Create an empty room entry if needed
        if row["Facility ID"] not in rooms:
            rooms[row["Facility ID"]] = {}

        room_names[row["Facility ID"]] = True

        # Load the current room
        room = rooms[row["Facility ID"]]

        # Create a string that describes when the class meets
        meetString = ""
        meetings = 0
        for day in [("Sunday", "U"), ("Monday", "M"), ("Tuesday", "T"), ("Wednesday", "W"), 
                    ("Thursday", "R"), ("Friday", "F"), ("Saturday", "S")]:
            if row["Meets on " + day[0]] == "Y":
                meetString += day[1]
                meetings += 1
        if meetString == "": meetString = "TBD"

        ### MR
#        print("DBG: currently right here, 'index out of range' error")
#        start = row["Start Time"].split(" ")[1].split(":")
        start = row["Start Time"].split(" ")[0].split(":")
        start = start[0] + ":" + start[1]
#        end = row["End Time"].split(" ")[1].split(":")
        end = row["End Time"].split(" ")[0].split(":")
        end = end[0] + ":" + end[1]

        uid = row["Class Nbr"] + meetString + start
        if uid in dupes:
            continue
        dupes[uid] = True

        # Shorten the instructor string
        instructorString = row["Instructor Name"].split(",")[0].replace("PHD", "").strip()
        if instructorString == "": instructorString = "TBD"

        # Create a unique color based on the course prefix
        prefix = row["Class Subject + Nbr"].split(" ")[0]
        try:
            color = prefix_colors[prefix]
        except:
            color = "D0D0D0"

        section = row["Primary Instruction Section"]
        if section.startswith("0"):
            section = str(int(section))

        # hour = int(start.split(":")[0])

        if "M" in meetString or "W" in meetString or "F" in meetString:
            start_prefix = "MWF"
        elif "T" in meetString or "R" in meetString:
            start_prefix = "TR"
        else:
            start_prefix = meetString
            print("ODD MEET TIME: " + meetString)

        # Kludge around the 12:40 vs 12:45 start time of Friday classes
        room_key = start_prefix + start
        if room_key == "MWF12:45": room_key = "MWF12:40"

        # Kludge Willie..
        if room_key == "MWF12:50": room_key = "MWF12:40"

        # Kludge the late start class time..
#        if room_key == "MWF08:30": room_key = "MWF08:00"

        best_key = False
        odd_time_string = ""
        if room_key not in standard_times:
            (hour, minute) = start.split(":")
            if hour == "TBD": continue
            hour = int(hour)
            minute = int(minute)
            for candidate_key in standard_times:
                if not candidate_key.startswith(start_prefix):
                    continue
                (c_hour, c_minute) = candidate_key.split(start_prefix)[1].split(":")
                c_hour = int(c_hour)
                c_minute = int(c_minute)
                if c_hour < hour or (c_hour == hour and c_minute < minute):
                    best_key = candidate_key
            if best_key:
                room_key = best_key
                odd_time_string = "<br /><span style=\"background-color:#ff0000\">ODD TIME</span>"

        # Format the content
        content = "<span style=\"background-color:#{}\"><span class=\"nowrap\"><b>{}-{}</b> {} #{}</span><br>\n<span class=\"nowrap\">{} (Cap {})</span><br><span class=\"nowrap\">{} - {}</span>{}</span>\n".format(
            color,
            row["Class Subject + Nbr"],
            section,
            meetString,
            row["Class Nbr"],
            instructorString,
            row["Enrollment Cap"], start, end, odd_time_string)

        if room_key not in room:
            room[room_key] = ["", "", ""]

        times[room_key] = True

        if room[room_key][0] != "":
            room[room_key][0] += "<hr>"
        room[room_key][0] += content
        room[room_key][1] = color
        room[room_key][2] += meetString

#print("DBG: num_rows =", num_rows)
times = list(times.keys())
times.sort()

room_names = list(room_names.keys())
room_names.sort()

with open("matrix_" + facility + "_" + pattern + ".html", 'w') as fh:
    fh.write("""
<html>
<head>
<style type="text/css">
table.gridtable {
font-family: verdana,arial,sans-serif;
font-size:11px;
color:#333333;
border-width: 1px;
border-color: #666666;
border-collapse: collapse;
}
table.gridtable th {
border-width: 1px;
padding: 2px;
border-style: solid;
border-color: #666666;
}
table.gridtable td {
border-width: 1px;
padding: 2px;
border-style: solid;
border-color: #666666;
}
.nowrap { white-space: nowrap; }
</style>
</head>
<body>

""")

    fh.write("<table class=\"gridtable\">")
    fh.write("<tr><td>&nbsp;</td>")

    for time in times:
        if pattern not in time: continue
        fh.write("<td valign='top'><b>{}</b></td>".format(
                time
                .replace("F", "F<br>")
                .replace("R", "R<br>")))
    fh.write("</tr>\n")
    for room_name in room_names:
        room = rooms[room_name]
        room_name_short = room_name.split("-")[1]
        try:
            room_color = prefix_colors[lab_dept[room_name]]
        except:
            room_color = "D0D0D0"
        fh.write("<tr><td bgcolor='#{}' valign='top'><b>{}</b></td>\n".format(
                room_color,
                room_name_short))

        for time in times:
            if pattern not in time: continue
            try:
                slot = room[time]
            except:
                slot = ["", "ffffff", ""]

            for p in pattern:
                if p not in slot[2]:
                    slot[1] = "ffffff"

            fh.write("<td valign='top' bgcolor='#{}'>{}</td>".format(slot[1], slot[0]))
        fh.write("</tr>\n")
    fh.write("</table><p></p>")
    fh.write("</body></html>")
