"""
    chapterbook.py -- a package to simplify usage of pylrs and streamline
               	      creation of LRF e-Books for the Sony PRS-500.
"""

#
# Acknowledgements:
#   This software would not have been possible without the efforts
#   of Mike Higgins (Falstaff), author of pylrs.
#   
# Copyright (c) 2007 EatingPie
#
#	You know the drill.  If you have any inkling of using this, it's
#   provided as-is and I am not responsible for an damage caused by
#   the use of the software.  This includes, but is not limited to,
#   the downfall of governments, the destruction of economies, the
#   collapse of infrastructure, etc.
#
# VERSIONS
#
#	2.1.2 - Convert <span class="italic"></span> to <i></i>
#			Removed stripping of empty <p> tags, since it removed
#			some NECESSARY <p> tags.
#			Moved --strip-html here, and added a
#			ChapterBook.preprocess_data() function.
#
#	2.1.1 - Re-Added Vertical Space at chapter start, and option
#			--no-chapterspace to control it
#			Added <starbreak> support, plus --no-starbreak option
#			Added --parskip option
#			Added "--use-html" as another alias for "--html-quotes"
#
#	2.1.0 - Added <verse> and <justified> tags. 
#			Rewrote lots of the style generation and HTML
#			tag detection code.
#			Fixed "<<" bug which only produced one "<"
#
#	2.0.3 - Add <blockquote> tag and offset of 40+40 by default
#
#   2.0.2 - Added function to remove all HTML Tags that are not
#           handled.
#           Fixed explanation of baselineskip (it's line spacing not
#           paragraph spacing).
#
#   2.0.1  - Fixed indentation error in text_to_unicode()
#
#

from sys			import *
from pylrs.pylrs	import *
from textconvert	import *
from cmdline		import *

#
# Verson Number
#
PIELRF_LIB_VERSION = "2.1.0"

#############################################################
# class PageStyles():										#
#															#
#		Encapsulation for TextStyles and PageStyles.		#
#															#
#############################################################
class PageStyles():

	# Text Type (size)
	STANDARD      = 0
	HEADER        = 1
	# Depth of BlockQuote Indent
	MAXDEPTH      = 3

	header        = None
	normalStyle   = None
	quoteStyle    = list()
	centered      = list()
	paragraph     = list()
	justified     = list()
	verse         = list()

	# Shortcuts
	chapterHead   = None
	tocEntry      = None
	tocHead       = None

	options       = None

	#################
	# __init__()	#
	#################
	def __init__(self):
		#
		# All these Appends set up the length of the lists,
		# and allow later assignment as array indices
		#
		for i in range(0,self.MAXDEPTH+1) :
			self.quoteStyle.append(None)
		#endfor
		for i in range(self.STANDARD,self.HEADER+1) :
			self.centered.append(None)
			self.paragraph.append(None)
			self.justified.append(None)
			self.verse.append(None)
		#endfor
	#enddef __init__

# endclass PageStyles()

#############################################################
#############################################################

