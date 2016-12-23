#######################################################################
# genetic_scheduler.py
#
# Script to output genetically optimized class schedules in CSV format
#
# Authors/Contributors:
# rmr5
# jdp85
#
# Date:
# November - December 2016
#
# Revisions:
#
# Github:
# https://github.com/monsoonfan/CS697_Fall2016
#
# Issues:
# - Online classes have no room, now to deal with
# - T dict assumes all rooms are available for all time slots, might need
#   a mechanism to block out rooms at certain days/times
# - EE 188 gets capacity of 90 from Sample, but try to assign to 069-224
# - need to kill solutions where time slots don't match minimum/maximum units,
#   and perhaps add some preference for standard time slots?
# - For new instructors not in the sample, have to add their info into
#   InstructorConstraints.csv.
# - Speed issues, can be more efficient during random_solution_generation,
#   some things are happening redundantly.
#
# Questions:
# - strip() not working, and why whitespace in the first place
# - instructor workload/days taught: if we add this to fitness, then I
#   think the program will simply take away courses to teach unless all of
#   the instructor/course assignments are made. Are they pretty much always
#   going to be made by constraint?
# - Do we have fixed rooms/schedules - labs, etc where the place/time fixed?
# - Or how about where the room is blacked out?
# - Presentation of "Top solution preservation"
#
# Scratchpad:
# - crossover, compare technique where parents breed exclusively vs non-excl.
# - return if avg fitness starts to drop?
# - Should have done this purely OO, with objects for everything, especially
#   solutions, then solution class could have it's own methods and make
#   the code more organized
#
#######################################################################
# Imports
#######################################################################
import collections
import operator

#######################################################################
# Global variables
#
# Heads up with default dict, when process_input_from_solution runs,the
# values are stored as lists, so you'll see [''] around the actual
# value, have to reference the 0th element of the list to get value
#######################################################################
GD = dict(
    POPULATION=4,
    CULL_SURVIVORS=2,
    NUM_ITERATIONS=10,
    NUM_SOLUTIONS_TO_RETURN=1,
    MUTATION_RATE=5,
    HIGH_SCORE=20000,
    INFO_LEVEL=3,  # see Helper.say()
    ROOM_CAPACITY_WASTE_THRESHOLD_PCT=25,
    UNIMPLEMENTED_BELOW_THIS_DUMMY_VAR=True,
    GENE_SWAP_PCT=50,
    CROSSOVER_TYPE="RANDOM_SINGLE",
    MUTATION_SEVERITY=10,
    CSV_IN='Data/ScheduleOfClassesSample.csv',
    CSV_NUM_LINES=0,
    CSV_NUM_ERRORS=0,
    COURSE_CONSTRAINTS='Data/CourseConstraints.csv',
    FITNESS_CONSTRAINTS='Data/FitnessConstraints.csv',
    ROOM_CONSTRAINTS='Data/RoomConstraints.csv',
    INSTRUCTOR_CONSTRAINTS='Data/InstructorConstraints.csv',
    HIGH_FITNESS_INDEX=0,
    LOGFILE=open('run.log', 'w'),
    DB_2LEVEL_PARAMS=["C", "I", "R", "S", "T", "CC"],
    DB_1LEVEL_PARAMS=["FC", "RC", "IC"],
    C=collections.defaultdict(lambda: collections.defaultdict()),  # courses
    I=collections.defaultdict(lambda: collections.defaultdict()),
    R=collections.defaultdict(lambda: collections.defaultdict()),  # rooms
    T=collections.defaultdict(lambda: collections.defaultdict()),  # times
    S=collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict()
    )),
    S_COPY=collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict()
    )),
    F=collections.defaultdict(lambda: collections.defaultdict()),
    RT=collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict()
    )),
    IT=collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict()
    )),
    CD=collections.defaultdict(int),  # stores sorted solution keys
    CC=collections.defaultdict(lambda: collections.defaultdict()),
    FC=collections.defaultdict(lambda: collections.defaultdict()),
    RC=collections.defaultdict(lambda: collections.defaultdict()),
    IC=collections.defaultdict(lambda: collections.defaultdict()),
    C_PARAMS=["Class Nbr",
              "*Section",
              "Class Description",
              "Enrollment Cap",
              "Enrollment Total",
              "Class Subject + Nbr",
              "Instructor Name",
              "Unit",
              "Primary Instruction Section",
              "*Course ID",
              "Status",
              "Campus",
              "Component Cd",
              "Maximum Units",
              "Minimum Units",
              "Consent Required",
              ],
    I_PARAMS=["Instructor Name",
              "Instructor Email",
              "Instructor Emplid",
              "Instructor Jan/Dana ID",
              "Instructor Last Name",
              "Instructor First Name",
              "Instructor Jobtitle",
              "Instructor Department",
              "College",
              ],
    R_PARAMS=["Facility ID",
              "Wait List Cap",
              ],
    CC_PARAMS=["Course",
               "Section",
               "Instructor",
               "Room",
               "Time Slot",
               "Prereq",
               "Coreq",
               "Semester",
               ],
    # "Condition",
    FC_PARAMS=[
              "Penalty",
              ],
    # "Room",
    RC_PARAMS=[
               "Building",
               "Capacity",
               "Labs Supported",
               ],
    # "Instructor Jan/Dana ID",
    IC_PARAMS=["Instructor Name",
               "Instructor Emplid",
               "Instructor Building",
               "Courses Taught",
               "Instructor Last Name",
               "Instructor First Name",
               "Instructor Jobtitle",
               "Instructor Department",
               "Instructor Email",
               "Instructor Jan/Dana ID",
               "College",
               ],
    S_PARAMS=["*Course ID",
              "Time Slot",
              "*Section",
              "Class Description",
              "Class Nbr",
              "Enrollment Cap",
              "Class Subject + Nbr",
              "End Time",
              "Facility ID",
              "Instructor Name",
              "Meets on Monday",
              "Meets on Tuesday",
              "Meets on Wednesday",
              "Meets on Thursday",
              "Meets on Friday",
              "Meets on Saturday",
              "Meets on Sunday",
              "Start Time",
              "Unit",
              "Status",
              "Instructor Email",
              "Instructor Emplid",
              "Instructor Jan/Dana ID",
              "Instructor Last Name",
              "Instructor First Name",
              "College",
              "Primary Instruction Section",
              "Enrollment Total",
              "Instructor Jobtitle",
              "Instructor Department",
              "Instructor Building",
              "Building",
              "Campus",
              "Component Cd",
              "Maximum Units",
              "Minimum Units",
              "Consent Required",
              ]
)


