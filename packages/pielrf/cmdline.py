"""
    cmdline.py -- Command Line Options for the ChapterBook() Class
                  Derive and extend this class to add additional
                  options.
"""

from sys		import *
from optparse	import OptionParser
from os			import path

#############################################################
# class ChapterBookOptions():								#
#															#
#############################################################
class ChapterBookOptions():

	cmdline = None
	options = None
	args    = None
	rcfile  = None

	#############################################################
	# __init__()												#
	#############################################################
	def __init__(self, usage, rcfile=None):

		self.cmdline = OptionParser(usage=usage)

		if rcfile != None :
			self.rcfile = path.expanduser("~/"+rcfile)

	#enddef __init__


	#############################################################
	# def optstr_to_boolean():									#
	#############################################################
	def optstr_to_boolean(self, value):
		if value[0] in ['t','T','1']:
			return True
		elif value[0] in ['f','F','0']:
			return False
		else:
			return None
	#enddef opstr_to_boolean

	#############################################################
	# def boolean_to_optstr():									#
	#############################################################
	def boolean_to_optstr(self, value):
		if value == True:
			return "True"
		return "False"
	#enddef opstr_to_boolean


	#############################################################
	# def read_config_file():									#
	#############################################################
	def read_config_file(self):

		if self.rcfile == None:
			return

		#
		#if it doesn't exist, just forget about it
		#
		if not path.isfile(self.rcfile):
			return

		try:
			f = open(self.rcfile, "r")
			data = f.readlines()
			f.close()
		except:
			print "Error reading config file:", self.rcfile
			return
		#endtry

		#
		# Read each line and set the default values
		#
		for line in data:
			line = line.split("=")
			if len(line) < 2 :
				continue
			name  = line[0].strip()
			value = line[1].split("#")[0].strip()
			self.set_option_default(name, value)
		#endfor

	#enddef read_config_file

	#############################################################
	# def write_config_file():									#
	#############################################################
	def write_config_file(self):

		if self.rcfile == None:
			return

		#
		# Load the options for writing
		#
		data = self.get_option_defaults()
		if data == None:
			return

		try:
			f = open(self.rcfile, "w")
			f.write(data)
			f.close()
		except:
			print "Error writing config file:", self.rcfile
			return
		#endtry

	#enddef write_config_file

	#############################################################
	# def set_option_default():									#
	#############################################################
	def set_option_default(self, name, value):

		cmdline = self.cmdline

		#
		# BOOLEAN
		#
		#
		# Paragraph Control
		#
		if name == "preserve-paragraphs":
			value = self.optstr_to_boolean(value)
			if value == None:
				return
			cmdline.set_defaults(preserve_paragraphs=value)
		elif name == "preserve-spaces":
			value = self.optstr_to_boolean(value)
			if value == None:
				return
			cmdline.set_defaults(preserve_spaces=value)
		elif name == "html-quotes":
			value = self.optstr_to_boolean(value)
			if value == None:
				return
			cmdline.set_defaults(html_quotes=value)
		#
		# Chapter Control
		#
		elif name == "no-chapterspace":
			value = self.optstr_to_boolean(value)
			if value == None:
				return
			cmdline.set_defaults(no_chapterspace=value)

		#
		# NUMBERS
		#
		#
		# Screen Dimensions
		#
		elif name == "screenheight":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(textheight=value)
		elif name == "screenwidth":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(textwidth=value)
		#
		# Margins
		#
		elif name == "headerheight":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(headerheight=value)
		elif name == "topmargin":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(topmargin=value)
		elif name == "sidemargin":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(sidemargin=value)
		elif name == "quoteoffset":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(quoteoffset=value)
		#
		# Paragraph Settings
		#
		elif name == "parskip":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(parskip=value)
		elif name == "parindent":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(parindent=value)
		elif name == "verseparindent":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(verseparindent=value)
		elif name == "baselineskip":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(baselineskip=value)
		#
		# Font size and boldness
		#
		elif name == "fontsize":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(textsize=value)
		elif name == "fontweight":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(textweight=value)
		elif name == "headerfontsize":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(headersize=value)
		elif name == "headerfontweight":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(headerweight=value)
		elif name == "chapterfontsize":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(chaptersize=value)
		elif name == "chapterfontweight":
			try:    value = int(value)
			except: return
			cmdline.set_defaults(chapterweight=value)
		#endif

	#enddef set_option_default

	#############################################################
	# def get_option_defaults():								#
	#############################################################
	def get_option_defaults(self) :

		options    = self.options

		paragraphs = self.boolean_to_optstr(options.preserve_paragraphs)
		spaces     = self.boolean_to_optstr(options.preserve_spaces)
		html       = self.boolean_to_optstr(options.html_quotes)
		no_chapspc = self.boolean_to_optstr(options.no_chapterspace)

		line = ""
		# Screen
		line += "#\n# Screen\n#\n"
		line += "screenheight = %d\n"        %options.textheight
		line += "screenwidth = %d\n"         %options.textwidth
		# Margins
		line += "#\n# Margins\n#\n"
		line += "headerheight = %d\n"        %options.headerheight
		line += "topmargin = %d\n"           %options.topmargin
		line += "sidemargin = %d\n"          %options.sidemargin
		line += "quoteoffset = %d\n"         %options.quoteoffset
		# Paragraph Settings
		line += "#\n# Paragraphs\n#\n"
		line += "parskip = %d\n"             %options.parskip
		line += "parindent = %d\n"           %options.parindent
		line += "verseparindent = %d\n"      %options.verseparindent
		line += "baselineskip = %d\n"        %options.baselineskip
		line += "preserve-paragraphs = %s\n" %paragraphs
		line += "preserve-spaces = %s\n"     %spaces
		line += "html-quotes = %s\n"         %html
		line += "no_chapterspace = %s\n"     %no_chapspc
		# Font Settings
		line += "#\n# Fonts\n#\n"
		line += "fontsize = %d\n"            %options.textsize
		line += "fontweight = %d\n"          %options.textweight
		line += "headerfontsize = %d\n"      %options.headersize
		line += "headerfontweight = %d\n"    %options.headerweight
		line += "chapterfontsize = %d\n"     %options.chaptersize
		line += "chapterfontweight = %d\n"   %options.chapterweight

		return line

	#enddef get_option_defaults

	#############################################################
	# def add_options():										#
	#															#
	#	These are the required options for ChapterBook()		#
	#	Instantiation.  A shortcut way to fill the options.		#
	#															#
	#############################################################
	def add_options(self):

		cmdline = self.cmdline

		#
		# Title / Author
		#
		cmdline.add_option("-t", "--title", dest="title", default="",
						   action="store",  type="string",
						   help="Specify Book Title, use quotes")
		cmdline.add_option("-a", "--author",dest="author",default="",
						   action="store",  type="string",
						   help="Specify Book Author, use quotes.")
		cmdline.add_option("--category", dest="category", default="Fiction",
						   action="store",  type="string",
						   help="Specify Book Category. DEFAULT: Fiction")
		cmdline.add_option("--bookid", dest="bookid", default="FB0123456",
						   action="store",  type="string",
						   help="Specify eReader Book ID (unnecessary).")
		cmdline.add_option("--isbn", dest="isbn", default="123-0-1234-5678-9",
						   action="store",  type="string",
						   help="Specify Book ISBN (unnecessary).")

		#
		# Paragraph cleaning
		#
		cmdline.add_option("--preserve-paragraphs",
						   dest="preserve_paragraphs",
						   default=False, action="store_true",
						   help="Do not remove blank (empty) paragraphs "
						        "DEFAULT is to remove all empty paragraphs."
						   )
		cmdline.add_option("--preserve-spaces", dest="preserve_spaces",
						   default=False, action="store_true",
						   help="Do not remove extra spaces between words. "
						        "DEFAULT is to remove spaces because the "
						   		"Reader treats extra spaces as non-breaking, "
						   		"which interferes with proper justification"
						   )
		cmdline.add_option("--no-chapterspace", dest="no_chapterspace",
						   default=False, action="store_true",
						   help="Chapters Headings have extra vertical space "
						   		"to offset them.  This option removes the "
						   		"extra vertical space, and pushes the chapter "
						   		"heading up to the top margin."
						   )
		cmdline.add_option("--ignore-html-quotes",   "--no-rdquotes",
						   "--use-quote-algorithm",
						   dest="html_quotes",
						   default=True,
						   action="store_false",
						   help="Abandont HTML curly quotes and use pielrf's "
						   		"internal curly-quote algorithm."
						        "DEFAULT is TO trust the HTML tags."
						   )
		cmdline.add_option("--html-quotes",      "--use-rdquotes",
						   "--html-curlyquotes", "--trust-html",
						   "--use-html",
						   dest="html_quotes_deprecated",
						   default=False,
						   action="store_true",
						   help="DEPRECATED, repaced by --ignore-html-quotes."
						   )
		#
		# These do NOT get written to the .rc file because they
		# will likely change with each run
		#
		cmdline.add_option("--no-starbreak", dest="no_starbreak",
						   default=False, action="store_true",
						   help="Do NOT convert \"* * *\" on its own line "
						   		"to a section break, just leave them as stars"
						   )
		cmdline.add_option("--strip-html", dest="strip_html",
						   default=False,
						   action="store_true",
						   help="Strip UNKNOWN html tags during conversion."
						   )
		#
		# Screen Dimensions
		#
		cmdline.add_option("--screenheight", dest="textheight",
						   default=690,
						   action="store",  type="int",
						   metavar="HEIGHT (pixels)",
						   help="Height of text \"screen\" area (pixels). "
						   "Note this is NOT the actual physical screen"
						   "height but the area text can be displayed within. "
						   "Using 690x575 for the 800x600 Sony Reader. "
						   "DEFAULT: 690")
		cmdline.add_option("--screenwidth", dest="textwidth",
						   default=560,
						   action="store",  type="int",
						   metavar="WIDTH (pixels)",
						   help="Width of text \"screen\" area (pixels). "
						   "DEFAULT: 560")

		#
		# Margins
		#
		cmdline.add_option("--headerheight", dest="headerheight",
						   default=55,
						   action="store",  type="int",
						   help="Vertical height of Header (pixels). "
						   		"DEFAULT: 55")
		cmdline.add_option("--topmargin", dest="topmargin",
						   default=15,
						   action="store",  type="int",
						   help="Height of Top Margin (pixels). "
						   		"DEFAULT: 15")
		cmdline.add_option("--sidemargin", dest="sidemargin",
						   default=20,
						   action="store",  type="int",
						   help="Width of Side Margins (pixels). "
						   		"DEFAULT: 20")
		cmdline.add_option("--quoteoffset", dest="quoteoffset",
						   default=40, #50
						   action="store",  type="int",
						   help="Additional Margin Depth for a Quote "
						   		"(margin=sidemargin+quoteoffset (pixels). "
						   		"DEFAULT: 40")

		#
		# Paragraph Settings
		#
		cmdline.add_option("--parskip", dest="parskip",
						   default=0,
						   action="store",  type="int",
						   help="Spacing between paragraphs"
						   "DEFAULT: 0")
		cmdline.add_option("--parindent", dest="parindent",
						   default=200,
						   action="store",  type="int",
						   help="How far to Indent Paragraph's first line. "
						   "DEFAULT: 200")
		cmdline.add_option("--verseparindent", dest="verseparindent",
						   default=-180,#-225
						   action="store",  type="int",
						   help="NEGATIVE Indentation for verses (poetry). "
						   "DEFAULT: -180")
		cmdline.add_option("--baselineskip", dest="baselineskip",
						   default=120,
						   action="store",  type="int",
						   help="Line spacing."
						   "DEFAULT: 120, for double-spaced lines use 240.")

		#
		# Font size and boldness
		#
		cmdline.add_option("--fontsize", dest="textsize",
						   default=95,
						   action="store",  type="int",
						   metavar="FONTSIZE (points)",
						   help="Text Font size (points) - "
						   		"DEFAULT: 95")
		cmdline.add_option("--fontweight", dest="textweight",
						   default=400,
						   action="store",  type="int",
						   metavar="FONTWEIGHT (strength)",
						   help="Text Font weight - "
						   		"DEFAULT 400, Bold is 800.")
		#
		cmdline.add_option("--headerfontsize", dest="headersize",
						   default=80,
						   action="store",  type="int",
						   metavar="FONTSIZE (points)",
						   help="Header Font size (points) - "
						   		"DEFAULT: 80")
		cmdline.add_option("--headerfontweight", dest="headerweight",
						   default=400,
						   action="store",  type="int",
						   metavar="FONTWEIGHT (strength)",
						   help="Header Font weight - "
						   		"DEFAULT 400, Bold is 800.")
		#
		cmdline.add_option("--chapterfontsize", dest="chaptersize",
						   default=120,
						   action="store",  type="int",
						   metavar="FONTSIZE (points)",
						   help="Chapter Font size (points) - "
								"DEFAULT: 120")
		cmdline.add_option("--chapterfontweight", dest="chapterweight",
						   default=800,
						   action="store",  type="int",
						   metavar="FONTWEIGHT (strength)",
						   help="Chapter Font weight - "
								"DEFAULT 800, Roman is 400.")

	# enddef add_book_options()

	#############################################################
	# def print_options():										#
	#############################################################
	def print_options(self):

		print "Title:   ", options.title
		print "Author:  ", options.author
		print "Category:", options.category
		print "ISBN:    ", options.isbn
		print "BookID:  ", options.bookid

		print "Options:"
		print "\tViewable Area:", \
			  options.textheight, "x", options.textwidth, \
			  "- [", options.topmargin, ", ", options.sidemargin, "] with", \
   			  options.headerheight, "header height"
		print "\tText Font:    ", \
			  options.textsize,   "(pixels) +", \
			  options.textweight, "(strength)"
		print "\tHeader Font:  ", \
			  options.headersize,   "(pixels) +", \
			  options.headerweight, "(strength)"
		print "\tChapter Font: ", \
			  options.chaptersize,  "(pixels) +", \
			  options.chapterweight,"(strength)"
		print "\tParagraphs:   ", \
			  options.parindent, "(points Indent) +", \
			  options.baselineskip, "(points Baseline)"
		if options.parskip > 0 :
			print "\t\t     +", options.parskip,   "(points Spacing)"
		if options.no_chapterspace :
			print "\tPushing Chapter Headings to top of margin"
		if options.no_starbreak :
			print "\tNot processing \"* * *\" characters into section breaks."
		print "\tIndent Level: ", \
			   options.quoteoffset, "(pixels Indent)"
		print "\tVerse Indent: ", \
			   options.verseparindent, "(pixels)"

		if options.html_quotes:
			print "\tUsing explicit HTML curly-quotes (&rdquo;|&ldquo;)"
		else :
			print "\tUsing algorithm for explicit curly-quotes"

		if options.preserve_spaces :
			print "\tPreserving extra spaces"
		else :
			print "\tEliminating extra spaces"

		if options.preserve_paragraphs :
			print "\tPreserving empty paragraphs"
		else :
			print "\tEliminating empty paragraphs"

		if options.strip_html :
			print "\tStripping Unknown HTML Tags"

	#enddef print_options()


# endclass ChapterBookOptions()

