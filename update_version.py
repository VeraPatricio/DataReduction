from mpdaf.obj import Cube
import os
import shutil
import datetime
import argparse

now = datetime.datetime.now()
date = now.strftime("%Y-%m-%d")

def update_cube_header(cube,version,user=None,email=None):
	""" Sort of a poors man git. It adds/updates the version in the cube
	and writes down the corresponding changes in the README.
	Parameters:
	-----------
	cube:	mpdaf.obj.cube
		Cube to be versioned
	version:	float
		new version number
	user: string
		user making the changes (default V.Patricio)
	"""
	## Open cube 
	c = Cube(cube)
	
	## Check if version already exists. If not, add it
	#try: 
	#	print('Updating old version')
	#	c.primary_header['VERSION'] = version
	#	c.primary_header['VERSDATE'] = date
	#	if user != None:
	#		c.primary_header['VERSBY'] = user
	#	else: 
	#		c.primary_header['VERSBY'] = 'VPatricio'
			
	c.primary_header.insert(-1,card=('VERSION',version,'Reduction Version'))
	c.primary_header.insert(-1,card=('VERSDATE',date,'Version created in'))
	if user != None:
		c.primary_header.insert(-1,card=('VERSBY',user,email))
	else:
		c.primary_header.insert(-1,card=('VERSBY','VPatricio','vera.patricio@univ-lyon1.fr'))
	c.write(cube)
	
if __name__ == "__main__":

        parser = argparse.ArgumentParser()
        parser.add_argument("cube", type=str, help='Cube to be versioned')
        parser.add_argument("version",type=float, help = 'new version number')
        parser.add_argument("readme", type=str, help = 'path to the README with the details of the scibasic/scipost steps')
        parser.add_argument("--user", help = 'Name if the person modifying the cube is not Vera :)')
        parser.add_argument("--email", help = 'email if the person modifying the cube is not Vera :)')
        args = parser.parse_args()

	if len(vars(args)) < 3:

                print 'Missing argument'
                print 'Usage: python update_version.py cube version README --user --email'
                sys.exit()

	## Store old readme, just in case
        dir = '.Readme_Backups/'
        if os.path.isdir(dir):
                shutil.copy(args.readme,dir+args.readme+str(date))

        else:
                os.makedirs(dir)
                shutil.copy(args.readme,dir+args.readme+str(date))

        ## update readme
        out = os.system('vi %s'%args.readme)

        if out != 0:
                print('Could not update readme')
		sys.exit()

	## make the changes in the cube header
	if args.user:
		update_cube_header(args.cube,args.version,user=args.user,email=args.email)
	else:
		update_cube_header(cube=args.cube,version=args.version)
	
	print('Updated Version in cube %s'%args.cube)