#######################################################################
# Input processing class
#######################################################################
class InputProcessor:
    global GD

    def __init__(self):
        """
        Constructor with initialization

        Database ideas:
        C = Course catalog
           - courses offered, # sections, # seats needed
           - demand
           - prereq chains
           Example:
               C[ID][Course Nbr] => ID = courseID from spreadsheet
        I = Instructor catalog
           - instructor names
           - preferred days/times
           - office/building
           - what they teach and weight of how good they are
        R = Building/room catalog
           - room # (depends on class, room-to-class mapping of caps)
           - size
           - configuration (lab, type of desk, etc)
           - already_taken?
        T = Time and day slots
           - days
           - start time
           - end time
           - details (meets on M/T/.../F)
        S = Solutions
           - fitness of each solution
           - problem_solution
        F = Fitness
           - this could be a dict where the first key is the fitness
             of the solution, and the solution is contained under the key
             The effect is that it's sorted
             Copy data into this as the population is culled
        """
        H.say("INFO", "Initializing data structures...")

    # Process the input and build out the data structures
    @staticmethod
    def process_input_from_solution():
        """
        Temporary method to build data structures based on sample solution,
        not sample input.
        :return: none
        """
        import csv

        H.say("INFO", "Processing input ...")
        row_num = 0
        # Iterate over the CSV and extract the information
        with open(GD['CSV_IN'], newline='', encoding='utf-8') as csv_in:
            csv_data = csv.DictReader(csv_in, delimiter=',', quotechar='"')
            for row in csv_data:
                GD['CSV_NUM_LINES'] += 1
                course_key = row['*Course ID'] + "_" + row['*Section']
                instructor_key = row['Instructor Jan/Dana ID']
                room_key = row['Facility ID']
                if course_key == '' or course_key == ' ':
                    H.say("VERBOSE", "Skipping blank record from row ",
                          row_num+1
                          )
                    continue
                # Now store course information into DB, can't do this
                # in a loop for each set of params because the id_num
                # will be different for courses/rooms/profs
                # TODO: error check here, see if already exists and diff
                for c_param in GD['C_PARAMS']:
                    GD['C'][course_key][c_param] = [row[c_param]]
                # store room information
                if room_key == '' or room_key == ' ':
                    H.say("LOG", "Missing room info from row ", row_num+1)
                    continue
                for r_param in GD['R_PARAMS']:
                    GD['R'][room_key][r_param] = [row[r_param]]

                # store instructor information
                if instructor_key == '' or instructor_key == ' ':
                    H.say("LOG", "Missing instructor info from row ",
                          row_num + 1
                          )
                    continue
                for i_param in GD['I_PARAMS']:
                    if instructor_key == '':
                        H.say("LOG", "Missing", i_param, " from row ",
                              row_num + 1
                              )
                        continue
                    GD['I'][instructor_key][i_param] = [row[i_param]]
                row_num += 1
        H.say("INFO", "Done pre-processing, found ",
              GD['CSV_NUM_LINES'], " lines, ",
              GD['CSV_NUM_ERRORS'], " errors")

    @staticmethod
    def process_schedule_constraints():
        """
        Method to store which contains the valid dates/times
        that classes will be held and populate a hash. Could store
        this info during input_processing, but having a separate method
        makes for a more modular solution

        This method uses the sample CSV as the set of constraints to
        extract valid day/time combinations from.

        For date/times - there is official NAU list of this somewhere, can
        pull this in later if time but for now, just extract information
        from the Sample

        :return:
        """
        import csv

        H.say("INFO", "Processing schedule constraints ...")
        row_num = 0
        # Iterate over the CSV and extract the information
        with open(GD['CSV_IN'], newline='', encoding='utf-8') as csv_in:
            csv_data = csv.DictReader(csv_in, delimiter=',', quotechar='"')
            for row in csv_data:
                time_slot_code = ''
                has_a_day = 0
                row_num += 1
                # Pull the day information
                if row['Meets on Monday'] == "Y":
                    time_slot_code += "M"
                    has_a_day += 1
                if row['Meets on Tuesday'] == "Y":
                    time_slot_code += "T"
                    has_a_day += 1
                if row['Meets on Wednesday'] == "Y":
                    time_slot_code += "W"
                    has_a_day += 1
                if row['Meets on Thursday'] == "Y":
                    time_slot_code += "Th"
                    has_a_day += 1
                if row['Meets on Friday'] == "Y":
                    time_slot_code += "F"
                    has_a_day += 1
                if row['Meets on Saturday'] == "Y":
                    time_slot_code += "S"
                    has_a_day += 1
                if row['Meets on Sunday'] == "Y":
                    time_slot_code += "U"
                    has_a_day += 1
                # skip this row if no day assigned
                if has_a_day == 0:
                    H.say("LOG", "Warning, no days found in row ", row_num)
                    continue

                # Pull the time information
                # start time
                H.say("DBG", row_num, "<>", row['Start Time'])
                fragments = row['Start Time'].split(' ')
                try:
                    start_time = fragments[1]
                except:
                    H.say("LOG", "Warning, no time in row ", row_num)
                fragments = row['End Time'].split(' ')
                # end time
                try:
                    end_time = fragments[1]
                except:
                    H.say("LOG", "Warning, no time in row ", row_num)
                time_slot_code += "_" + start_time + "_" + end_time
                H.say("DBG", time_slot_code)
                
                # Populate the time slot hash with needed info now
                # that we have the key
                GD['T'][time_slot_code]['Start Time'] = start_time
                GD['T'][time_slot_code]['End Time'] = end_time
                GD['T'][time_slot_code]['Meets on Monday'] \
                    = row['Meets on Monday']
                GD['T'][time_slot_code]['Meets on Tuesday'] \
                    = row['Meets on Tuesday']
                GD['T'][time_slot_code]['Meets on Wednesday'] \
                    = row['Meets on Wednesday']
                GD['T'][time_slot_code]['Meets on Thursday'] \
                    = row['Meets on Thursday']
                GD['T'][time_slot_code]['Meets on Friday'] \
                    = row['Meets on Friday']
                GD['T'][time_slot_code]['Meets on Saturday'] \
                    = row['Meets on Saturday']
                GD['T'][time_slot_code]['Meets on Sunday'] \
                    = row['Meets on Sunday']
                GD['T'][time_slot_code]['AlreadyAssigned'] = "false"
        # Finished
        H.say(
            "INFO", "Done, created ", len(GD['T']),
            " time slots from ", row_num, " lines"
        )

    @staticmethod
    def process_csv_constraints(csv_file, param):
        """
        Generic method to open csv containing any special constraints
        a course has, such as
        - room it must be taught in
        - instructor(s) [specify on separate lines in CSV]
        - Prereq
        - Coreq
        - Semester taught (fall or spring or both)
        :return:
        """
        import csv
        H.say("INFO", "Processing ", csv_file, "...")
        row_num = 0
        stored_params = 0
        base_key = ""
        item_key = ""
        if param == 'CC_PARAMS':
            base_key = 'CC'
            item_key = 'Course'  # do nothing in this case
        if param == 'FC_PARAMS':
            base_key = 'FC'
            item_key = 'Condition'
        if param == 'RC_PARAMS':
            base_key = 'RC'
            item_key = 'Room'
        if param == 'IC_PARAMS':
            base_key = 'IC'
            item_key = 'Instructor Jan/Dana ID'
        with open(csv_file, newline='', encoding='utf-8') as csv_in:
            csv_data = csv.DictReader(csv_in, delimiter=',', quotechar='"')
            for row in csv_data:
                for csv_param in GD[param]:
                    i_key = row[item_key]
                    value = row[csv_param]
                    if value != '':
                        # create mechanism to allow for direct access to
                        # make it easier to directly pull values later for
                        # ones that don't need to have a random unique key
                        if base_key == 'CC':
                            GD[base_key][row_num][csv_param] = value
                        else:
                            H.say("VERBOSE", "storing ", value, " under",
                                  "[", base_key, "]",
                                  "[", i_key, "]"
                                  "[", csv_param, "]",
                                  )
                            GD[base_key][i_key][csv_param] = value
                        stored_params += 1
                    else:
                        if 'CC' not in base_key:
                            GD[base_key][i_key][csv_param] = ''
                row_num += 1
        H.say("INFO", "Done, stored ",
              stored_params,
              " constraints from ",
              row_num,
              " lines."
              )

    @staticmethod
    def print_database_1level(param):
        """
        Method for printing a single database/dict
        Assumes the database is only 2 levels deep
        :param param:
        :return:
        """
        H.say("DBG", "Database: ", param)
        for k1 in GD[param]:
            H.say("DBG", "[", k1, "]:", GD[param][k1])

    @staticmethod
    def print_database_2level(param):
        """
        Method for printing a single database/dict
        Assumes the database is only 2 levels deep
        :param param:
        :return:
        """
        H.say("DBG", "Database: ", param)
        for k1 in GD[param]:
            for k2 in GD[param][k1]:
                # TODO: load regexp module and skip all assigned
                if k2 != "AlreadyAssigned":
                    H.say("DBG", "[", k1, "][", k2, "]:", GD[param][k1][k2])

    @staticmethod
    def print_database_keys(param):
        """
        Method to print just the keys of a database to a CSV, using this
        to generate lists of each course, instructor, room, etc for
        building the "constraints" CSVs. This is so simple, no need for
        DictWriter on this one
        :param param:
        :return:
        """
        import sys

        file_name = "keys_" + param + ".csv"
        try:
            fh = open(file_name, 'w')
            H.say("INFO", "Writing ", file_name, "...")
        except PermissionError:
            H.say("ERROR", file_name, " probably open")
            sys.exit(2)
        except:
            print("ERROR", "Unknown error with ", file_name)
        # print the data
        for key in sorted(GD[param]):
            print(key, file=fh)

    def print_databases(self):
        """
        Method for iterating over each of the databases and printing them
        :return:
        """
        H.say("LOG", "All 2-level databases: ")
        for param2 in GD['DB_2LEVEL_PARAMS']:
            H.say("LOG", ">", param2)
            self.print_database_2level(param2)

        H.say("LOG", "All 1-level databases: ")
        for param1 in GD['DB_1LEVEL_PARAMS']:
            H.say("LOG", ">", param1)
            self.print_database_1level(param1)

    @staticmethod
    def print_sample_assignments():
        """
        Method for printing csv of each course/instructor assignment from
        the sample CSV
        :return:
        """
        file_name = "sample_assignments.csv"
        file = open(file_name, 'w')
        for key in sorted(GD['C']):
            for x in GD['C'][key]["Class Subject + Nbr"]:
                print(x, file=file, end=',')
            for y in GD['C'][key]["*Section"]:
                print(y, file=file, end=',')
            for z in GD['C'][key]["Instructor Name"]:
                print(z, file=file)

    @staticmethod
    def print_instructor_info():
        """
        Helper method to print all info that's in the I dict to csv
        :return:
        """
        file_name = "instructor_info.csv"
        file = open(file_name, 'w')
        print("Instructor Jan/Dana ID", file=file, end=',')
        print("Instructor Name", file=file, end=',')
        print("Instructor Department", file=file, end=',')
        print("College", file=file, end=',')
        print("Instructor Emplid", file=file)
        for key in sorted(GD['I']):
            print(GD['I'][key]["Instructor Jan/Dana ID"][0], file=file, end=',')
            print('"', GD['I'][key]["Instructor Name"][0], '"', file=file, end=',')
            print(GD['I'][key]["Instructor Department"][0], file=file, end=',')
            print(GD['I'][key]["College"][0], file=file, end=',')
            print(GD['I'][key]["Instructor Emplid"][0], file=file)


