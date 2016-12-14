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
#
# Questions:
# - strip() not working, and why whitespace in the first place
#
# fixed rooms/schedules - labs, etc where the place/?time fixed
#
# Scratchpad:
# - Ensure all generated solutions are legal, use culling/fitness to kill
#   all illegal children, as opposed to generating only legal children. Use
#   check_legality during fitness testing to accomplish this
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
    POPULATION=12,
    CULL_SURVIVORS=6,
    NUM_ITERATIONS=10,
    NUM_SOLUTIONS_TO_RETURN=3,
    GENE_SWAP_PCT=50,
    CROSSOVER_TYPE="RANDOM_SINGLE",
    MUTATION_RATE=5,
    MUTATION_SEVERITY=10,
    ROOM_CAPACITY_WASTE_THRESHOLD_PCT=25,
    CSV_IN='Data/ScheduleOfClassesSample.csv',
    CSV_NUM_LINES=0,
    CSV_NUM_ERRORS=0,
    COURSE_CONSTRAINTS='Data/CourseConstraints.csv',
    FITNESS_CONSTRAINTS='Data/FitnessConstraints.csv',
    ROOM_CONSTRAINTS='Data/RoomConstraints.csv',
    INSTRUCTOR_CONSTRAINTS='Data/InstructorConstraints.csv',
    HIGH_SCORE=20000,
    INFO_LEVEL=2,  # see Helper.say()
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
    IC_PARAMS=[
               "Instructor Name",
               "Instructor Emplid",
               "Instructor Building",
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
                GD['C'][course_key]['TimeSlotAssigned'] = "false"
                GD['C'][course_key]['RoomAssigned'] = "false"
                GD['C'][course_key]['InstructorAssigned'] = "false"
                # store room information
                if room_key == '' or room_key == ' ':
                    H.say("LOG", "Missing room info from row ", row_num+1)
                    continue
                for r_param in GD['R_PARAMS']:
                    GD['R'][room_key][r_param] = [row[r_param]]
                GD['R'][room_key]['AlreadyAssigned'] = "false"
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
                GD['I'][instructor_key]['AlreadyAssigned'] = "false"
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

        :param args:
        :return:
        """
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
            if level == "VERBOSE" and GD['INFO_LEVEL'] == 2:
                if k != "VERBOSE":
                    print(k, file=GD['LOGFILE'], end=end_char)
                    printed_to_log += 1
            if level == "DBG" and GD['INFO_LEVEL'] >= 3:
                print(k, end=end_char)
                printed_to_terminal += 1
            if level == "DBG1" and GD['INFO_LEVEL'] >= 1:
                print(k, end=end_char)
                printed_to_terminal += 1
            if level == "LOG":
                if k != "LOG":
                    print(k, file=GD['LOGFILE'], end=end_char)
                    printed_to_log += 1
            if level == "ERROR":
                print(k, end=end_char)
            end_char = ''
        if printed_to_terminal > 0:
            print()
        if printed_to_log > 0:
            print(file=GD['LOGFILE'], end='\n')

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
        return random.randrange(0, max_num)

    @staticmethod
    def get_random_course(hash_key, entry):
        """
        method to get a random course from a solution dict
        Designed for use with cull_population
        """
        import random
        counter = 0
        max_num = len(GD[hash_key][entry])
        key_num = random.randrange(0, max_num)
        for course in GD[hash_key][entry]:
            if key_num == counter:
                return course
            else:
                counter += 1
        # Error if we reach this point
        H.say("ERROR", "Unable to find a random course key for ", hash_key)

    #
    @staticmethod
    def get_random_element(key):
        """
        method to randomly get an element off a dict, but get only
        elements that haven't been "gotten" yet.
        Designed for use with generate_random_solutions
        :param key:
        :return: element
        """
        import sys
        counter = 0
        random = H.get_random_number(key)
        e_id = ""  # for error message printing only
        for element_id in GD[key]:
            e_id = element_id
            if counter == random:
                if GD[key][element_id]['AlreadyAssigned'] == "true":
                    GD[key][element_id]['AlreadyAssigned'] = "true"
                    continue
                else:
                    return element_id
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
            e_id, ": ",
            GD[key][e_id]['AlreadyAssigned']
        )
        sys.exit(2)

    @staticmethod
    def check_element_valid():
        element_valid = 0
        if element_valid == 1:
            return

    @staticmethod
    def make_forced_assignment(course, db_type, key):
        """
        Helper method to generate_random_solutions, this one takes a key
        from the GD['C'] courses hash and a type of assignment ('I', 'R', etc)
        and makes a forced assignment if one needs to be made so that it's
        not randomly generated

        :return:
        """
        import sys
        forced = 0
        for cc_key in GD['CC']:
            cc_course = GD['CC'][cc_key]['Course']
            cc_section = GD['CC'][cc_key]['Section']
            c_course = GD['C'][course]['Class Subject + Nbr'][0]
            c_section = GD['C'][course]['*Section'][0]
            if cc_course == c_course and cc_section == c_section:
                forced += 1
                H.say("VERBOSE", "Making forced (", db_type,
                      ") assignment for:\n",
                      c_course, " section ", c_section
                      )
                if db_type == "I":
                    GD['S'][key][course]['Instructor'] \
                        = H.get_id(GD['CC'][cc_key]['Instructor'])
                    GD['C'][course]['InstructorAssigned'] = "true"
                if db_type == "R":
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
                        sys.exit(2)
                    else:
                        GD['S'][key][course]['Room'] \
                            = GD['CC'][cc_key]['Room']
                        GD['C'][course]['RoomAssigned'] = "true"
                # May need to support day/time assignment as well

    @staticmethod
    def get_id(instructor_name):
        try:
            for key in GD['I']:
                H.say("DBG", "key: ", key, " against: ", instructor_name)
                if GD['I'][key]['Instructor Name'][0] == instructor_name:
                    H.say("DBG", "returning: ", key)
                    return key
        except:
            H.say("ERROR", "Trying to get Jan/Dana ID for instructor\n",
                  instructor_name,
                  " but could not find one.")

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
    def generate_random_solutions():
        """
        Method to generate the random seed of solutions
        Solution requirements:
        - all GD['C'][course_key] are assigned
        - all courses have an instructor and a room

        Flow of method:
        - assign all courses into the solution
        - assign an instructor to the course
        - assign them to a room

        :return:
        """
        H.say("INFO", "Generating set of random solutions...")
        # Make assignments randomly unless assignment was already made
        rs_counter = 0
        while rs_counter < GD['POPULATION']:
            # course assignment
            for course in GD['C']:
                H.say("DBG", "Assigning course: ", course)
                for c_param in GD['C_PARAMS']:
                    GD['S'][rs_counter][course][c_param] \
                        = GD['C'][course][c_param]
                # time slot assignment
                if GD['C'][course]['TimeSlotAssigned'] == 'false':
                    time = H.get_random_element('T')
                    for t_key in GD['T'][time]:
                        GD['S'][rs_counter][course][t_key] \
                            = GD['T'][time][t_key]
                    GD['S'][rs_counter][course]['Time Slot'] = time
                # instructor assignment, if not assigned by constraint
                # TODO: have to check if instructor is not already teaching
                # TODO: at that time (like TTh 12:25 overlapping T 1pm)
                H.make_forced_assignment(course, "I", rs_counter)
                if GD['C'][course]['InstructorAssigned'] == 'false':
                    instructor = H.get_random_element('I')
                else:
                    instructor = GD['S'][rs_counter][course]['Instructor']
                for i_key in GD['I'][instructor]:
                    GD['S'][rs_counter][course][i_key] \
                        = GD['I'][instructor][i_key]
                for ic_key in GD['IC'][instructor]:
                    GD['S'][rs_counter][course][ic_key] \
                        = GD['IC'][instructor][ic_key]
                # room assignment, if not assigned by constraint
                # TODO: have to check if room is not already occupied by funky
                # TODO: constraint (like TTh 12:25 overlapping T 1pm)
                H.make_forced_assignment(course, "R", rs_counter)
                if GD['C'][course]['RoomAssigned'] == 'false':
                    room = H.get_random_element('R')
                else:
                    room = GD['S'][rs_counter][course]['Room']
                GD['S'][rs_counter][course]['Facility ID'] \
                    = GD['R'][room]['Facility ID']
                GD['S'][rs_counter][course]['Building'] \
                    = GD['RC'][room]['Building']
                GD['S'][rs_counter][course]['Unit'] \
                    = GD['C'][course]['Unit']
            rs_counter += 1
        # InputProcessor.print_database_2level('S')
        H.say("INFO", "Done, generated ", rs_counter, " solutions.")

    # Method to check feasibility of a solution
    # Might be able to skip this one if assignments are made as feasible
    @staticmethod
    def check_feasibility():
        print("TODO feasible")

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
        :return:
        """
        H.say("LOG", "Evaluating fitness...")
        total_fitness = 0
        for s in GD['S']:
            score = GD['HIGH_SCORE']
            for c in GD['S'][s]:
                # set some vars that might get used multiple times
                room = GD['S'][s][c]['Facility ID'][0]
                capacity = GD['S'][s][c]['Enrollment Cap'][0]

                # instructor proximity check = 'Instructor Proximity'
                if GD['S'][s][c]['Instructor Building'] \
                        != GD['S'][s][c]['Building']:
                    penalty = GD['FC']['Instructor Proximity']['Penalty']
                    score -= int(penalty)
                # course proximity = 'Room Proximity'
                if GD['S'][s][c]['Unit'] != GD['S'][s][c]['Building']:
                    penalty = GD['FC']['Room Proximity']['Penalty']
                    score -= int(penalty)
                # instructor days taught = 'Instructor Days Taught'
                # time of day = 'Time of day'
                if '08:00' in GD['S'][s][c]['Start Time']:
                    H.say("DBG1", "docking for TOD")
                    penalty = GD['FC']['Room Proximity']['Penalty']
                    score -= int(penalty)
                # class taught in same semester as prereq = 'Prereq'
                # wasted capacity in rooms = 'Wasted Capacity', kill the
                # solution if the room isn't big enough
                room_capacity = GD['RC'][room]['Capacity']
                room_waste = (1 - (int(capacity)/int(room_capacity)))*100
                if room_waste > 100:
                    score = 0
                else:
                    if room_waste > GD['ROOM_CAPACITY_WASTE_THRESHOLD_PCT']:
                        penalty = GD['FC']['Wasted Capacity']['Penalty']
                        score -= int(penalty)
                # professor workload = 'Instructor Workload'
            H.say("VERBOSE", "Score for solution ", s, ": ", score)
            # Store the key of the solution and it's fitness score on the
            # 'F' dict so that they can be pulled off in sorted order
            GD['F'][s]['fitness'] = score
            total_fitness += score
        avg_fitness = total_fitness / len(GD['S'])
        H.say("INFO", "Average fitness: ", avg_fitness)

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
        H.say("LOG", "Performing ", type, " crossover...")
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

            # create child 1 solution - p1 is the "dominant" parent
            # instructors are always the same
            H.copy_solution(p1, crossover_index, 'S_COPY', 'S')
            p1_course = H.get_random_course('S_COPY', p1)
            p2_course = H.get_random_course('S_COPY', p2)
            H.say("VERBOSE", " swapping rooms for ",
                  p1_course, ",", p2_course)
            GD['S'][crossover_index][p1_course]['Facility ID'] \
                = GD['S'][crossover_index][p2_course]['Facility ID']
            crossover_index += 1

            # create child 2 solution - p2 is the "dominant" parent
            # instructors are always the same
            H.copy_solution(p2, crossover_index, 'S_COPY', 'S')
            p1_course = H.get_random_course('S_COPY', p1)
            p2_course = H.get_random_course('S_COPY', p2)
            H.say("VERBOSE", " swapping rooms for ",
                  p1_course, ",", p2_course)
            GD['S'][crossover_index][p2_course]['Facility ID'] \
                = GD['S'][crossover_index][p1_course]['Facility ID']
            crossover_index += 1

            # store parents onto solution dict and remove them
            # from S_COPY so they won't be selected again
            H.copy_solution(p1, crossover_index, 'S_COPY', 'S')
            crossover_index += 1
            H.copy_solution(p2, crossover_index, 'S_COPY', 'S')
            crossover_index += 1
            pass_num += 1
        H.say("VERBOSE", "Done crossover after ", pass_num-1, " passes.")

    # Mutation
    @staticmethod
    def mutate():
        H.say("DBG", "TODO mutate, perhaps change day/times")

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
    # TODO: format of this method is corrupted, extra whitespace all over
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
                          ", is it open in Excel?")
                    sys.exit(2)
                except:
                    H.say("ERROR", "Unknown error opening ", file_name)

                # print the header the first time around
                for s_param in GD['S_PARAMS']:
                    print(s_param, file=fh, end=',')
                print(file=fh)

                # print the data into rows
                for c in GD['S'][s]:
                    for s_param in GD['S_PARAMS']:
                        # some elements are stored as lists, some are not
                        if len(GD['S'][s][c][s_param]) == 1:
                            print('"', GD['S'][s][c][s_param][0],
                                  '"', file=fh, end=',')
                        else:
                            print('"', GD['S'][s][c][s_param],
                                  '"', file=fh, end=',')
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

    # Loop over the population and perform the genetic optimization
    iteration_count = 0
    while iteration_count < GD['NUM_ITERATIONS']:
        H.say("INFO", "Iteration: ", iteration_count)
        population.fitness()
        population.cull_population()
        population.crossover()
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
    # - fix return_population output
    # - improve fitness function (including check_feasible)
    # - mutation, at least have crossover change day/time too

    # Finish up and return, run fitness to sort, and return top N
    population.fitness()
    population.return_population()
    H.say("INFO", "Done")

if __name__ == "__Main__":
    Main()
