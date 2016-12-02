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
# Development began November 2016
#
# Github:
#
# Issues:
# Online classes have no room, now to deal with
#
# Questions:
# style - global dictionary of value, or pass values to each method
#         code seems more concise and easier to read/manipulate with
#         global dict. One place to edit all values, don't have to hunt
#         for params
#
# fixed rooms/schedules - labs, etc where the place/?time fixed
#
#######################################################################
# Imports
#######################################################################
import collections

#######################################################################
# Global variables
#######################################################################
GD = dict(
    POPULATION=100,
    NUM_ITERATIONS=100,
    NUM_SOLUTIONS_TO_TRY=2,
    NUM_SOLUTIONS_TO_RETURN=1,
    GENE_SWAP_PCT=50,
    MUTATION_RATE=5,
    MUTATION_SEVERITY=10,
    CSV_IN='ScheduleOfClassesSample.csv',
    CSV_NUM_LINES=0,
    CSV_NUM_ERRORS=0,
    INFO_LEVEL=1,  # see Helper.say()
    LOGFILE=open('run.log','w'),
    DB_PARAMS=["C", "I", "R", "S"],
    C=collections.defaultdict(lambda: collections.defaultdict()),
    I=collections.defaultdict(lambda: collections.defaultdict()),
    R=collections.defaultdict(lambda: collections.defaultdict()),
    T=collections.defaultdict(lambda: collections.defaultdict()),
    S=collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict()
    )),
    C_PARAMS=["Class Nbr",
              "*Section",
              "Class Description",
              "Enrollment Cap",
              "Class Subject + Nbr",
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
              ]
)

# Time and day slot hash - should this info be room based?
# Or even course based, like labs will have diff meeting time/date
# num - days
#     - time
#     - already_taken
#     - details (like meets on M/T/.../F

# Hash for instructors can be simple:
# above info plus:
#     - building_of_office
#     - courses taught hash

# Fitness parameter hash details (could have multiple ways to configure)
#     - professor proximity of chosen room to department
#     - course proximity of chosen room to department
#     - what days professor is teach
#     - penalty for time of day, but a light penalty
#     - class/prereq
#     - class/coreg
#
#     - degree progression (need 2 spreadsheets that don't exist)
#       first one has class/prereq (this means you can teach)
#       another one has class/coreq
#     - number of classes taught by professor (hard constraint)
#     - no room/date/time/instructor conflicts (depends on how detailed
#                                               the solution generator is)
#     - professor workload (like how many people a class has, but not now)


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
        S = Solutions
           - fitness of each solution
           - problem_solution

        """
        H.say("INFO", "Initializing data structures...")

    # Process the input and build out the data structures
    def process_input_from_solution(self):
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
                    H.say("LOG","Missing room info from row ", row_num + 1)
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

    # Method for printing a single database/dict
    def print_database(self, param):
        H.say("LOG", "Database: ", param)
        for k1 in GD[param]:
            for k2 in GD[param][k1]:
                H.say("LOG", "[", k1, "][", k2, "]:", GD[param][k1][k2])

    # Method for iterating over each the databases and printing them
    def print_databases(self):
        H.say("INFO","All databases: ")
        for param in GD['DB_PARAMS']:
            H.say("LOG", ">", param)
            self.print_database(param)


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
        2 = Turn on VERBOSE messages to the prompt
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
            if level == "VERBOSE" and GD['INFO_LEVEL'] >= 2:
                if k != "VERBOSE":
                    print(k, end=end_char)
                    printed_to_terminal += 1
            if level == "DBG" and GD['INFO_LEVEL'] >= 3:
                print(k, end=end_char)
                printed_to_terminal += 1
            if level == "LOG":
                if k != "LOG":
                    print(k, file=GD['LOGFILE'], end=end_char)
                    printed_to_log += 1
            end_char = ''
        if printed_to_terminal > 0:
            print()
        if printed_to_log > 0:
            print(file=GD['LOGFILE'], end='\n')

    @staticmethod
    def get_random_number(GD_hash_key):
        """
        method to generate a random number that will be between 0 and
        the length of the hash that we will use the number to pull an
        element from
        :param GD_hash_key:
        :return random_number:
        """
        import random
        max_num = len(GD[GD_hash_key])
        return random.randrange(0, max_num)

    #
    @staticmethod
    def get_random_element(key):
        """
        method to randomly get an element off a hash, but get only
        elements that haven't been "gotten" yet
        :param key:
        :return: element
        """
        counter = 0
        random = H.get_random_number(key)
        element = ""
        for element_id in GD[key]:
            counter += 1
            if counter == random:
                if key == "I":
                    element = GD[key][element_id]['Instructor Jan/Dana ID']
                if key == "R":
                    element = GD[key][element_id]['Facility ID']
        return element

    @staticmethod
    def check_element_valid():
        element_valid = 0
        if element_valid == 1:
            return


#######################################################################
# Population processing class
#######################################################################
class Population:
    global GD

    def generate_random_solutions(self):
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
        rs_counter = 0
        while rs_counter < GD['NUM_SOLUTIONS_TO_TRY']:
            # course assignment
            for course in GD['C']:
                H.say("VERBOSE", "Assigning course: ", course)
                GD['S'][rs_counter][course]['Class Subject + Nbr'] \
                    = GD['C'][course]['Class Subject + Nbr']
                GD['S'][rs_counter][course]['Class Nbr'] \
                    = GD['C'][course]['Class Nbr']
                GD['S'][rs_counter][course]['*Section'] \
                    = GD['C'][course]['*Section']
                # instructor assignment
                GD['S'][rs_counter][course]['Instructor'] \
                    = H.get_random_element('I')
                # room assignment
                GD['S'][rs_counter][course]['Facility ID'] \
                    = H.get_random_element('R')
            rs_counter += 1

    # Method to check feasibility of a solution
    def check_feasibility(self):
        print("TODO feasible")

    # Fitness function
    def fitness(self):
        print("Evaluating fitness...")
        # Ideas for checking fitness:
        # Create a hash (even a mutating one?) that has the lookup
        # of values for the function


    # Crossover method
    def crossover(self):
        print("TODO crossover")

    # Mutation
    def mutate(self):
        print("TODO mutate")

    # Culling method
    def cull_population(self):
        print("TODO cull")

    # Helper method to sort the population
    def sort_population(self):
        print("TODO sort")

    # Helper method to return the population in CSV format
    def return_population(self):
        print("Returning top", GD['NUM_SOLUTIONS_TO_RETURN'], "solutions...")
        for s in GD['S']:
            for c in GD['S'][s]:
                H.say("VERBOSE", "C:", GD['S'][s][c]['Class Subject + Nbr'],
                      GD['S'][s][c]['*Section'],
                      " ", "I:", GD['S'][s][c]['Instructor'],
                      " ", "R:", GD['S'][s][c]['Facility ID']
                      )


#######################################################################
# Main
#######################################################################


class Main:
    print("Running genetic_scheduler...")
    # Process the input and build the DBs
    ip = InputProcessor()
    ip.process_input_from_solution()
    ip.print_databases()

    # Initial randomly generated population seed, check
    population = Population()
    population.generate_random_solutions()
    population.fitness()
    population.sort_population()
    population.cull_population()
    population.crossover()
    population.mutate()

    # Finish up and return
    population.sort_population()
    population.return_population()
    H.say("INFO", "Done")

if __name__ == "__Main__":
    Main()