#######################################################################
# Helper methods class
# H = "Helper", shortened to H for length of line considerations
#######################################################################
class H:
    global GD

    @staticmethod
    def say(*args):
        """
        say method for messages, allows for flexible verbosity from script
        -----------------------------------------------
        usage: say(<info_level>,<all_message_elements>)

        Info levels - controlled by GD['INFO_LEVEL'}
        (all levels will print to still print to LOG):
        0 = Turn off all messages to the prompt/shell
        1 = Turn on INFO messages to the prompt
        2 = Turn on VERBOSE messages to the log
        3 = Turn on DBG messages to the prompt

        Exit if ERROR

        :param args: List of items to be printed
        :return:
        """
        import sys
        level = args[0]
        end_char = ': '
        printed_to_terminal = 0
        printed_to_log = 0
        for k in args:
            if level == "INFO" and GD['INFO_LEVEL'] >= 1:
                print(k, end=end_char)
                print(k, file=GD['LOGFILE'], end=end_char)
                printed_to_terminal += 1
                printed_to_log += 1
            if level == "VERBOSE" and GD['INFO_LEVEL'] >= 2:
                if k != "VERBOSE":
                    print(k, file=GD['LOGFILE'], end=end_char)
                    printed_to_log += 1
            if level == "DBG" and GD['INFO_LEVEL'] >= 3:
                print(k, file=GD['LOGFILE'], end=end_char)
                printed_to_log += 1
            if level == "DBG1" and GD['INFO_LEVEL'] >= 1:
                print(k, file=GD['LOGFILE'], end=end_char)
                print(k, end=end_char)
                printed_to_log += 1
                printed_to_terminal += 1
            if level == "LOG":
                if k != "LOG":
                    print(k, file=GD['LOGFILE'], end=end_char)
                    printed_to_log += 1
            if level == "WARN":
                print(k, file=GD['LOGFILE'], end=end_char)
                printed_to_log += 1
            if level == "ERROR":
                print(k, file=GD['LOGFILE'], end=end_char)
                print(k, end=end_char)
            end_char = ''
        if printed_to_terminal > 0:
            print()
        if printed_to_log > 0:
            print(file=GD['LOGFILE'], end='\n')
        if "ERROR" in level:
            sys.exit(2)

    @staticmethod
    def help(*args):
        if args[0] == 1:
            H.say("ERROR",
                  "Exceeded max tries, this means an open ",
                  "time could not be found for an instructor from: ",
                  GD['C'][args[1]]['Instructors'], " to teach ",
                  args[2], " section ", args[3],
                  "\nTry running again to get different ",
                  "random seed. If problem persists, please\n",
                  "consider *Constraints.csv files and the ",
                  "following:\n",
                  "1) are there enough instructors for each course?\n",
                  "2) too many forced assignments:\n",
                  "  - at same time\n",
                  "  - for given instructor(s)\n"
                  )
        # H.help(2, course, instructor, room, course_name, course_section)
        if args[0] == 2:
            H.say("ERROR", "not able to make random assignment: \n",
                  "course: ", args[1], "\n",
                  "instructor: ", args[2], "\n",
                  "room: ", args[3], "\n",
                  "course_name: ", args[4], "\n",
                  "section: ", args[5], "\n",
                  "Look at which parameter above is an empty string. ",
                  "That should indicate the problem.\n",
                  "Consider if this course has too many sections ",
                  "for the number of instructors who teach it.\n",
                  "Also consider if the instructors who can teach ",
                  "it are overloaded relative to other instructors.")

    @staticmethod
    def atomize_time_slot(time_slot):
        """
        Helper return a list of enumerated time slots for each day:

        MWF_8:00_8:50 becomes {M_8:00_8:50, W_8:00_8:50, F_8:00_8:50}

        :param time_slot:
        :return:
        """
        H.say("DBG", "atomize_time_slot() in: ", time_slot)
        # Variables
        atomized_slots = []

        ts = time_slot.replace("Th", "H")

        e = H.get_time_slot_elements(ts)
        days = e[0]

        for d in days:
            # Change Th back, maybe should leave it as H or R?
            d_r = d.replace("H", "Th")
            atomized_slots.append(d_r + "_" + e[1] + "_" + e[2])

        return atomized_slots

    @staticmethod
    def copy_solution(from_key, to_key, from_db, to_db):
        """
        Helper to perform the copy of all key/value pairs for a
        solution entry in one dict to another
        :param from_key:
        :param to_key:
        :param from_db:
        :param to_db:
        :return:
        """
        H.say("DBG", "Copying solution ", from_key,
              " from ", from_key, " to ", to_key)
        for c in GD[from_db][from_key]:
            for param in GD['S_PARAMS']:
                GD[to_db][to_key][c][param] = GD[from_db][from_key][c][param]

    @staticmethod
    def check_day_equivalence(reference, check):
        """
        Helper to check if days overlap between reference and check args

        Make each day atomic. MWF will return M, W, F. M will return only M.
        Changed from MWF returning MWF and M returning MWF


        Example: MW would overlap with MWF time slot, and vice versa, but
                 would not overlap with F time slot.
                 TTh would not overlap with MW or MWF or F, but would
                 overlap with T, Th, or TTh.

        :param reference: compare against this arg, e.g. MWF
        :param check: argument to check, e.g. MW
        :return: True/False
        """
        # Swap out "Th" for "H" for easy comparisons
        # So we have M T W H F
        r = reference.replace("Th", "H")
        c = check.replace("Th", "H")

        # TODO: can remove the error checking when this is verified...
        if len(r) != 1:
            H.say("ERROR", "Incorrect argument passed to ",
                  "check_day_equivalence(r): ", r)
        if len(c) != 1:
            H.say("ERROR", "Incorrect argument passed to ",
                  "check_day_equivalence(c): ", c)

        # Iterate over elements of check and see if they occur in reference
        if c == r:
            H.say("DBG", "check_day_equivalence, c: ", c,
                  " equals r: ", r, ", returning true")
            return True

        # Default case, return false
        return False

    @staticmethod
    def check_forced(index, course, element_type):
        if "Facility" in element_type:
            forced_type = "RoomForced"
        elif "Time" in element_type:
            forced_type = "TimeForced"
        elif "Instructor" in element_type:
            forced_type = "InstructorForced"
        else:
            H.say("ERROR", "Unsupported type to check_forced(): ",
                  element_type)
        if forced_type in GD['S'][index][course]:
            return True
        return False

    @staticmethod
    def execute_management(resource_type, index, resource, time, mode):
        """
        Wrapper method to make error checking modular and re-usable

        :param resource_type:
        :param index:
        :param resource:
        :param time:
        :param mode:
        :return:
        """
        for arg in (resource_type, index, resource, time, mode):
            if isinstance(arg, list):
                print("DBG TODO REMOVE")
        # Check for a valid mode.
        if not (mode == "free" or mode == "busy"):
            H.say("ERROR", "Invalid mode passed to execute_management(): ",
                  mode)
        # Check that the resource actually exists
        if resource not in GD[resource_type][index]:
            H.say("ERROR", "Trying to ", mode,
                  " resource that doesn't exist: ", resource)
        GD[resource_type][index][resource][time] = mode

    @staticmethod
    def get_course_name(course):
        return GD['C'][course]['Class Subject + Nbr']

    @staticmethod
    def get_course_section(course):
        return GD['C'][course]['*Section']

    @staticmethod
    def get_equivalent_slots(time_slot):
        """
        Given a time_slot, returns a list of time slots which overlap on
        at least one day.

        :param time_slot:  MWF_9:10_10:00
        :return: 'W_8:00_10:00', 'F_8:00_10:00', 'MWF_9:10_10:00', 'M_8:00_10:00'
        """
        H.say("DBG", "get_equivalent_slots() in: ", time_slot)
        # Variables
        return_value = []

        # Convert the input and do error checking. Atomize the input first.
        atoms = H.atomize_time_slot(time_slot)
        for a in atoms:
            e = H.get_time_slot_elements(a)
            start_time = int(H.get_time(e[1]))
            end_time = int(H.get_time(e[2]))
            if start_time >= end_time:
                H.say("ERROR", "get_equivalent_slots(): ",
                      "start time greater than end time")
            for t in (start_time, end_time):
                if t < 0 or t > 2400:
                    H.say("ERROR", "get_equivalent_slots(): invalid time: ", t)

        # Do equivalent lookups for the start time and append them.
        for ts in GD['T']:
            ts_atoms = H.atomize_time_slot(ts)
            for ts_a in ts_atoms:
                ts_e = H.get_time_slot_elements(ts_a)
                # enumerate the conditions over which a time slot is equivalent
                c1 = H.get_time(e[1]) >= H.get_time(ts_e[1])
                c2 = H.get_time(e[1]) <= H.get_time(ts_e[2])
                c3 = H.get_time(e[2]) >= H.get_time(ts_e[1])
                c4 = H.get_time(e[2]) <= H.get_time(ts_e[2])
                c5 = H.check_day_equivalence(e[0], ts_e[0])
                if ((c1 and c2) or (c3 and c4)) and c5:
                    if ts_a not in return_value:
                        return_value.append(ts_a)

        # Do equivalent lookups for the end time and append them.
        H.say("DBG", "get_equivalent_slots() out: ", return_value)
        return return_value

    @staticmethod
    def get_random_number(hash_key):
        """
        method to generate a random number that will be between 0 and
        the length of the hash that we will use the number to pull an
        element from
        :param hash_key:
        :return random_number:
        """
        import random
        max_num = len(GD[hash_key])
        return random.randrange(0, max_num, 1)

    @staticmethod
    def get_random_course(hash_key, entry):
        """
        method to get a random course from a solution dict
        Designed for use with cull_population
        """
        import random
        counter = 0
        max_num = len(GD[hash_key][entry])
        key_num = random.randrange(0, max_num, 1)
        for course in GD[hash_key][entry]:
            if key_num == counter:
                return course
            else:
                counter += 1
        # Error if we reach this point
        H.say("ERROR", "Unable to find a random course key for ", hash_key)

    @staticmethod
    def get_random_element(key, course):
        """
        method to randomly get an element off 'R', 'T' or 'I' dict. Does
        not check if the element is free or not.

        Designed for use with generate_random_solutions and mutate.

        :param key:
        :param course:
        :return: element
        """
        H.say("DBG", "get_random_element() in: ", key)
        import sys
        import random
        counter = 0
        # Skip the random vs counter loop for instructors, since we will pull
        # them off of a hash directly and randomly assign one of them
        if 'I' in key:
            r_n = 0
        else:
            r_n = H.get_random_number(key)
        e_id = ""  # for error message printing only
        for element_id in GD[key]:
            e_id = element_id
            if counter == r_n:
                # Pull an instructor randomly from a qualified pool
                if 'I' in key:
                    pool = GD['C'][course]['Instructors']
                    pool_size = len(pool)
                    name = H.get_course_name(course)[0]
                    H.say("DBG", "get_random_element() pool: ", pool)
                    if pool_size < 1:
                        H.say("ERROR", "No instructors for: ", name)
                    elif pool_size == 1:
                        element_id = pool[0]
                    else:
                        i_random = random.randrange(0, pool_size)
                        element_id = pool[i_random]
                    H.say("DBG", "get_random_element() out(I): ", element_id)
                    return element_id
                elif 'R' in key:
                    H.say("DBG", "get_random_element() out(R): ", element_id)
                    return element_id
                elif 'T' in key:
                    H.say("DBG", "get_random_element() out(T): ", element_id)
                    return element_id
                else:
                    H.say("ERROR", "get_random_element() invalid key: ", key)
            else:
                counter += 1

        # If we reach this point, a problem occurred, exit with info
        H.say(
            "ERROR",
            "Not able to find a random element from ",
            key, "\n",
            "dict, this means all possibilities were already assigned\n",
            "There aren't enough of one of the following:\n",
            "day/time slots, instructors, or rooms\n\n",
            "Was trying: \n",
            e_id,
        )
        sys.exit(2)

    @staticmethod
    def get_random_course_element():
        """
        Helper method to randomly return either "Facility ID" or "Time Slot"

        Designed for use with mutate() method
        :return: element_code
        """
        import random
        number = random.randrange(0, 9, 1)
        if number < 5:
            element_code = "Facility ID"
        else:
            element_code = "Time Slot"
        return element_code

    @staticmethod
    def get_id(instructor_name):
        """
        Takes 'Instructor Name' field and returns the equivalent
        NAU Jan/Dana ID #
        :param instructor_name: 'Palmer, James Dean'
        :return: e.g. 'jdp85'
        """
        H.say("DBG", "get_id() in: ", instructor_name)
        try:
            for key in GD['I']:
                if GD['I'][key]['Instructor Name'][0] == instructor_name:
                    H.say("DBG", "get_id() out: ", key)
                    return key
        except:
            H.say("ERROR", "get_id(): Could not find Jan/Dana ID for: ",
                  instructor_name)

    @staticmethod
    def get_resource(rs_counter, course, time, code, cc_key):
        """
        Return a semi-randomly assigned resource (obeys constraints). If a
        non-empty string is passed in for cc_key, then it will check for
        forced assignments first before randomly assigning.

        :param rs_counter:
        :param course:
        :param time:
        :param code:
        :param cc_key: key from the course constraints hash
        :return:
        """
        # Process inputs
        if "I" in code:
            r_type = 'I'
            r_key1 = 'InstructorAssigned'
            r_key2 = 'Instructor'
            num_to_try = len(GD['C'][course]['Instructors'])
            check_code = 'IT'
        elif "R" in code:
            r_type = 'R'
            r_key1 = 'RoomAssigned'
            r_key2 = 'Room'
            num_to_try = len(GD['R'])
            check_code = 'RT'
        else:
            H.say("ERROR", "get_resource() was passed unknown type: ", code)
            return

        # Variables
        resource = ""

        # Forced assignments first
        if cc_key != "":
            resource = H.make_forced_assignment(rs_counter,
                                                course,
                                                time,
                                                r_type,
                                                cc_key
                                                )

        # Iterate until available resource found
        if resource == "":
            flag = False
            try_counter = 0
            while not flag:
                if try_counter == num_to_try:
                    H.say("DBG", "all ", r_type, " busy at ", time)
                    return ""
                    break
                resource = H.get_random_element(code, course)
                eq_times = H.get_equivalent_slots(time)
                flag = H.manage_resource(check_code,
                                         rs_counter,
                                         resource,
                                         eq_times,
                                         "check"
                                         )
                try_counter += 1
        else:
            flag = True

        if flag:
            H.say("DBG", "get_resources() returning ", r_type, " : ", resource)
            return resource
        else:
            return ""

    @staticmethod
    def get_time(time):
        """
        Helper to convert 24hr time into an integer.

        :param time: time in 24hr format, e.g. 8:50, 13:00
        :return: integer numerical equivalent, e.g. 850, 1300
        """
        components = time.split(':')
        if len(components) != 2:
            H.say("ERROR", "trying to convert invalid input time: ", time)

        numerical_time = int(components[0] + components[1])

        return numerical_time

    @staticmethod
    def get_time_slot(solution, course):
        """
        Helper to get a random time slot and assign the course to it
        within the given solution number.

        :param solution: key from GD['S'] hash
        :param course: key from GD['S'][solution] hash
        :return:
        """
        H.say("DBG", "get_time_slot() in: ", solution, ":", course, ":")
        time = H.get_random_element('T', course)
