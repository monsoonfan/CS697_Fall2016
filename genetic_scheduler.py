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
#
#
#######################################################################
# Imports
#######################################################################


#######################################################################
# Input processing class
#######################################################################
class InputProcessor:
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
        P = Professor catalog
           - prof names
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
        import collections
        print("Initializing data structures...")
        # Global Dictionary initialized by constructor
        self.GD = dict(
            NUM_ITERATIONS=1000,
            GENE_SWAP_PCT=50,
            MUTATION_RATE=5,
            MUTATION_SEVERITY=10,
            CSV_IN='ScheduleOfClassesSample.csv',
            CSV_NUM_LINES=0,
            CSV_NUM_ERRORS=0,
            DB_PARAMS=["C", "I", "R", "S"],
            C=collections.defaultdict(lambda: collections.defaultdict()),
            I=collections.defaultdict(lambda: collections.defaultdict()),
            R=collections.defaultdict(lambda: collections.defaultdict()),
            S=collections.defaultdict(lambda: collections.defaultdict()),
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
                      "Wait List Cap",  # TODO: bad hack here
                      ]
        )

    # Process the input and build out the data structures
    def process_input_from_solution(self):
        """
        Temporary method to build data structures based on sample solution,
        not sample input.
        :return: none
        """
        import csv
        print("Processing input ...")
        row_num = 0
        # Iterate over the CSV and extract the information
        with open(self.GD['CSV_IN'], newline='', encoding='utf-8') as csv_in:
            csv_data = csv.DictReader(csv_in, delimiter=',', quotechar='"')
            for row in csv_data:
                self.GD['CSV_NUM_LINES'] += 1
                course_key = row['*Course ID'] + "_" + row['*Section']
                instructor_key = row['Instructor Jan/Dana ID']
                room_key = row['Facility ID']
                # Now store course information into DB, can't do this
                # in a loop for each set of params because the id_num
                # will be different for courses/rooms/profs
                for c_param in self.GD['C_PARAMS']:
                    self.GD['C'][course_key][c_param] = [row[c_param]]
                # store room information
                for r_param in self.GD['R_PARAMS']:
                    self.GD['R'][room_key][r_param] = [row[r_param]]
                # store instructor information
                for i_param in self.GD['I_PARAMS']:
                    self.GD['I'][instructor_key][i_param] = [row[i_param]]
                row_num += 1
        print("Done preprocessing, found",
              self.GD['CSV_NUM_LINES'], "lines, ",
              self.GD['CSV_NUM_ERRORS'], "errors")

    # Method for printing a single database/dict
    def print_database(self, param):
        print("Database: ", param)
        for k in self.GD[param]:
            for v in self.GD[param][k]:
                print("[", k, "]: ", v)

    # Method for iterating over each the databases and printing them
    def print_databases(self):
        print("All databases: ")
        for param in self.GD['DB_PARAMS']:
            print(">", param)
            self.print_database(param)

    # Method to generate the random seed of solutions

#######################################################################
# Population processing class
#######################################################################
class Population:
    def generate_random_solutions(self):
        print("Generating set of random solutions...")
        print("TODO")

    # Method to check feasibility of a solution
    def check_feasibility(self):
        print("TODO")

    # Fitness function
    def fitness(self):
        print("TODO")

    # Mutation
    def mutate(self):
        print("TODO")

    # Crossover method
    def crossover(self):
        print("TODO")

    # Culling method
    def cull_population(self):
        print("TODO")

    # Helper method to sort the population
    def sort_population(self):
        print("TODO")

    # Helper method to return the population in CSV format
    def return_population(self):
        print("TODO")


#######################################################################
# Main
#######################################################################


class Main:
    print("Running genetic_scheduler...")
    ip = InputProcessor()
    # Process the input and build the DBs
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
    print("Done")

if __name__ == "__Main__":
    Main()
