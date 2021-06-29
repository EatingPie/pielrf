#!/usr/bin/env python
#
# Setup script for pielrf
#
# Installs required modules into python2.5+
#
#		ElemenTree
#		pylrs
#
# Windows does not have required utilities, so print appropriate
# messages in this case.
#
# Usage: python setup.py install
#
VERSION                = "2.0"
REQUIRED_PYLRS_VERSION = "1.0.1"
autoinstall            = True

from   distutils.core import setup
import sys
try :
	from os import rename, name as osname
	from os import path, symlink, unlink
except ImportError :
	autoinstall = False
#endtry

#
# Require Python 2.5 or bomb
#
if sys.hexversion < 0x20500f0:
	print >> sys.stderr, "You have python version", sys.version
	print >> sys.stderr, "You must use python version 2.5 or later"
	print >> sys.stderr, "Try invoking this script as \"python2.5 setup.py\""
	print >> sys.stderr, "Otherwise, download and install from "\
						 "<www.python.org>:"
	print >> sys.stderr, "\t<http://www.python.org/download>"
	sys.exit(1)
#endif

#
# Want to be smart about this...
# If user is requesting help or whatnot, skip error and install checks
# and go straight to setup command so it can print the appropriate
# help messages.
#
do_checks = True
if len(sys.argv) <= 1 :
	# Skip checkign if there are no arguments passed to the script
	do_checks = False
else :
	# Skip checking if ALL arguments are flags (start with "-")
	total_args = len(sys.argv)-1
	flag_count  = 0
	for i in range(1,len(sys.argv)) :
		if sys.argv[i][0] != "-" :
			break
		flag_count += 1
	#endfor
	if flag_count == total_args :
		do_checks = False
#endif

#
# Define Packages and associated directories
# For auto-install or messages to hand-install
#
packages     = ["elementtree", "pylrs"]
element_dir  = "elementtree-1.2.6"
pylrs_dir    = "pylrs-1.0.1"
element_link = "packages/elementtree"
pylrs_link   = "packages/pylrs"
if autoinstall and do_checks :
	#
	# Create links so setup can find packages
	# This are ALWAYS installed using this method.
	#
	if path.islink(element_link) :
		unlink(element_link);
	if path.islink(pylrs_link) :
		unlink(pylrs_link);
	symlink(element_dir+"/elementtree", element_link)
	symlink(pylrs_dir+"/pylrs",         pylrs_link)

elif do_checks :
	#
	# Windows cannot do links so the user will have to install
	# the Packages by hand
	#
	try :
		import elementtree
	except ImportError :
		print "Required packages \""+packages[0]+"\" and\""+packages[1]+\
			  "\" are not installed."
		print "They are included in the \"packages\" directory,", \
	          "please install by hand:"
		print "\t cd packages/"+element_dir
		print "\t python setup.py install"
		print "\t cd .."
		print "\t cd packages/"+pylrs_dir
		print "\t python setup.py install"
		sys.exit(1)
	#end try

	#
	# Tell windows users to install if pylrs is wrong version, or
	# not found at all.
	#
	needs_pylrs = False
	try:
		from pylrs.pylrs import PYLRS_VERSION
		if PYLRS_VERSION != REQUIRED_PYLRS_VERSION :
			needs_pylrs = True
	except ImportError:
		needs_pylrs = True
	#end try

	if needs_pylrs :
		print "Required package \""+packages[1]+"\" Version", \
			  REQUIRED_PYLRS_VERSION, "is not installed."
		print "It is included in the \"packages\" directory,", \
	          "please install by hand:"
		print "\t cd packages/"+pylrs_dir
		print "\t python setup.py install"
		sys.exit(1)
	#endif

	# Everything Installed, now do pielrf itself, but no packages
	packages = []
#endif

#
# Always install pielrf library package (in packages directory)
#
packages += ["pielrf"]
scripts   = [ "pielrf", "asciicheck", "striphtml" ]

#
# For windows, make sure the scripts are named correctly
# for install (without .py extension)
#
if osname == "nt" :
	for script in scripts:
		win_script = script.upper()+".PY"
		if path.isfile(win_script):
			print "*** Renaming", win_script, "to", script
			rename(win_script, script)
		#endif
	#endfor
#endif

#
# SETUP COMMAND
#
setup(name         = "pielrf",
	  version      = VERSION,
	  author       = "EatingPie",
	  author_email = "pie@storybytes.com",
	  description  = "A program to create eBooks for the Sony PRS-500",
	  url          = "http://www.storybytes.com",
	  package_dir  = {"": "packages"},
	  packages     = packages,
	  scripts      = scripts
	  )

#
# Unlink the links for cleanliness
#
if autoinstall :
	if path.islink(element_link) :
		unlink(element_link);
	if path.islink(pylrs_link) :
		unlink(pylrs_link);
#endif

#
# For windows, make sure the scripts are named correctly
# for install (without .py extension)
#
if osname == "nt" :
	for script in scripts:
		win_script = script.upper()+".PY"
		if path.isfile(script):
			print "*** Renaming", script, "to", win_script
			rename(script, win_script)
		#endif
	#endfor
#endif