#        for t_key in GD['T'][time]:
#            GD['S'][solution][course][t_key] = GD['T'][time][t_key]
#        GD['S'][solution][course]['Time Slot'] = time
        H.say("DBG,", "get_time_slot() out: ", time)
        return time

    @staticmethod
    def get_time_slot_elements(time_slot):
        """
        Helper to split time_slot, can do error checking in here, so that's
        the idea behind creating a method for a single-line operation.

        :param time_slot: e.g. MWF_8:00_8:50
        :return: list of each component, e.g. (MWF, 8:00, 8:50)
        """
        return_value = time_slot.split('_')
        if len(return_value) != 3:
            H.say("ERROR", "get_time_slot_elements() : Invalid time slot: ",
                  time_slot)
        return return_value

    @staticmethod
    def make_assignment(solution, course, resource, time, mode):
        """
        Helper method to assign the given resource at a given time for the
        given course within the solution.

        :param solution:
        :param course:
        :param resource:
        :param time:
        :param mode:
        :return:
        """
        # Instructor + ( time + course params <- only do these once)
        if "instructor" in mode:
            # Course params
            for c_param in GD['C_PARAMS']:
                GD['S'][solution][course][c_param] = GD['C'][course][c_param]

            # Instructor params
            for i_key in GD['I'][resource]:
                GD['S'][solution][course][i_key] \
                    = GD['I'][resource][i_key]
            GD['S'][solution][course]['Instructor Building'] = \
                GD['IC'][resource]['Instructor Building']
            times = H.get_equivalent_slots(time)
            H.say("DBG", " resource: ", resource)
            H.manage_resource('IT', solution, resource,
                              times, "book")

            # Time
            if time not in GD['T']:
                name = GD['C'][course]['Class Subject + Nbr']
                section = GD['C'][course]['*Section']
                H.say("ERROR", "Trying to assign non-existent time slot ",
                      time, " for course: ", name, " section: ", section,
                      "\nAre you forcing ",
                      "invalid constraint in CourseConstraints?"
                      )
            for t_key in GD['T'][time]:
                GD['S'][solution][course][t_key] = GD['T'][time][t_key]
            GD['S'][solution][course]['Time Slot'] = time

        # Room
        if "room" in mode:
            GD['S'][solution][course]['Facility ID'] \
                = GD['R'][resource]['Facility ID']
            GD['S'][solution][course]['Building'] \
                = GD['RC'][resource]['Building']
            GD['S'][solution][course]['Unit'] \
                = GD['C'][course]['Unit']
            times = H.get_equivalent_slots(time)
            H.manage_resource('RT', solution, resource, times, "book")

    @staticmethod
    def make_forced_assignment(solution, course, time, db_type, cc_key):
        """
        Helper method to get_resource, this one takes a key
        from the GD['C'] courses hash and a type of assignment ('I', 'R', etc)
        and propagates forced assignment if one was made by CSV constraint

        :param solution:
        :param course:
        :param time:
        :param db_type:
        :param cc_key: key from CourseConstraint dict, saves us a loop
        :return:
        """
        H.say("DBG", "make_forced_assignment() in: ",
              solution, ":", course, ":", time,
              ":", db_type, ":", cc_key)
        forced = 0
        if cc_key in GD['CC']:
            forced += 1
            cc_course = GD['CC'][cc_key]['Course']
            eq_times = H.get_equivalent_slots(time)

            # Deal with instructors
            if db_type == "I":
                instructor = H.get_id(GD['CC'][cc_key]['Instructor'])
                flag = H.manage_resource('IT',
                                         solution,
                                         instructor,
                                         eq_times,
                                         "check"
                                         )
                # Error out if resource busy, this would indicate that
                # constraints file has them double-booked.
                if not flag:
                    H.say("ERROR", "Trying to force assign busy resource:",
                          instructor, " @ ", time,
                          "\nCheck our CourseConstraints.")
                GD['S'][solution][course]['InstructorForced'] = True
                H.say("DBG", "make_forced_assignment()",
                      "force assign instructor: ", instructor)
                return instructor

                # Deal with roms
            if db_type == "R":
                # Skip the case where course is assigned to instructor,
                # but not to a room.
                if 'Room' in GD['CC'][cc_key]:
                    room = GD['CC'][cc_key]['Room']
                    room_capacity = GD['RC'][room]['Capacity']
                    course_capacity = GD['C'][course]['Enrollment Cap'][0]
                    if int(course_capacity) > int(room_capacity):
                        H.say("ERROR", "Trying to assign course ",
                              cc_course, " with capacity ",
                              course_capacity, " to room ",
                              room, " but will be over room capacity(",
                              room_capacity, ")!"
                              )
                    else:
                        flag = H.manage_resource('RT',
                                                 solution,
                                                 room,
                                                 eq_times,
                                                 "check"
                                                 )
                        # Error out if room not free
                        GD['S'][solution][course]['RoomForced'] = True
                        if not flag:
                            H.say("ERROR",
                                  "Trying to force assign busy room: ",
                                  room, " @ ", time)
                        # Else make the assignment'
                        H.say("DBG", " force assign room: ", room)
                        return room

                # May need to support day/time assignment as well

        # If we fall through to here, no forced assignment needs to be made.
        H.say("DBG", "make_forced_assignment() returning empty string")
        return ""

    @staticmethod
    def manage_resource(resource_type, solution, resource, times, mode):
        """
        Helper to book or free a given resource at a given time.
        Also added functionality to check on the resource

        :param resource_type: RT or IT
        :param solution: number key for the solution on GD['S'] dict
        :param resource: room or instructor
        :param times: list of times in time slot format (MWF_08:00_09:15)
        :param mode: book, free, or check
        :return: True or False
        """
        H.say("DBG", "manage_resource() in: ", resource_type,
              ":", solution, ":", resource, ":", times, ":", mode)

        # Error checkin on arguments.
        if not ('RT' in resource_type or 'IT' in resource_type):
            H.say("ERROR", "manage_resource() received illegal resource_type: ",
                  resource_type)

        # determine the mode and process the request
        # Handle the "Book" requests
        if "book" in mode:
            H.say("VERBOSE", "booking resource ", resource,
                  " at times ", times
                  )
            for time in times:
                if GD[resource_type][solution][resource][time] == "free":
                    GD[resource_type][solution][resource][time] = "busy"
                else:
                    H.say("ERROR", "Trying to book a busy resource!\n",
                          resource, ":", time, ":", solution)
            H.say("DBG", "manage_resource() returning True (busy)")
            return True
        # end "Book"

        # Handle the "Free" requests
        elif "free" in mode:
            H.say("VERBOSE", "freeing resource ", resource,
                  " at times ", times
                  )
            # need to book or free times for all solutions if -1 is passed in
            for time in times:
                H.execute_management(resource_type, solution, resource,
                                     time, "free"
                                     )
            H.say("DBG", "manage_resource() returning True (free)")
            return True
        # End "free"

        # "Check" requests
        elif "check" in mode:
            is_free = True
            for time in times:
                if time not in GD[resource_type][solution][resource]:
                    H.say("ERROR", "Can't find ", time,
                          " as a valid time slot, are you forcing\n",
                          "invalid constraint in CourseConstraints?"
                          )
                # In theory, all times here would be free/busy together
                value = GD[resource_type][solution][resource][time]
                if "free" not in value:
                    is_free = False
                    break
            if is_free:
                H.say("DBG", "manage_resource() returning True (free)")
                return True
            else:
                H.say("DBG", "manage_resource() returning False (not free)")
                return False

        else:
            H.say("ERROR", "requested resource management for",
                  " and unknown mode: ", mode)
            return False  # isn't reached but quiets PyCharm

    @staticmethod
    def swap_elements(index, p1_course, p2_course, swap_type):
        """
        Swap elements on 'S' dict at given index if neither is a forced
        assignment.

        :param index:
        :param p1_course:
        :param p2_course:
        :param swap_type:
        :return: true if swapped
        """
        c1 = H.check_forced(index, p1_course, swap_type)
        c2 = H.check_forced(index, p2_course, swap_type)
        if c1 or c2:
            H.say("DBG", "s_e: skipping swap, one of elements was forced")
            return False
        else:
            temp = GD['S'][index][p1_course][swap_type]
            GD['S'][index][p1_course][swap_type] = \
                GD['S'][index][p2_course][swap_type]
            GD['S'][index][p2_course][swap_type] = temp
            return True


