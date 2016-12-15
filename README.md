# CS697_Fall2016
GeneticScheduler
------------------------------------
Description of program control flow
------------------------------------

--------------------------------------------
Data structures, and how they are populated
--------------------------------------------
There is a global dictionary called GD, all global data is stored on it. There
are several dictionaries on GD that store all the data and constraints for the
program. Following is a description of each structure.

Parameter dictionaries:
-----------------------
- This is where you tell the CSV parser what parameters to look
for within a CSV file and store in the constraints dictionaries.
Enumeration of types of parameters to specify:

C = Course parameters
I = Instructor
R = Room
T = Time/day slot
S = Solutions         (note: for solutions, these are output parameters, not input, so
                             this is where you can control which parameters are sent
			     to CSV during solution output

GD['*_PARAMS'] -> 
                  <param>
		 
Example (will store "Facility ID" and "Wait List Cap" into GD['R'] dictionary:
		  GD['R_PARAMS']=["Facility ID",
		                  "Wait List Cap",
				  ]

Constraints dictionaries:
-------------------------
- These will store the constraints specified by the parameters
above. They are kept in different dictionaries by category for clarity. Here's an
enumeration of the possible parameters, along with the CSV file that is read to
populate them (all CSVs are read from "Data/" dir):

CC = CourseConstraints.csv     - this is where you'll store constraints for each course
FC = FitnessConstraints.csv    - specify constraints for the fitness function here
RC = RoomConstraints.csv       - constraints for the room such as capacity and
     			       	 labs taught go in here. The building the room
				 is in is also stored here and is needed for the
				 fitness function
IC = InstructorConstraints.csv - specify the constraints for the instructor here as
     			       	 per the example on github. These constraints are
				 used during fitness

Mapping of structures:
GD['RC'] ->
            [room_key] ->                 (this is an integer)
	                  <param> = value

Solutions dictionaries:
-------------------------
- these are where the data for the population of solutions is stored. There are
two of them:

GD['S']      = this is the big dictionary used to store the population of
               solutions. The CSV output of final solutions happens from this dictionary
GD['S_COPY'] = used as a temporary dictionary to copy data into DB manipulation, it
	       has the same keys/parameters as GD['S']

- Each solution is comprised of a dictionary of courses, where each course has
  room, day/time, and instructor assignments, along with many other attributes
  as dictated by S_PARAMS.
- I won't enumerate the parameters here (see S_PARAMS dictionary), rather, here's
  a mapping of the structure itself:

GD['S'] ->
           [solution_key] ->                 ( this is an integer)
	   
	                     [course_key] -> ( this is a number comprised of
			                       '*Course ID' and '*Section' fields from the
					       "ScheduleOfClassesSample.csv"
					       
			                     <s_param>

Example - this would assign 069-224 as the room for "SOFTWARE ARCHITECTURE",
          Section #1 for the 4th solution on the 'S' dictionary:
GD['S'][3][10912_1]['Facility ID'] = "069-224"