#############################################################
# class ChapterBook											#
#															#
#		An encapsulation around Book(), taking options		#
#		portion of cmdopts structure as parameters.			#
#															#
#############################################################
class ChapterBook(Book):

	#
	# Encapsulating PageStyles is the main function of ChapterBook
	#
	styles  = None

	#############################################################
	# __init__()												#
	#############################################################
	def __init__(self, bookopts, **settings) :

		options           = bookopts.options

		#
		# Globals for textconvert.py
		#
		set_preserve_spaces(options.preserve_spaces)
		set_html_quotes(options.html_quotes)

		ps                = dict(textwidth=options.textwidth,
								 textheight=options.textheight)
		ps['topmargin']   = options.topmargin
		ps['headheight']  = options.headerheight

		# Sweeten up the title
		options.title     = convert_title_text(options.title)

		#
		# Title and author sort options are ignored for now, since
		# they don't seem to have any effect, or serve a different
		# purpose than I understood.
		#
		Book.__init__(self,
					  pagestyledefault= ps,
					  title=            options.title,
					  author=           options.author,
					  category=         options.category,
					  isbn=             options.isbn,
					  bookid=           options.bookid,
					  **settings)

		s = PageStyles()

		s.options      = bookopts.options

		STD            = s.STANDARD
		HDR            = s.HEADER
		MAX            = s.MAXDEPTH

		#
		# Pre-Creating (and re-using) the Styles saves tons of
		# space, rather than generating styles on a as-needed basis
		# This makes for some heavy code here, but saves a lot
		# of time/space in the LRF itself
		#
		s.normalStyle   = BlockStyle(sidemargin=  options.sidemargin)
		s.quoteStyle[0] = s.normalStyle
		for i in range(1,MAX+1) :
			offset          = options.sidemargin + (i*options.quoteoffset)
			s.quoteStyle[i] = BlockStyle(sidemargin=offset)
		#endif

		s.centered[STD]  = TextStyle(align="center",
									 parskip=      options.parskip,
									 baselineskip= options.baselineskip,
									 fontsize=     options.textsize,
									 fontweight=   options.textweight)
		s.centered[HDR]  = TextStyle(align="center",
									 parskip=      options.parskip,
									 baselineskip= options.baselineskip,
									 fontsize=     options.chaptersize,
									 fontweight=   options.chapterweight)
		s.paragraph[STD] = TextStyle(parindent=    options.parindent,
									 parskip=      options.parskip,
									 baselineskip= options.baselineskip,
									 fontsize=     options.textsize,
									 fontweight=   options.textweight)
		s.paragraph[HDR] = TextStyle(parindent=    options.parindent,
									 parskip=      options.parskip,
									 baselineskip= options.baselineskip,
									 fontsize=     options.chaptersize,
									 fontweight=   options.chapterweight)
		s.justified[STD] = TextStyle(baselineskip= options.baselineskip,
									 parskip=      options.parskip,
									 fontsize=     options.textsize,
									 fontweight=   options.textweight)
		s.justified[HDR] = TextStyle(baselineskip= options.baselineskip,
									 parskip=      options.parskip,
									 fontsize=     options.chaptersize,
									 fontweight=   options.chapterweight)
		s.verse[STD]     = TextStyle(parindent=    options.verseparindent,
									 parskip=      options.parskip,
									 baselineskip= options.baselineskip,
									 fontsize=     options.textsize,
									 fontweight=   options.textweight)
		s.verse[HDR]     = TextStyle(parindent=    options.verseparindent,
									 parskip=      options.parskip,
									 baselineskip= options.baselineskip,
									 fontsize=     options.chaptersize,
									 fontweight=   options.chapterweight)
		# top-of-page header
		s.header         = TextStyle(align='foot',
									 fontsize=     options.headersize,
									 fontweight=   options.headerweight)

		s.chapterHead    = s.centered[HDR] 
		s.tocHead        = s.centered[HDR]
		s.tocEntry       = s.justified[STD]

		self.styles      = s

	#enddef __init__()

	#############################################################
	# def make_title_sort():									#
	#															#
	#############################################################
	def make_title_sort(self, title):

		titlesort  = title
		titlesplit = title.split(" ")

		# Title with one name is just returned
		if len(titlesplit) <= 1 :
			return title

		if titlesplit[0] == "The" or titlesplit[0] == "the" or \
		   titlesplit[0] == "A"   or titlesplit[0] == "a" :
			del titlesplit[0]
			titlesort = " ".join(titlesplit)
		#endif

		return titlesort

	# enddef make_title_sort()

	#############################################################
	# def make_author_sort():									#
	#															#
	#############################################################
	def make_author_sort(self, author):

		authorsplit  = author.split(" ")
		authorlast   = len(authorsplit)-1
		# One-name author
		if authorlast <= 0 :
			return author

		lastname     = authorsplit.pop(authorlast)
		authorsort   = lastname+", "+" ".join(authorsplit)

		return authorsort

	# enddef make_author_sort()

	#############################################################
	# def TocPage():											#
	#															#
	#############################################################
	def TocPage(self, headertext=None, **settings):
		p = TocPage(self, headertext, **settings)
		self.append(p)
		return p
	# enddef TocPage()

	#############################################################
	# def Chapter():											#
	#															#
	#############################################################
	def Chapter(self, headertext=None, **settings):
		p = Chapter(self, headertext, **settings)
		self.append(p)
		return p
	# enddef Chapter()


	#############################################################
	#############################################################

	#############################################################
	# def preprocess_data():									#
	#############################################################
	def preprocess_data(self, data, verbose=False):

		options = self.styles.options

		# Convert known <span> to their simplified html equivalents
		data = eat_spans_replace_format(data)

		# Strip out the unknown HTML if requested
		if options.strip_html :
			if verbose :
				print "Cleaning unknown HTML tags..."
			data = eat_unknown_tags_yum(data)
		#endif

		# Replace floating "* * *" with a special <starbreak> tag
		if not options.no_starbreak :
			if verbose :
				print "Converting breaks..."
			data = eat_stars_replace_break(data)
		#endif

		return data
	# enddef preprocess_data()