#######################################################################
# Population processing class
#
# The methods in this class operate by way of "assignment" principle. The
# code is trying to make assignments for room, instructor, time slot, etc..
# There are forced assignments and randomly generated ones.
#######################################################################
class Population:
    global GD

    @staticmethod
    def initialize_resources():
        """
        Method to initialize the GD['RT'] and GD['IT'] data structures, which
        contain an enumeration of all time slots for each room and
        instructor, respectively.

        Values are "busy" and "free". As each resource (room/instructor) is
        assigned, it is marked busy/free in this structure so that no
        duplicate resource assignments are made.

        :return:
        """
        H.say("INFO", "Initializing resources...")
        # Also add instructors from InstructorConstraints to GD['I'] dict
        for ic in GD['IC']:
            if ic not in GD['I']:
                for i_param in GD['I_PARAMS']:
                    temp = []
                    temp.append(GD['IC'][ic][i_param])
                    GD['I'][ic][i_param] = temp
                GD['I'][ic]['AlreadyAssigned'] = "false"

        # Iterate over each time slot, and create resources for R and I
        num_resources = 0
        s = 0
        while s < GD['POPULATION']:
            for ts in GD['T']:
                atoms = H.atomize_time_slot(ts)
                for a in atoms:
                    for r in GD['R']:
                        GD['RT'][s][r][a] = "free"
                        num_resources += 1
                    for i in GD['I']:
                        GD['IT'][s][i][a] = "free"
                        num_resources += 1
            s += 1

        # Check and make sure that all offered courses will have instructors
        courses_taught = ""
        courses_not_taught = collections.defaultdict()
        error_count = 0
        H.say("VERBOSE", "\nCourses taught:")
        for ic in GD['IC']:
            courses_taught += (GD['IC'][ic]['Courses Taught'])
            H.say("VERBOSE", GD['IC'][ic]['Courses Taught'])
        H.say("VERBOSE", "\nCourses offered:")
        for c in GD['C']:
            offered = GD['C'][c]['Class Subject + Nbr'][0]
            H.say("VERBOSE", offered, " section: ",
                  GD['C'][c]['*Section'])
            if courses_taught.find(offered) == -1:
                courses_not_taught[offered] = ""
                error_count += 1
            GD['C'][c]['Instructors'] = []  # initialize a string for later
        H.say("VERBOSE", "\n")
        if error_count:
            H.say("INFO", "These offered courses have no instructor\n",
                  "constrained to teach them:"
                  )
            for cnt in courses_not_taught:
                H.say("INFO", cnt)
            H.say("ERROR", "Please fix in: ", GD['COURSE_CONSTRAINTS']
                  )

        # Add "instructors" entry to the 'C' dict so that we can do a
        # direct lookup of instructors during instructor assignment.
        for c in GD['C']:
            c_name = H.get_course_name(c)[0]
            for i in GD['IC']:
                courses = GD['IC'][i]['Courses Taught']
                # Don't know how to do lookup between c_name and c directly
                # so do this the long way.
                if courses.find(c_name) != -1:
                    GD['C'][c]['Instructors'].append(i)

        H.say("INFO", "Done, created ",
              num_resources / s, " instructor/room resources for ",
              len(GD['T']), " time slots on the calendar.")

    @staticmethod
    def generate_random_solutions():
        """
        Method to generate the random seed of solutions
        Solution requirements:
        - all GD['C'][course_key] are assigned
        - all courses have an instructor and a room

        Flow of method:
        - assign all courses into the solution
        - pick a time slot
        - assign an instructor to the course
        - assign them to a room

        Issues (12/17/ infinite loop debug)
        - Probably not the best idea to pick the time slot first, or at least
          need a mechanism to update it if resources are all busy.
        - When finding a room, if all are busy, it will simply keep searching
          them all over and over again. Need a way to know that all have been
          checked and bump back out to pick a new time slot.
        - probably need to make all forced assignments first and book those
          resources because now, simply making the assignment and booking
          over top of any other assignment, so think about how to manage this

        :return:
        """
        H.say("INFO", "Generating set of random solutions...")
        # Initialize the resources calendar
        Population.initialize_resources()

        # Iterate over all course constraints and make assignments so that
        # the constraints reserve their place in the solution.
        rs_counter = 0
        num_forces = 0
        # Loop over all solutions.
        while rs_counter < GD['POPULATION']:
            H.say("INFO", "creating solution [", rs_counter, "]")
            # First loop over all course constraints
            for course in GD['C']:
                course_name = GD['C'][course]['Class Subject + Nbr']
                course_section = GD['C'][course]['*Section']
                instructor = ""
                room = ""
                time = ""
                # Could save this loop by making 'cc' key a code, not integer
                # to support direct look-up.
                for cc in GD['CC']:
                    c1 = (GD['CC'][cc]['Course'] in course_name)
                    c2 = (GD['CC'][cc]['Section'] in course_section)
                    if c1 and c2:
                        H.say("DBG", "found constraint(s) for: ",
                              course_name, " section ", course_section)
                        if 'Time Slot' in GD['CC'][cc]:
                            time = GD['CC'][cc]['Time Slot']
                            GD['S'][rs_counter][course]['TimeForced'] = True
                            H.say("DBG", "force time slot: ", time)
                            # This will get forced assignments.
                            instructor = H.get_resource(rs_counter,
                                                        course,
                                                        time,
                                                        'I',
                                                        cc
                                                        )
                            if instructor == "":
                                H.say("ERROR", "Instructor force error")
                            # This will get forced assignments.
                            room = H.get_resource(rs_counter,
                                                  course,
                                                  time,
                                                  'R',
                                                  cc
                                                  )
                            if room == "":
                                H.say("ERROR", "Room force error")
                            break
                        # This is the case where no time slot is forced.
                        else:
                            time_valid = False
                            time_try = 0
                            max_tries = len(GD['T'])
                            while not time_valid:
                                # if not, will set false during while
                                time_valid = True
                                time = H.get_time_slot(rs_counter, course)
                                time_try += 1
                                H.say("DBG", " trying time: ", time)
                                instructor = H.get_resource(rs_counter,
                                                            course,
                                                            time,
                                                            'I',
                                                            cc
                                                            )
                                if instructor == "":
                                    time_valid = False
                                room = H.get_resource(rs_counter,
                                                      course,
                                                      time,
                                                      'R',
                                                      cc
                                                      )
                                if room == "":
                                    time_valid = False
                                if time_try == max_tries:
                                    # Exit with message
                                    H.help(1, course,
                                           course_name, course_section)

                # Make the actual assignment
                if not (instructor == "") and not (room == ""):
                    H.say("DBG", "making forced assignments for ",
                          instructor, ":", room, ":", time)
                    H.make_assignment(rs_counter,
                                      course,
                                      instructor,
                                      time,
                                      "instructor"
                                      )
                    H.make_assignment(rs_counter,
                                      course,
                                      room,
                                      time,
                                      "room"
                                      )
                    num_forces += 1
                    GD['S'][rs_counter][course]['CourseAssigned'] = True
                else:
                    GD['S'][rs_counter][course]['CourseAssigned'] = False
            H.say("DBG", "Made ", num_forces, " forced assignments")

            # Second loop over all remaining unassigned courses
            for course in GD['C']:
                course_name = GD['C'][course]['Class Subject + Nbr']
                course_section = GD['C'][course]['*Section']
                instructor = ""
                room = ""
                time = ""
                if not GD['S'][rs_counter][course]['CourseAssigned']:
                    H.say("DBG", "\nRandomly assigning course: ", course,
                          " : ", course_name, " : ", course_section)
                    time_valid = False
                    time_try = 0
                    max_tries = len(GD['T'])
                    while not time_valid:
                        # if not, will set false during while
                        time_valid = True
                        time = H.get_time_slot(rs_counter, course)
                        time_try += 1
                        H.say("DBG", " trying time: ", time)
                        instructor = H.get_resource(rs_counter,
                                                    course,
                                                    time,
                                                    'I',
                                                    ""
                                                    )
                        if instructor == "":
                            time_valid = False
                        room = H.get_resource(rs_counter,
                                              course,
                                              time,
                                              'R',
                                              ""
                                              )
                        if room == "":
                            time_valid = False
                        if time_try == max_tries:
                            # Exit with message
                            H.help(1, course,
                                   course_name, course_section)
                    # Make the actual assignment
                    if not (instructor == "") and not (room == ""):
                        H.make_assignment(rs_counter,
                                          course,
                                          instructor,
                                          time,
                                          "instructor"
                                          )
                        H.make_assignment(rs_counter,
                                          course,
                                          room,
                                          time,
                                          "room"
                                          )
                        GD['S'][rs_counter][course]['CourseAssigned'] = True

                    else:
                        # Exit with message
                        H.help(2, course, instructor, room,
                               course_name, course_section)
            rs_counter += 1

        H.say("INFO", "Done, generated ", rs_counter, " solutions.")

    # Method to check feasibility of a solution
    # Might be able to skip this one if assignments are made as feasible
    @staticmethod
    def check_feasibility(hash_key, entry):
        H.say("DBG", "Checking feasibility...")
        for c in GD[hash_key][entry]:
            print(c)

    # Fitness function
    @staticmethod
    def fitness():
        """
        Method for evaluating the fitness of a given solution
        creates GD['F'] dict with the number of the solution as the key
        and the fitness score as a value, this makes it easy to traverse
        the solutions based on fitness later

        Scratch pad of ideas
        --------------------
        Fitness parameter hash details (could have multiple ways to configure)
        - professor proximity of chosen room to department
        - course proximity of chosen room to department
        - what days professor teaches
        - penalty for time of day, but a light penalty
        - class/prereq
        - class/coreg
        - wasted capacity in rooms

        - degree progression (need 2 spreadsheets that don't exist)
          first one has class/prereq (this means you can teach)
          another one has class/coreq
        - number of classes taught by professor (hard constraint)
        - no room/date/time/instructor conflicts (depends on how detailed
          the solution generator is)
        - professor workload (like how many people a class has,
          how many courses professor teaches, etc)

        Other ideas:
        - departure from a previous schedule/solution?
        - TODO - keep track of penalty metrics, a way to tell the user which
          penalties are being imposed the most? Might help tailor constraints
          with that info
        :return:
        """
        H.say("LOG", "Evaluating fitness...")
        total_fitness = 0
        high_fitness = 0
        high_fitness_index = 0
        for s in GD['S']:
            score = GD['HIGH_SCORE']
            for c in GD['S'][s]:
                # set some vars that might get used multiple times
                if len(GD['S'][s][c]['Facility ID']) == 1:
                    room = GD['S'][s][c]['Facility ID'][0]
                else:
                    room = GD['S'][s][c]['Facility ID']
                capacity = GD['S'][s][c]['Enrollment Cap'][0]

                # instructor proximity check = 'Instructor Proximity'
                if GD['S'][s][c]['Instructor Building'] \
                        != GD['S'][s][c]['Building']:
                    penalty = GD['FC']['Instructor Proximity']['Penalty']
                    score -= int(penalty)

                # course proximity = 'Room Proximity'
                # TODO: fix this, Unit is list, building string, values
                # won't equal anyway
                if GD['S'][s][c]['Unit'] != GD['S'][s][c]['Building']:
                    penalty = GD['FC']['Room Proximity']['Penalty']
                    score -= int(penalty)

                # time of day = 'Time of day'
                if 'Start Time' not in GD['S'][s][c]:
                    print("DBG TODO REMOVE")
                start_time = H.get_time(GD['S'][s][c]['Start Time'])
                if start_time < 900 or start_time > 1700:
                    penalty = GD['FC']['Room Proximity']['Penalty']
                    score -= int(penalty)

                # class taught in same semester as prereq = 'Prereq'

                # wasted capacity in rooms = 'Wasted Capacity'
                room_capacity = GD['RC'][room]['Capacity']
                room_util = (1 - (int(capacity)/int(room_capacity)))*100
                # kill the solution if the room isn't big enough
                if room_util > 100:
                    score = 0
                # TODO: Also kill solutions that waste way too much
