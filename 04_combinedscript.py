# ==================================================================================================================

# DISSERTATION
# SECTION 04: COMBINED SCRIPT
#   This script executes each of the components 01, 01C & 02 in sequence. 
# Date created: 2023-08-16
# Author: J Post

# ==================================================================================================================


from globals import *       # Imports the filepaths defined in globals.py

script04_start = time.time()

with open("01_preparefiles.py") as f:
    exec(f.read())

with open("01c_pythonsubstitution.py") as f:
    exec(f.read())

with open("02_pythonprocesses.py") as f:
    exec(f.read())

print("Combined script process complete.")
timestamp(script04_start)


# buffer_poly_state.plot()
# plt.show()