#endclass ChapterBook()


#############################################################
#############################################################


#############################################################
# class Chapter												#
#############################################################
class Chapter(Page):

	#####################
	# class Layout()	#
	#####################
	class Layout():
		layout   = 0
		level    = 0
		maxLevel = 3

		def __init__(self, new_layout, new_level) :
			self.layout = new_layout
			self.level  = new_level
		#enddef __init__

		def equal(self, other) :
			if self.layout == other.layout and \
			   self.level  == other.level :
				return True
			#endif
			return False
		#enddef equal
	# end Layout()

	#
	# Constants - Bit Vectors
	#
	# Text Format/Style (not used as a vector currently)
	#
	ROMAN        = 0
	ITALIC       = 1
	BOLD         = 2
	SUB          = 4
	SUP          = 8

	#
	# Layout - A bit vector, with 1st 2 entries as array indices
	#
	STANDARD     = 0		# Index Into Array
	HEADER       = 1		# Index Into Arry

	CENTERED     = 2
	BLOCKQUOTE   = 4
	VERSE        = 8
	JUSTIFIED    = 16

	#
	# Chapter Headings vs. Body
	#
	BODY         = 0
	HEADING      = 1
	SUBHEADING   = 2

	#
	# Instance Variables
	#

	book         = None
	textBlock    = None
	TargetBlock  = None

	layout       = None
	pending      = None

	curParagraph = None

	style        = ROMAN
	emptyBQtag   = False
	first        = True

	line = ""

	#############################################################
	# __init__()												#
	#############################################################
	def __init__(self, book, headertext=None, **settings) :
		
		#
		# Initialization is somewhat redundant, but declaring
		# the things above makes things a bit clearer
		#
		self.book         = book
		self.textBlock    = None
		self.TargetBlock  = None
		self.curParagraph = None

		self.style        = self.ROMAN
		self.emptyBQtag   = False

		# First Layout is a Chapter Heading, set below
		self.layout       = self.Layout(self.HEADER|self.CENTERED, 0)
		self.pending      = self.Layout(self.STANDARD,             0)

		styles = book.styles
		if headertext :
			#
			# Make the Header, since the text was provided
			# It requires a style applied to the whole Page
			#
			header = Paragraph().append(headertext)
			bs     = styles.normalStyle
			hs     = styles.header
			hb     = TextBlock(hs, bs).append(header)
			hdr    = Header()
			hdr.PutObj(hb)
			ps     = self.book.PageStyle(header=hdr, **settings)
		else:
			ps     = book.PageStyle(**settings)
		#endif

		Page.__init__(self, ps, **settings)

		#
		# A textblock at top of page to jump to from the TOC.
		# This will end up being filled with the Chapter Header,
		# hence it being Centered/Header
		#
		bs = styles.normalStyle
		ts = styles.centered[styles.HEADER]

		self.TargetBlock = self.TextBlock(ts, bs);
		self.textBlock   = self.TargetBlock

	# enddef  __init__


	#############################################################
	# def strip_heading():										#
	#															#
	#	Even though everything has been converted, chapter		#
	#	titles must be stripped of lots of excess.				#
	#															#
	#############################################################
	def strip_heading(self, line):

		line = line.replace("\r\n"," ")
		line = line.replace("\n"," ")
		spaceline = line.replace("  ", " ")
		while spaceline != line :
			line      = spaceline
			spaceline = line.replace("  ", " ")
		return line

	# enddef strip_heading()

	#############################################################
	# def next_layout():										#
	#############################################################
	def next_layout(self, next_Layout, headStyle=BODY) :

		new_layout     = next_Layout.layout
		new_level      = next_Layout.level

		if headStyle == self.HEADING :
			new_layout |= self.CENTERED | self.HEADER
		if headStyle == self.SUBHEADING :
			new_layout &= ~self.CENTERED
			new_layout |=  self.HEADER | self.JUSTIFIED
		#endif

		#
		# the whole point of this is to NOT generate a new textblock
		# unless we absolutely need to!
		#
		if (self.textBlock != None) and \
		   (new_layout     == self.layout.layout) and \
		   (new_level      == self.layout.level) :
			return self.textBlock.Paragraph()

		#
		# Get Styles from the Book
		# First set up constants, and index into which
		# text style (standard or header)
		#
		styles    = self.book.styles
		MAXDEPTH  = styles.MAXDEPTH

		style     = styles.STANDARD
		if new_layout & self.HEADER :
			style = styles.HEADER

		newStyle  = styles.paragraph[style]
		newBlock  = styles.normalStyle
		level     = new_level

		#
		# If verse or blockquote, go to indented block
		#
		if new_layout & self.VERSE:
			#
			# Verse is 1 quote level indented further
			# than current quote level
			#
			level    += 1
		#endif
		if level > 0 :
			# BlockQuote - Just make sure it doesn't overflow the Reader
			if level > MAXDEPTH :
				level = MAXDEPTH
			#endif
			newBlock  = styles.quoteStyle[level]
		#endif

		#
		# The Text Style is determined here.
		# Justified is lowest priority, centered is highest.
		#
		if new_layout & self.JUSTIFIED:
			newStyle  = styles.justified[style]
		#endif
		if new_layout & self.VERSE:
			newStyle  = styles.verse[style]
		#endif
		if new_layout & self.CENTERED :
			newStyle  = styles.centered[style]
		#endif

		self.textBlock = self.TextBlock(newStyle, newBlock)
		self.layout    = self.Layout(new_layout, new_level);

		return self.textBlock.Paragraph()

	# enddef next_layout()


	#############################################################
	#############################################################

	#############################################################
	# def NewHeadingTarget():									#
	#															#
	#############################################################
	def NewTargetHeading(self):

		styles            = self.book.styles

		# First Layout is a Chapter Heading, set below
		self.layout       = self.Layout(self.HEADER|self.CENTERED, 0)
		self.pending      = self.Layout(self.STANDARD,             0)

		#
		# A textblock at top of page to jump to from the TOC.
		# This will end up being filled with the Chapter Header,
		# hence it being Centered/Header
		#
		bs = styles.normalStyle
		ts = styles.centered[styles.HEADER]

		self.TargetBlock = self.TextBlock(ts, bs);
		self.textBlock   = self.TargetBlock

	# enddef NewTargetHeading()


	#############################################################
	# def Heading():											#
	#															#
	#############################################################
	def Heading(self, line):

		line = self.strip_heading(line)

		self.Body(line, headStyle=self.HEADING)

		#
		# Save the TextBlock for return, in case a TOC wants to
		# point here
		#
		headingTarget = self.textBlock

		#
		# This will insert a standard sized line-break
		# between the chapter heading and the following text.
		# Just generating / inserting a blank paragraph does this
		#
		nextLayout    = self.Layout(self.STANDARD, 0)
		paragraph     = self.next_layout(nextLayout)

		return headingTarget

	# enddef Heading()

	#############################################################
	# def SubHeading():											#
	#															#
	#############################################################
	def SubHeading(self, line):

		line = self.strip_heading(line)

		self.Body(line, headStyle=self.SUBHEADING)

		#
		# Save the TextBlock for return, in case a TOC wants to
		# point here
		#
		headingTarget = self.textBlock

		#
		# This will insert a standard sized line-break
		# between the chapter heading and the following text.
		# Just generating / inserting a blank paragraph does this
		#
		nextLayout    = self.Layout(self.STANDARD, 0)
		paragraph     = self.next_layout(nextLayout)

		return headingTarget

	# enddef SubHeading()


	#############################################################
	# def Body():												#
	#############################################################
	def Body(self, line, headStyle=BODY):

		self.line = line

		italic_bgn    = re.compile("<i>",           re.I|re.M)
		italic_end    = re.compile("</i>",          re.I|re.M)
		bold_bgn      = re.compile("<b>",           re.I|re.M)
		bold_end      = re.compile("</b>",          re.I|re.M)
		em_bgn        = re.compile("<em>|<cite>",   re.I|re.M)
		em_end        = re.compile("</em>|</cite>", re.I|re.M)
		strong_bgn    = re.compile("<strong>",      re.I|re.M)
		strong_end    = re.compile("</strong>",     re.I|re.M)
		#
		sub_bgn       = re.compile("<sub>",         re.I|re.M)
		sub_end       = re.compile("</sub>",        re.I|re.M)
		sup_bgn       = re.compile("<sup>",         re.I|re.M)
		sup_end       = re.compile("</sup>",        re.I|re.M)
		#
		hdr_bgn       = re.compile("<h.>",          re.I|re.M)
		hdr_end       = re.compile("</h.>",         re.I|re.M)
		#
		center_bgn    = re.compile("<center>",      re.I|re.M)
		center_end    = re.compile("</center>",     re.I|re.M)
		#
		blockqt_bgn   = re.compile("<blockquote>",  re.I|re.M)
		blockqt_end   = re.compile("</blockquote>", re.I|re.M)
		#
		just_bgn      = re.compile("<justified>",   re.I|re.M)
		just_end      = re.compile("</justified>",  re.I|re.M)
		verse_bgn     = re.compile("<verse>",       re.I|re.M)
		verse_end     = re.compile("</verse>",      re.I|re.M)
		#
		starbreak     = re.compile("<starbreak>",   re.I|re.M)
		#
		br_bgn        = re.compile("<br>",          re.I|re.M)
		br_end        = re.compile("</br>",         re.I|re.M)

		nextLayout    = self.pending.layout
		nextLevel     = self.pending.level
		preserve_pps  = self.book.styles.options.preserve_paragraphs
		chapterspace  = not self.book.styles.options.no_chapterspace

		#
		# If we are not preserving blank paragraphs, eat
		# up blank lines.
		#
		if len(line) <= 0 :
			if preserve_pps :
				layout    = self.Layout(nextLayout, nextLevel)
				paragraph = self.next_layout(layout, headStyle)
			#endif
			return
		#endif

		#
		# Set Up Initial paragraph based on previous tags
		# The bodyTarget is the "topmost" TextBlock in the
		# paragraph (there may be multiple TextBlocks due to
		# formatting, so we need to save the first)
		#
		paragraph   = self.next_layout(self.pending, headStyle)
		bodyTarget  = self.textBlock
		needsLayout = False

		# Chapter Heading gets a CR on first line to offset it
		if headStyle != self.BODY and chapterspace:
			paragraph.CR()
		#endif

		#
		# Split at html open, a "<"
		#
		first_char  = line[0]
		formatting  = line.split("<")
		length      = len(formatting)

		#
		# If the open of the paragraph was NOT a tag
		# Due to the intricacies of the split, if the first
		# character is a "<", we start at index 1, since index 0
		# will contain nothing.  Otherwise, start at index 0 like
		# we should
		#
		initial_lt  = True
		start       = 1
		if first_char != '<' and len(formatting[0]) >= 1 :
			start      = 0
			initial_lt = False
		#endif

		#
		# Each line in split is broken at a potential html format tag
		#
		needs_cr = False
		had_cr   = True
		first    = True
		i        = start
		while i < length :
			#
			# Add the "<" that we split on back in
			#
			f_str = "<" + formatting[i]
			if first and not initial_lt :
				f_str    = formatting[i]
			#endif
			first = False

			if needs_cr :
				paragraph.append(CR())
				needs_cr = False
				had_cr   = True
			#endif

			#
			# START FORMATTING
			#
			check       = True
			strip_regex = None

			#
			# <I> - ITALICS
			# For some reason find range 0,1 doesn't work, but 0,2 does
			#
			if check and italic_bgn.match(f_str, 0, 3) != None :
				self.style |= self.ITALIC
				f_str       = italic_bgn.sub("", f_str, 1)
				check       = False
			#endif
			#
			# <EM>|<CITE> - Same as Italics
			#
			if check and em_bgn.match(f_str, 0, 6) != None :
				self.style |= self.ITALIC
				f_str       = em_bgn.sub("", f_str, 1)
				check       = False
			#endif
			#
			# <STRONG> - Italics
			#
			if check and strong_bgn.match(f_str, 0, 8) != None :
				self.style |= self.ITALIC
				f_str       = strong_bgn.sub("", f_str, 1)
				check       = False
			#endif

			#
			# <B> - BOLD
			#
			if check and bold_bgn.match(f_str, 0, 3) != None :
				self.style |= self.BOLD
				f_str       = bold_bgn.sub("", f_str, 1)
				check       = False
			#endif

			#
			# SUB
			# <SUB> - SUBSCRIPT
			#
			if check and sub_bgn.match(f_str, 0, 5) != None :
				self.style |= self.SUB
				f_str       = sub_bgn.sub("", f_str, 1)
				check       = False
			#endif

			#
			# SUPER
			# <SUP> - SUPERSCRIPT
			#
			if check and sup_bgn.match(f_str, 0, 5) != None :
				self.style |= self.SUP
				f_str       = sup_bgn.sub("", f_str, 1)
				check       = False
			#endif

			#
			# END FORMATTING
			#

			#
			# </I> - END ITALICS
			#
			if check and italic_end.match(f_str, 0, 4) != None :
				self.style &= ~self.ITALIC
				f_str       = italic_end.sub("", f_str, 1)
				check       = False
			#endif
			#
			# </EM>|</CITE> - END ITALICS
			#
			if check and em_end.match(f_str, 0, 7) != None :
				self.style &= ~self.ITALIC
				f_str       = em_end.sub("", f_str, 1)
				check       = False
			#endif
			#
			# </STRONG> - END ITALICS
			#
			if check and strong_end.match(f_str, 0, 9) != None :
				self.style &= ~self.ITALIC
				f_str       = strong_end.sub("", f_str, 1)
				check       = False
			#endif

			#
			# </B> - END BOLD
			#
			if check and bold_end.match(f_str, 0, 4) != None :
				self.style &= ~self.BOLD
				f_str       = bold_end.sub("", f_str, 1)
				check       = False
			#endif

			#
			# SUPER
			# </SUB> - END SUBSCRIPT
			#
			if check and sub_end.match(f_str, 0, 6) != None :
				self.style &= ~self.SUB
				f_str       = sub_end.sub("", f_str, 1)
				check       = False
			#endif

			#
			# SUB
			# </SUP> - END SUPERSCRIPT
			#
			if check and sup_end.match(f_str, 0, 6) != None :
				self.style &= ~self.SUP
				f_str       = sup_end.sub("", f_str, 1)
				check       = False
			#endif

			#
			# Formatting (new Paragraph) Tags
			#
			# These ALL generate new paragraphs, so we need to strip
			# any leading whitespaces, including "/r"
			#
			# Note: <blockquote> will create a blank newline before and
			# after, which emulates HTML behaviour.
			# None of the other tags cause vertical whitespace
			#

			#
			# <H1>|<H2>|<H3>  - HEADER
			#
			# Set paragrah element to be a header.
			#
			if check and hdr_bgn.match(f_str, 0, 4) != None :
				nextLayout |= self.HEADER
				strip_regex = hdr_bgn
				needsLayout = True
				check       = False
			#endif

			#
			# <CENTER>  - CENTERED TEXT
			#
			# Set paragrah element to be centered.
			#
			if check and center_bgn.match(f_str, 0, 8) != None :
				nextLayout |= self.CENTERED
				strip_regex = center_bgn
				needsLayout = True
				check       = False
			#endif

			#
			# <JUSTIFIED>   - QUOTED TEXT
			# <VERSE>       - QUOTED TEXT
			#
			# Set quote element to be a quote.
			#
			if check and just_bgn.match(f_str, 0, 11) != None :
				nextLayout |= self.JUSTIFIED
				strip_regex = just_bgn
				needsLayout = True
				check       = False
			#endif
			if check and verse_bgn.match(f_str, 0, 7) != None :
				nextLayout |= self.VERSE
				strip_regex = verse_bgn
				needsLayout = True
				check       = False
			#endif

			#
			# <BLOCKQUOTE>  - QUOTED TEXT
			#
			if check and blockqt_bgn.match(f_str, 0, 12) != None :
				nextLevel  += 1
				strip_regex = blockqt_bgn
				needsLayout = True
				check       = False

				# This produces blank line
				if not self.emptyBQtag and not had_cr :
					layout      = self.Layout(nextLayout, nextLevel)
					paragraph   = self.next_layout(layout, headStyle)
				#endif
				self.emptyBQtag = True
				had_cr          = True
			#endif

			#
			# </H1>|</H2>|</H3>  - END HEADER
			#
			if check and hdr_end.match(f_str, 0, 5) != None :
				nextLayout &= ~self.HEADER
				strip_regex = hdr_end
				needsLayout = True
				check       = False
			#endif

			#
			# </CENTER> - END CENTERED (JUSTIFIED TEXT)
			#
			if check and center_end.match(f_str, 0, 9) != None :
				nextLayout &= ~self.CENTERED
				strip_regex = center_end
				needsLayout = True
				check       = False
			#endif

			#
			# </JUSTIFIED> - END QUOTE
			# </VERSE> - END QUOTE
			#
			if check and just_end.match(f_str, 0, 12) != None :
				nextLayout &= ~self.JUSTIFIED
				strip_regex = just_end
				needsLayout = True
				check       = False
			#endif
			if check and verse_end.match(f_str, 0, 8) != None :
				nextLayout &= ~self.VERSE
				strip_regex = verse_end
				needsLayout = True
				check       = False
			#endif

			#
			# </BLOCKQUOTE> - END QUOTE
			#
			if check and blockqt_end.match(f_str, 0, 13) != None :
				nextLevel  -= 1
				strip_regex = blockqt_end
				needsLayout = True
				check       = False

				# Blank line after block quote
				if not self.emptyBQtag and not had_cr:
					layout      = self.Layout(nextLayout, nextLevel)
					paragraph   = self.next_layout(layout, headStyle)
				#endif
				self.emptyBQtag = True
				had_cr          = True
			#endif

			#
			# <BR> - Break
			#
			if check and br_bgn.match(f_str, 0, 4) != None :
				strip_regex = br_bgn
				needsLayout = False
				check       = False

				layout      = self.Layout(nextLayout, nextLevel)
				paragraph   = self.next_layout(layout, headStyle)
				had_cr      = True
			#endif

			#
			# <STARBREAK> - A layout break with "* * *" in the middle
			#
			if check and starbreak.match(f_str, 0, 12) != None :
				strip_regex = starbreak
				needsLayout = False
				check       = False

				wascentered = False
				if nextLayout & self.CENTERED :
					wascentered = True

				nextLayout |= self.CENTERED
				layout      = self.Layout(nextLayout, nextLevel)
				paragraph   = self.next_layout(layout, headStyle)

				if not had_cr or wascentered :
					paragraph.append(CR())

				paragraph.append("* * *")

				if not wascentered :
					nextLayout &= ~self.CENTERED
					layout      = self.Layout(nextLayout, nextLevel)
					paragraph   = self.next_layout(layout, headStyle)
				#endif

				#
				# Always need a CR
				# If we get a new paragraph, this loop will exit and
				# the correct CR will be placed afterwards
				#
				needs_cr    = True
				had_cr      = True
				#endif
			#endif

			#
			# Eliminate trailing spaces from layout tags such as <center>,
			# <blockquote>, <h1>, etc.  strip_regex will be provided if
			# we just had a layout tag.
			#
			if strip_regex != None :
				f_str       = strip_regex.sub("", f_str, 1)
				f_str       = f_str.lstrip().lstrip("/r").lstrip("/n")
				if len(f_str) <= 0 or f_str.isspace():
					i += 1
					continue
				#endif
			#endif

			# Got some text, so IF we're in a blockquote, it's not empty
			self.emptyBQtag = False

			#
			# There is text to include at this point...
			# IF the layout has changed, get the new paragraph
			# under the new layout
			#
			if needsLayout :
				layout      = self.Layout(nextLayout,  nextLevel)
				paragraph   = self.next_layout(layout, headStyle)
				needsLayout = False
			#endif

			#
			# The order here is imperative!
			# Cannot append Bold/Italic to Sub/Sup,
			# But you CAN append Sub/Sup to Bold/Italic
			# So sub/sup go first.
			#
			s = f_str
			if s != None and s != "" :
				#
				# Yes this needs to be done at the top AND bottom
				# of the loop, in case the loop exits, or re-enters
				# Weird, but trust me, I tested it
				#
				if needs_cr :
					paragraph.append(CR())
					needs_cr = False
				#endif

				if self.style & self.SUB :
					s = Sub(s)
				if self.style & self.SUP :
					s = Sup(s)
				if self.style & self.ITALIC :
					s = Italic(s)
				if self.style & self.BOLD :
					s = Bold(s)

				paragraph.append(s)
				had_cr = False
			#endif

			#increment
			i += 1
		#endfor

		self.curParagraph = paragraph

		# Save off current (potential) settings for next run thru
		self.pending = self.Layout(nextLayout, nextLevel)

		return bodyTarget

	# enddef Body()