#                if room_util < 5:
#                    score = 0
                else:
                    if room_util > GD['ROOM_CAPACITY_WASTE_THRESHOLD_PCT']:
                        penalty = GD['FC']['Wasted Capacity']['Penalty']
                        score -= int(penalty)

            # instructor days taught = 'Instructor Days Taught'
            # Simple version of check is to just count number of days
            # instructed and add a penalty for each of them
#            for i in GD['I']:

            # instructor workload = 'Instructor Workload'
            # count total number of students taught
            workload = 0

            H.say("VERBOSE", "Score for solution ", s, ": ", score)
            # Store the key of the solution and it's fitness score on the
            # 'F' dict so that they can be pulled off in sorted order
            GD['F'][s]['fitness'] = score
            total_fitness += score
            if score > high_fitness:
                high_fitness = max(score, high_fitness)
                high_fitness_index = s
        avg_fitness = round(total_fitness / len(GD['S']), 2)
        GD['HIGH_FITNESS_INDEX'] = high_fitness_index
        H.say("DBG", "HFI: ", GD['HIGH_FITNESS_INDEX'])

        H.say("INFO", "Average fitness: ", avg_fitness,
              " \n                 High: ", high_fitness)

    # Crossover
    @staticmethod
    def crossover():
        """
        Method to implement the population crossover. Take each solution on
        the S_COPY dict and create a child from them.
        Actually, let's create 2 children per pair so that the population
        remains stable at it's max value

        Techniques:
        - swap a single random element between randomly selected parents

        Notes:
        - default: instructor will not be swapped, assume that the mapping
          between course/instructor is not changeable
        - an interesting idea might be to enable different types of techniques
          within the same optimization. So, RANDOM_SINGLE for a while, then
          switch it to RANDOM_DOUBLE for the remainder
        :return:
        """
        # parameter-ize the technique so that it's easily changeable
        ct = GD['CROSSOVER_TYPE']
        H.say("LOG", "Performing ", ct, " crossover...")
        crossover_index = 0
        # TODO: why is this always number I expect + 1?
        # num_solutions = len(GD['S_COPY'])
        num_solutions = GD['POPULATION']
        num_passes = num_solutions / 4
        pass_num = 1

        # Pull each solution from S_COPY and pair it with another as parents.
        # If only one element remains on S_COPY, store it directly, maybe it
        # will get to breed in the next iteration
        while pass_num <= num_passes:
            H.say("VERBOSE", "Pass: ", pass_num)
            p1 = H.get_random_number('S_COPY')
            p2 = H.get_random_number('S_COPY')
            while p1 == p2:
                p2 = H.get_random_number('S_COPY')

            # store parents onto solution dict and remove them
            # from S_COPY so they won't be selected again
            H.copy_solution(p1, crossover_index, 'S_COPY', 'S')
            crossover_index += 1
            H.copy_solution(p2, crossover_index, 'S_COPY', 'S')
            crossover_index += 1

            # Create child 1 solution - p1 is the "dominant" parent
            # instructors are always the same, don't swap if the room
            # or time is fixed by constraint.
            H.copy_solution(p1, crossover_index, 'S_COPY', 'S')
            p1_course = H.get_random_course('S_COPY', p1)
            p2_course = H.get_random_course('S_COPY', p2)
            H.say("VERBOSE", " swapping rooms for ",
                  p1_course, ",", p2_course)
            H.swap_elements(crossover_index, p1_course, p2_course,
                            'Facility ID')
            crossover_index += 1

            # Create child 2 solution - p2 is the "dominant" parent.
            H.copy_solution(p2, crossover_index, 'S_COPY', 'S')
            p1_course = H.get_random_course('S_COPY', p1)
            p2_course = H.get_random_course('S_COPY', p2)
            H.say("VERBOSE", " swapping rooms for ",
                  p1_course, ",", p2_course)
            H.swap_elements(crossover_index, p1_course, p2_course,
                            'Facility ID')
            crossover_index += 1

            pass_num += 1
        H.say("VERBOSE", "Done crossover after ", pass_num-1, " passes.")

    # Mutation
    @staticmethod
    def mutate():
        """
        This needs to work on both time and location, so should crossover.
        MUTATION_RATE is a %, so 5% would mutate a total of 5% of elements

        Method #1: want to randomly choose from the entire set of
          solutions elements to mutate, as opposed to uniformly mutating a
          certain percentage of each solution. This way

        Method #2: TODO for each solution, swap the same percentage of elements

        Ideas: what about not mutating the top solution. If we don't, then we
        always preserve it. If mutation them improves a lesser solution, then
        the first top one is no longer the top one and it can then be mutated.
        If a lesser solution never eclipses it, then you've found the best
        possible solution! (same for crossover)
        """
        H.say("LOG", "Mutating the population...")
        ###########
        # Method #1
        ###########
        # Go through each solution and un-assign a percentage of the day/time
        # and room elements randomly.

        # Get the total number of elements so that mutation rate can
        # be tracked. Multiply number of solutions * number of courses
        # per solution * 2 (because we are swapping only 2 possible elements
        width = len(GD['S'])
        height = len(GD['S'][0])
        total_elements = width * height * 2
        num_mutated = 0

        # Perform the un-assignment
        while num_mutated < (GD['MUTATION_RATE']/100) * total_elements:
            random_s = GD['HIGH_FITNESS_INDEX']

            # TODO fix this: preserve the top solution always
            while random_s == GD['HIGH_FITNESS_INDEX']:
                random_s = H.get_random_number('S')

            # get random element and mutate
            random_c = H.get_random_course('S', random_s)
            random_e = H.get_random_course_element()
            # TODO: verify: skip if it was assigned by forced assignment
            if H.check_forced(random_s, random_c, random_e):
                H.say("DBG1", "skipping mutation of forced assignment")
                continue

            # Process the mutation for random element
            original_instructor = \
                GD['S'][random_s][random_c]['Instructor Jan/Dana ID']
            original_room = GD['S'][random_s][random_c]['Facility ID']
            orig_time = GD['S'][random_s][random_c]['Time Slot']
            orig_times = H.get_equivalent_slots(orig_time)
            element = GD['S'][random_s][random_c][random_e]
            H.say("DBG", "mutating ", element, " at s:c ", random_s, ":",
                  random_c)

            # Kludge because sometimes things are a list, sometimes a string
            if isinstance(original_room, list):
                room = original_room[0]
                original_room = original_room[0]
            else:
                room = original_room
            if isinstance(original_instructor, list):
                instructor = original_instructor[0]
                original_instructor = original_instructor[0]
            else:
                instructor = original_instructor

            # Only mutate the room resource in this case.
            if "Facility ID" in random_e:
                r_type = "RT"
                # Try to get a new room at the same time as before.
                room = H.get_resource(random_s,
                                      random_c,
                                      orig_time,
                                      'R',
                                      ""
                                      )
                if room != "":
                    # No need to check before booking, get_resource() does that
                    H.manage_resource(r_type,
                                      random_s,
                                      room,
                                      orig_times,
                                      "book"
                                      )
                    H.say("DBG", "mutated rooms: ", original_room,
                          "->", room, ". Freeing original room...")
                    H.manage_resource(r_type,
                                      random_s,
                                      original_room,
                                      orig_times,
                                      "free"
                                      )
                    num_mutated += 1
                else:
                    H.say("DBG", "Skipping element: ", element,
                          ", not able to find another room at same time")
                    continue

            # To mutate time slot, have to find one where both instructor
            # and room are free.
            elif "Time Slot" in random_e:
                r_type = "IT"
                time_valid = False
                time_try = 0
                max_tries = len(GD['T'])
                # Iterate over available times to try and find one that works
                # for both instructor and room.
                while not time_valid:
                    time_valid = True
                    new_time = H.get_random_element("T", random_c)
                    new_times = H.get_equivalent_slots(new_time)
                    H.say("DBG", "trying time ", new_time,
                          " for instructor ", instructor,
                          ", time_try = ", time_try)
                    # Try for the instructor.
                    i_flag = H.manage_resource(r_type,
                                               random_s,
                                               instructor,
                                               new_times,
                                               "check"
                                               )
                    if not i_flag:
                        time_valid = False  # Doesn't work, will try next time
                    # Works for instructor.
                    else:
                        # Try for room.
                        H.say("DBG", "trying time ", new_time,
                              " for room ", room,
                              ", time_try = ", time_try)
                        r_flag = H.manage_resource("RT",
                                                   random_s,
                                                   room,
                                                   new_times,
                                                   "check"
                                                   )
                        # Doesn't work for room, try next time for both
                        if not r_flag:
                            time_valid = False
                        # Success, found new time slot, book 'em!
                        else:
                            H.manage_resource(r_type,
                                              random_s,
                                              instructor,
                                              new_times,
                                              "book"
                                              )
                            H.manage_resource("RT",
                                              random_s,
                                              room,
                                              new_times,
                                              "book"
                                              )
                            H.say("DBG", "mutated times: ", orig_time,
                                  "->", new_time, ". Freeing instructor ",
                                  "and room at original time...")
                            # Free both room and instructor from old time.
                            H.manage_resource(r_type,
                                              random_s,
                                              instructor,
                                              orig_times,
                                              "free"
                                              )
                            H.manage_resource("RT",
                                              random_s,
                                              room,
                                              orig_times,
                                              "free"
                                              )
                            num_mutated += 1
                            break
                    time_try += 1
                    if time_try == max_tries:
                        H.say("DBG", "Skipping time swap, could not find ",
                              "time that works for both ", original_room,
                              " and ", original_instructor)
                        break
            else:
                H.say("ERROR", "Unrecognized type code ", random_e)

        # Report stats/return to main loop
        H.say("LOG", "Mutated ", num_mutated,
              " elements of the solution")

    # Culling
    @staticmethod
    def cull_population():
        """
        # Culling method, this will take the top solutions one by one
        and copy them into S_COPY dict in sorted order until the max number of
        solutions to preserve have been copied
        :return:
        """
        preserved_count = 0
        H.say("LOG", "Culling population...")
        # Get each fitness score and solution key
        for f in GD['F']:
            H.say("VERBOSE", "s: ", f, " fitness: ", GD['F'][f]['fitness'])
            GD['CD'][f] = GD['F'][f]['fitness']
        for k, v in sorted(
                GD['CD'].items(),
                key=operator.itemgetter(1),
                reverse=True
        ):
            # copy surviving solutions into the copy dict
            if preserved_count <= GD['CULL_SURVIVORS']:
                H.say("DBG", "preserving ", k, ":", preserved_count)
                H.copy_solution(k, preserved_count, 'S', 'S_COPY')
                preserved_count += 1
            # purge all elements from original solutions dict, and also
            # clear the cull and fitness score dictionaries so they will be
            # ready for next iteration
            del GD['S'][k]
            del GD['CD'][k]
            del GD['F'][k]
        H.say("LOG", "Done, preserved ", preserved_count, " of population")

    @staticmethod
    def return_population():
        """
        The big method to print all data for a solution to CSV the old
        fashioned way, without using csv.writer

        :return:
        """
        import sys
        # determine which solutions to output
        solution_count = 0
        # Get each fitness score and solution key, return highest N
        for f in GD['F']:
            GD['CD'][f] = GD['F'][f]['fitness']
        for s, f in sorted(GD['CD'].items(), key=operator.itemgetter(1),
                           reverse=True):
            if solution_count < GD['NUM_SOLUTIONS_TO_RETURN']:
                solution_count += 1

                # set some vars and open the CSV
                file_name = "Solution" + s.__str__() + "_" + f.__str__() + ".csv"
                try:
                    H.say("INFO", "Opening ", file_name, " for write...")
                    fh = open(file_name, 'w')
                except PermissionError as e:
                    H.say("ERROR", "Could not open ", file_name,
                          ", is it open in Excel?",
                          e.strerror()
                          )
                    sys.exit(2)
                except:
                    H.say("ERROR", "Unknown error opening ", file_name)

                # print the header the first time around
                count = 0
                num_elements = len(GD['S_PARAMS'])
                for s_param in GD['S_PARAMS']:
                    count += 1
                    if count == num_elements:
                        end_char = ''
                    else:
                        end_char = ','
                    print(s_param, file=fh, end=end_char)
                print(file=fh)

                # print the data into rows
                for c in GD['S'][s]:
                    count = 0
                    for s_param in GD['S_PARAMS']:
                        count += 1
                        # element = ""
                        if count == num_elements:
                            end_char = ''
                        else:
                            end_char = ','
                        # some elements are stored as lists, some are not
                        if len(GD['S'][s][c][s_param]) == 1:
                            element = GD['S'][s][c][s_param][0]
                        else:
                            element = GD['S'][s][c][s_param]
                        if element.find(',') != -1:
                            element = '"' + element + '"'
                        # print the actual line
                        print(element.strip(), file=fh, end=end_char)
                    print(file=fh)
        H.say("INFO", "Done, returned ", solution_count, " solutions.")

    @staticmethod
    def return_population_by_writer():
        """
        Helper method to return the top n solutions in full CSV output format
        :return:
        """
        import csv

        H.say("INFO", "Returning top ", GD['NUM_SOLUTIONS_TO_RETURN'],
              " solutions...")
        with open('solution.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for c in GD['S'][0]:
                H.say("DBG1", "c: ", c, "c0: ", c[0])
                writer.writerow(c)


#######################################################################
# Main
#######################################################################


class Main:
    print("Running genetic_scheduler...")
    # Process the inputs and build the DBs
    ip = InputProcessor()
    ip.process_input_from_solution()
    ip.process_schedule_constraints()
    ip.process_csv_constraints(GD['COURSE_CONSTRAINTS'], "CC_PARAMS")
    ip.process_csv_constraints(GD['FITNESS_CONSTRAINTS'], "FC_PARAMS")
    ip.process_csv_constraints(GD['ROOM_CONSTRAINTS'], "RC_PARAMS")
    ip.process_csv_constraints(GD['INSTRUCTOR_CONSTRAINTS'], "IC_PARAMS")
    ip.print_databases()
    ip.print_sample_assignments()

    # Initial randomly generated population seed
    population = Population()
    population.generate_random_solutions()
    population.fitness()
    population.return_population()

    # Loop over the population and perform the genetic optimization
    iteration_count = 0
    while iteration_count < GD['NUM_ITERATIONS']:
        H.say("INFO", "Iteration: ", iteration_count)
        population.fitness()
        population.cull_population()
        population.crossover()
        # Don't run mutation on last iteration
        if iteration_count < GD['NUM_ITERATIONS'] - 1:
            # idea: mutate only every nth iteration??
            population.mutate()
        iteration_count += 1
    # End the loop
    H.say("INFO", "Performed ",
          GD['NUM_ITERATIONS'],
          " iterations, returning top ",
          GD['NUM_SOLUTIONS_TO_RETURN'],
          " results..."
          )

    # Up next:
    # - make target around matrix_viewer
    # - improve fitness function (including check_feasible)
    # - work on top solution preservation, culling is messing with order
    # - more crossover/mutation techniques, some research, etc.

    # Finish up and return, run fitness to sort, and return top N
    # ip.print_database_1level('RT')
    # ip.print_database_1level('IT')
    population.fitness()
    #population.return_population()
    H.say("INFO", "Done")

if __name__ == "__Main__":
    Main()
