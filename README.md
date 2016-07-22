# DataReduction

Some scripts to perform data reduction on MUSE cubes

** rowcol.py: from Johan. To fix the background levels to zero by subtracting the median value calculated both on columns and rows in an moving window of 50 A. Uses parallelization.

** analysis.py: takes a list of cubes and produces narrow bands and pdfs to quickly check the reduced data from GALAXY CLUSTERS

** update_version.py: updated the cube's header with a version number

** measure_psf.py: takes a cube and a list of stars and measures the psf in several wavelenght planes
