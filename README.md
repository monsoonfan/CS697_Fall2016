# CS697_Fall2016 - GeneticScheduler
## Description of program control flow
The flow of the program is typical of a genetic algorithm. For details, look
at the main method. It's object oriented and written for clarity. You'll see
3 classes:

Num | Name | Purpose
--- | --- | ---
1 | InputProcessor |takes care of any input processing
2 | H | helper methods, the name "H" keeps lines of code shorter
3 | Population | methods for the specific tasks related to the population

For details about each method, please refer to the docstring comments.

### Variables
These are the main configurable varaibles to dictate program operations. They all exist
inside the 'GD' global dictionary. There are other variables in that dictionary that are
there for internal program operation only.

Variable | Description
--- | --- | ---
POPULATION | Number of solutions in the population, ust be 4 or greater. Testing was done with sizes up to 100 solutions. Recommend an even number.
CULL_SURVIVORS | Make this number exactly half of POPULATION. To be deprecated.
NUM_ITERATIONS | Will give this many iterations of crossover, and one less of mutations.
HIGH_SCORE | Determines the starting score of each solution before fitness() asseses penalties
INFO_LEVEL | Configures the level of output detail. 1 is minimum, 2 will be verbose, 3 will give DBG level of detail.
MUTATION_RATE | This is a percentage, and mutation will affect this percent of the elements of the total population. With default setting of 5, that means 5% of the population's room or day/time assignements will get mutated.
ROOM_CAPACITY_WASTE_THRESHOLD_PCT | If a room is utilized below this amount, a penalty will be assesed during fitness(). Meaning, a class with a cap of 10 students in a room with a cap of 100 would get a penalty with a setting of 10% or higher.
UNIMPLEMENTED_BELOW_THIS_DUMMY_VAR | All variables below this in the dictionary either are not implemented, or are for internal use only.

### Data structures, and how they are populated
There is a global dictionary called GD, all global data is stored on it. There
are several dictionaries on GD that store all the data and constraints for the
program. Following is a description of each structure.

#### Parameter dictionaries:
This is where you tell the CSV parser what parameters to look
for within a CSV file and store in the constraints dictionaries.
Enumeration of types of parameters to specify:

Key | Description | Notes
--- | --- | ---
C | Course parameters | First key is comprised of '*Course ID' and '*Section' fields from the "ScheduleOfClassesSample.csv": 10121_1
I | Instructor | First key is Jan user ID: rmr5
R | Room | First keys is like: 069-106
T | Time/day slot | First key is like: MWF_8:00_8:50, called "time_slot" within the code
S | Solutions | For solutions, these are output parameters, not input, so this is where you can control which parameters are sent to CSV during solution output

GD['*_PARAMS'] -> [param] = value
		 
##### Example (will store "Facility ID" and "Wait List Cap" into GD['R'] dictionary)

> GD['R_PARAMS']=["Facility ID","Wait List Cap"]


#### Constraints dictionaries:
These will store the constraints specified by the parameters
above. They are kept in different dictionaries by category for clarity. Here's an
enumeration of the possible parameters, along with the CSV file that is read to
populate them (all CSVs are read from "Data/" dir)

Key | File | Description
--- | --- | ---
CC | CourseConstraints.csv | this is where you'll store constraints for each course
FC | FitnessConstraints.csv | specify constraints for the fitness function here
RC | RoomConstraints.csv |constraints for the room such as capacity and labs taught go in here. The building the room is in is also stored here and is needed for the fitness function
IC | InstructorConstraints.csv | specify the constraints for the instructor here as per the example on github. These constraints are used during fitness

##### Example mapping of constraints dictionaries:
GD['RC'] -> [room_key] -> [param] = value

#### Solutions dictionaries:
these are where the data for the population of solutions is stored. There are
two of them:

GD['S'] = this is the big dictionary used to store the population of solutions. The CSV output of final solutions happens from this dictionary

GD['S_COPY'] = used as a temporary dictionary to copy data into DB manipulation, it has the same keys/parameters as GD['S']

- Each solution is comprised of a dictionary of courses, where each course has
  room, day/time, and instructor assignments, along with many other attributes
  as dictated by S_PARAMS.
- I won't enumerate the parameters here (see S_PARAMS dictionary), rather, here's
  a mapping of the structure itself:

GD['S'] -> [solution_key] -> [course_key] -> <s_param> = value

> solution_key: ( this is an integer)                                  course_key: ( this is a number comprised of '*Course ID' and '*Section' fields from the "ScheduleOfClassesSample.csv")

##### Example - this would assign 069-224 as the room for "SOFTWARE ARCHITECTURE", Section #1 for the 4th solution on the 'S' dictionary:
	  
GD['S'][3][10912_1]['Facility ID'] = "069-224"

#### Special dictionary:
generate_random_solutions, crossover, and mutation will check these

Key | Notes
--- | ---
RT | this one is basically the resource calendar for rooms at each enumerated time slot
IT | same as RT for instructors
   | RT[room_key] -> [time_key] = "busy" or "free"
F | keeps track of fitness scores
  | F[solution_number] -> ['fitness'] = score
CD | Stores the sorted solution keys