# endclass Chapter()

#############################################################
#############################################################

#############################################################
# class TocPage():											#
#															#
#############################################################
class TocPage(Chapter):

	tocHead    = None
	tocEntries = None

	#############################################################
	# def Heading():											#
	#############################################################
	def Heading(self, headingText):

		styles   = self.book.styles
		bs       = styles.normalStyle
		headTs   = styles.chapterHead

		self.tocHead  = self.TextBlock(headTs, bs)

		self.tocHead.Paragraph(headingText)
		self.tocHead.Paragraph()

		return self.tocHead

	#enddef Heading

	#############################################################
	# def TocEntry():											#
	#############################################################
	def TocEntry(self, text=None, target=None):

		if not self.tocEntries :
			styles          = self.book.styles
			bs              = styles.normalStyle
			tocTs           = styles.tocEntry
			self.tocEntries = self.TextBlock(tocTs, bs)
		#endif

		#
		# Can Add
		# 	1) a blank spacer
		# 	2) Text Entry
		# 	3) Toc Button
		#
		if not text :
			self.tocEntries.Paragraph()
		elif not target :
			self.tocEntries.Paragraph(text)
		else :
			button = CharButton(JumpButton(target), text)
			self.tocEntries.Paragraph(button)
		#endif

		return self.tocEntries

	# enddef TocEntry()

# endclass TocPage()
