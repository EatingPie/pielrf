"""
    textconvert.py -- Text Conversion utilities for use with pylrf.py
                      in the creation of LRF e-Books for the Sony PRS-500.

"""
#
# Acknowledgements:
#   Thanks to Lee Bigelow for contribution of text_to_unicode().
#
# Copyright (c) 2007 EatingPie, unless otherwise noted.
# text_to_unicode() copyright (c) 2007 Lee Bigelow.
#
#	See License in pielrf.py in this same directory.  Yeah, it applies
#	here too.  I know it sucks, but whatchya gonna do?
#

from   sys	import *
import re

#
# Globals - Should be set by command line options
#           from the book
#
preserve_spaces = False
html_quotes     = False

no_starbreak    = False
strip_html      = False

#############################################################
# def set_html_quotes():									#
#############################################################
def set_html_quotes(val):
	global html_quotes
	html_quotes = val
# enddef set_html_quotes()
#############################################################
# def set_preserve_spaces():								#
#############################################################
def set_preserve_spaces(val):
	global preserve_spaces
	preserve_spaces = val
# enddef set_preserve_spaces()
#############################################################
# def set_no_starbreak():									#
#############################################################
def set_no_starbreak(val):
	global no_starbreak
	no_starbreak = val
# enddef set_no_starbreak()

#############################################################
# def text_to_unicode():									#
#															#
#	accepts (text, a specific encoding to try, system		#
#	default encoding)										#
#	returns (unicode/ascii object, charaters punted flag,	#
#	encoding used)											#
#															#
#############################################################
def text_to_unicode(s, enc=None, denc=getdefaultencoding()):
	"""Try interpreting s using several possible encodings.  The
	return value is a three-element tuple.  The first element is
	either an ASCII string or a Unicode object.  The second
	element is 1 if the decoder had to punt and delete some
	characters from the input to successfully generate a Unicode
	object."""
	if isinstance(s, unicode):
		return s, 0, "unicode"
	try:
		x = unicode(s, "ascii")
		# if it's ascii, we're done
		return s, 0, "ascii"
	except UnicodeError:
		encodings = ["utf_8","latin_1","cp1252","iso8859_15"]
		if denc != "ascii":
			encodings.insert(0, denc)
		# always try any caller-provided encoding first
		if enc:
			encodings.insert(0, enc)

		for enc in encodings:

			# Most of the characters between 0x80 and 0x9F are
			# displayable in cp1252 but are control characters in
			# iso-8859-1.  Skip iso-8859-1 if they are found, even
			# though the unicode() call might well succeed.

			if (enc in ("iso8859_15", "latin_1") and
				re.search(r"[\x80-\x9f]", s) is not None):
				continue

			# Characters in the given range are more likely to be 
			# symbols used in iso-8859-15, so even though unicode()
			# may accept such strings with those encodings, skip them.

			if (enc in ("latin_1", "cp1252") and
				re.search(r"[\xa4\xa6\xa8\xb4\xb8\xbc-\xbe]", s) is not None):
				continue

			try:
				x = unicode(s, enc)
			except LookupError:
				pass
			except UnicodeError:
				pass
			else:
				if x.encode(enc) == s:
					return x, 0, enc
		#endfor

		# nothing worked perfectly - try again, but use the
		# "ignore" parameter and return the longest result
		output = []
		for enc in encodings:
			enc_s = unicode(s, enc, "ignore")
			output.append( (len(enc_s), enc) )
			del enc_s
		#endfor
		output.sort()
		enc = output[-1][1]
		x = unicode(s, enc, "ignore")
		return x, 1, enc
#enddef

#
# Globals for convert_curly_quotes()
#
prev_char       = ' '
prev_was_open   = False

#############################################################
# def convert_curly_quotes():								#
#															#
#############################################################
def convert_curly_quotes(line):

	#############################################################
	# def next_single_is_close():								#
	#		Find next valid single quote, and decide if it		#
	#		is a close quote.									#
	#############################################################
	def next_single_is_close(line, start) :
		#
		# Find next ' and see if it is a close quote.
		# If our find succeeds, but we're at end-of-line, that means
		# next is a close quote.
		#
		# Need a loop to skip apostrophes since those are legal,
		# even between single-quotes
		#
		# Damn single quotes... DAMN THEM ALL TO HELL!
		# On next occurrance, can have a close-quote between
		# a letter and punctuation, letter and a space.
		# Apostrophes are legal within single quotes.
		#
		last_pos  = start
		index     = line.find("'", start)
		while (index > 0) :
			#
			# Hitting eol, meaning it MUST be a curly close
			# even if it is floating in space
			#
			if index >= (len(line)-1):
				return True
			#endif

			prev_char = line[index-1]
			next_char = line[index+1]

			#
			# Skip an apostrophe -- this is the ONLY thing
			# we skip, and only reason this is a loop
			#
			if prev_char.isalnum() and next_char.isalnum() :
				last_pos = index+1
				index    = line.find("'", last_pos)
				continue
			#endif

			# Does not loop after this point, guaranteed return

			#
			# If previous is a space, it's open quote...
			# Unless it's floating in space, then we call it
			# a close-quote by default
			#
			if (prev_char.isspace() or prev_char == '\n') :
				if (next_char.isspace() or next_char == '\n') :
					# Floating in space - call it a close
					return True
				else :
					# Against a letter or something - it's not a close
					return False
			#endif

			#
			# At this point, prev char is NOT a space
			# Call it a close, since it could be against a letter
			# or some punctuation mark
			#
			return True
		#end while

		# Never found a valid close-quote
		return False
	#enddef next_single_is_close

	global prev_char
	global prev_was_open
	global html_quotes

	do_open   = True
	next_char = '\n'

	#
	# Replace any HTML quotes with he actual quote
	# This allows the curly-quote algorithm to function
	# on quotes only.
	#
	# The global html_quotes means we want to ignore
	# html-explicit curly quotes and use our own algorith
	# to figure them out
	#
	line = line.replace("&quot;", "\"")
	if not html_quotes :
		line = line.replace("&ldquo;", "\"")
		line = line.replace("&rdquo;", "\"")
		line = line.replace("&lsquo;", "\'")
		line = line.replace("&rsquo;", "\'")
		line = line.replace("&#8220;", "\"")
		line = line.replace("&#8221;", "\"")
		line = line.replace("&#8216;", "\'")
		line = line.replace("&#8217;", "\'")
		line = line.replace("&#147;",  "\"")
		line = line.replace("&#148;",  "\"")
		line = line.replace("&#145;",  "\'")
		line = line.replace("&#146;",  "\'")
	#endif

	for i in range(len(line)) :
		if i+1 < len(line) :
			next_char = line[i+1]
		else :
			next_char = '\n';

		#
		# DOUBLE QUOTE
		#
		if line[i] == '"' :
			do_open = True

			# Prev IS Whtespace
			if prev_char.isspace() or prev_char == '\n' :
				# Open by default
				do_open = True

				# Special case if it is a dangling quote
				if next_char.isspace() or next_char == '\n' :
					do_open = False
					if not prev_was_open :
						do_open = True
				#endif

			# Prev is NOT Whitespace
			else :
				do_open = False
				if prev_char == '-' and next_char.isalnum() :
					do_open = True
				if prev_char == '>' :
					do_open = not prev_was_open

			if do_open :
				line     = line.replace("\"",u"\u201C",1)
				prev_was_open = True
			else :
				line     = line.replace("\"",u"\u201D",1)
				prev_was_open = False
		#endif

		#
		# SINGLE QUOTE
		#
		if line[i] == '\'' :
			do_open = False

			# Prev IS Whtespace or Punctuation
			if not prev_char.isalnum() :
				# Open by default
				do_open = True
				#
				# Determining contraction vs. Open Quote
				#
				index = line.find("'",i+1)
				if not next_single_is_close(line, i+1) :
					# current is a contraction ("tell 'im this")
					do_open = False
				# endif
			#endif

			if do_open :
				line = line.replace("\'",u"\u2018",1)
			else :
				line = line.replace("\'",u"\u2019",1)
		#endif

		prev_char = line[i]

	prev_char = '\n'
	return line

# enddef convert_curly_quotes()

#############################################################
# def convert_misc():										#
#															#
#############################################################
def convert_misc(line):
	global preserve_spaces

	#
	# Compresses multiple spaces into single-space
	# The Reader DOES NOT justify text correclty when
	# multiple spaces between words are involved (it seems to
	# interpret the first space encountered as "flowable" and
	# the rest are treated as non-breaking spaces).
	#
	if not preserve_spaces :
		spaceline = line.replace("  ", " ")
		while spaceline != line :
			line      = spaceline
			spaceline = line.replace("  ", " ")

	#
	# Em-Dash Replacement
	#
	# Do triple dash first, then double-dash if any are left
	#
	line = line.replace("---",   u"\u2013")
	line = line.replace("--",    u"\u2013")

	#
	# DOS '/r' hoses up alignment.
	# Just remove the damned things
	#
	line = line.replace("\r", "")

	return line

# enddef convert_misc()


#############################################################
# def convert_button_text():								#
#															#
#############################################################
def convert_button_text(longline):

	#
	# the button may actually span multiple lines,
	# so make take only the very first line
	#
	unix = longline.split("\n")
	dos  = longline.split("\r\n")
	if (len(unix) >= len(dos)) :
		line = unix[0]
	else :
		line = dos[0]

	line = line.lstrip().rstrip()
	line = convert_curly_quotes(line)
	line = convert_misc(line)
	line = convert_html_ampersands(line)

	line = line.replace("<i>","").replace("<I>","")
	line = line.replace("<b>","").replace("<B>","")
	line = line.replace("<sub>","").replace("<SUB>","")
	line = line.replace("<sup>","").replace("<SUP>","")
	line = line.replace("<center>","").replace("<CENTER>","")
	line = line.replace("<br>","").replace("<BR>","")
	line = line.replace("<br />","").replace("<BR>","")
	#
	line = line.replace("</i>","").replace("</I>","")
	line = line.replace("</b>","").replace("</B>","")
	line = line.replace("</sub>","").replace("</SUB>","")
	line = line.replace("</sup>","").replace("</SUP>","")
	line = line.replace("</center>","").replace("</CENTER>","")
	line = line.replace("</br>","").replace("</BR>","")

	return line

# enddef convert_button_text()

#############################################################
# convert_title_text()										#
# convert_header_text()										#
#															#
#		Equivalents for alternate usage.					# 
#															#
#############################################################
convert_title_text  = convert_button_text
convert_header_text = convert_button_text

#############################################################
# def eat_unknown_tags_yum():								#
#															#
#	Tags for HTML 3.2, from the site:						#
#	<http://htmlhelp.com/reference/wilbur/alltags.html>		#
#															#
#############################################################
def eat_unknown_tags_yum(line):

	# Tags to remove
	body_tags     = "<html.*?>|</html>"                     +"|"+\
					"<head.*?>|</head>"                     +"|"+\
					"<body.*?>|</body>"                     +"|"+\
					"<title>.*?</title>"                    +"|"+\
					"<meta.*?>"                             +"|"+\
					"<!DOCTYPE.*?>"                         +"|"+\
					"<\?xml.*?\?>"

	# Remove Tag and text In Between
	defs_tags     = "<a href.*?>.*?</a>"                    +"|"+\
					"<a\s*name.*?>"                         +"|"+\
					"<!--.*?-->"                            +"|"+\
					"<address>.*?</address>"                +"|"+\
					"<applet.*?>.*?</applet>"               +"|"+\
					"<form.*?>.*?</form>"                   +"|"+\
					"<object.*?>.*?</object>"               +"|"+\
					"<select.*?>.*?</select>"               +"|"+\
					"<script.*?>.*?</script>"               +"|"+\
					"<style.*?>.*?</style>"                 +"|"+\
					"<var.*?>.*?</var>"

	fmt_tags      = "<pre>|</pre>"                          +"|"+\
					"<big>|</big>"                          +"|"+\
					"<small>|</small>"

	# List Elements, <li> is transformed to <p> in later regex 
	list_tags     = "<ol.*?>|</ol>"                         +"|"+\
					"<ul.*?>|</ul>"                         +"|"+\
					"<span.*?>|</span>"                     +"|"+\
					"<div.*?>|</div>"                       +"|"+\
					"<dl.*?>|</dl>"                         +"|"+\
					"<dt>|</dt>"

	# For table </caption>, </tr> and </td> are transformed to <br>
	table_tags    = "<table.*?>|</table>"                   +"|"+\
					"<caption.*?>"                          +"|"+\
					"<td.*?>"                               +"|"+\
					"<th.*?>"                               +"|"+\
					"<tr.*?>"

	general_tags  = "<area.*?>"                             +"|"+\
					"<basefont.*?>"                         +"|"+\
					"<base href.*?>"                        +"|"+\
					"<code>|</code>"                        +"|"+\
					"<dir.*?>|</dir>"                       +"|"+\
					"<font.*?>|</font>"                     +"|"+\
					"<frame.*?>|</frame>"                   +"|"+\
					"<form.*?>|</form>"                     +"|"+\
					"<hr.*?>"                               +"|"+\
					"<img .*?>"                             +"|"+\
					"<input.*?>"                            +"|"+\
					"<isindex.*?>"                          +"|"+\
					"<kbd>|</kbd>"                          +"|"+\
					"<link.*?>"                             +"|"+\
					"<map.*?>|</map>"                       +"|"+\
					"<menu.*?>|</menu>"                     +"|"+\
					"<option.*?>|</option>"                 +"|"+\
					"<param.*?>"

	#
	# end_tags must be removed last, since some eliminate
	# dangling tags that are handled by transforms (below)
	#
	end_tags      = "</p>"                                  +"|"+\
					"</br>"                                 +"|"+\
					"</dd>"                                 +"|"+\
					"</dfn>"                                +"|"+\
					"<hr\s*/>"                              +"|"+\
					"</li>"                                 +"|"+\
					"</a>"

	# Tags to transform to paragraphs <p> or breaks <br>
	para_tags     = "<li>"                                  +"|"+\
					"<dd>"                                  +"|"+\
					"<dfn>"                                 +"|"+\
					"</td>"                                 +"|"+\
					"</textarea>"
	br_tags       = "<br\s*.*?/>"                           +"|"+\
					"<br />"                                +"|"+\
					"</caption>"                            +"|"+\
					"</tr>"                                 +"|"+\
					"</th>"
	hn_tags       = "<h[1-9]\s+.*?>"

	# Tags to transform to italics
	ibgn_tags     = "<pre.*?>"                              +"|"+\
					"<samp.*?>"                             +"|"+\
					"<strike.*?>"                           +"|"+\
					"<strong.*?>"                           +"|"+\
					"<tt>"                                  +"|"+\
					"<u>"
	iend_tags     = "</pre>"                                +"|"+\
					"</samp>"                               +"|"+\
					"</strike>"                             +"|"+\
					"</strong>"                             +"|"+\
					"</tt>"                                 +"|"+\
					"</u>"

	# Tags for remove empty lines
	emptyline     = "^[ \t]*[\r\n]+^[ \t]*[\r\n]+"

	xre_tags      =     body_tags
	xre_tags      +="|"+defs_tags
	xre_tags      +="|"+fmt_tags
	xre_tags      +="|"+list_tags
	xre_tags      +="|"+table_tags
	xre_tags      +="|"+general_tags
	xre_tags      +="|"+end_tags
	xheadings     = re.compile(xre_tags,    re.I|re.DOTALL)
	replaceps     = re.compile(para_tags,   re.I|re.DOTALL)
	replacebr     = re.compile(br_tags,     re.I|re.DOTALL)
	replacei_bgn  = re.compile(ibgn_tags,   re.I|re.DOTALL)
	replacei_end  = re.compile(iend_tags,   re.I|re.DOTALL)
	replace_hn    = re.compile(hn_tags,     re.I|re.DOTALL)
	replace_lines = re.compile(emptyline,   re.M)

	# Removal
	line = xheadings.sub("",     line)

	# Replace with paragraph and break
	line = replaceps.sub("<p>",  line)
	line = replacebr.sub("<br>", line)

	# replace to italics
	line = replacei_bgn.sub("<i>", line)
	line = replacei_end.sub("</i>", line)

	# remove empty lines, but DO NOT remove empty <p> tags.
	line = replace_lines.sub("", line)

	# Replace <h1 class=etc> with <h1>
	line = replace_hn.sub("<h1>", line)

	return line

# enddef eat_unknown_tags_yum()

#############################################################
# def eat_stars_replace_break():							#
#															#
#############################################################
def eat_stars_replace_break(line):
	p    = re.compile("^\s*\*\s*\*\s*\*\s*$", re.M)
	line = p.sub("<starbreak>", line)
	return line
# enddef eat_p_replace_tab()


#############################################################
# def eat_nbsp_replace_space():								#
#															#
#############################################################
def eat_nbsp_replace_space(line):

	nbsp = re.compile(u"&nbsp;", re.I|re.DOTALL)
	line = nbsp.sub(" ", line)

	return line

# enddef eat_nbsp_replace_space()

#############################################################
# def eat_p_replace_tab():									#
#															#
#############################################################
def eat_p_replace_tab(line):

	p    = re.compile("<p>", re.I)
#	p    = re.compile(u"<p.*?>", re.I|re.M)
	line = p.sub("\t", line)

	return line

# enddef eat_p_replace_tab()

#############################################################
# def eat_a_replace_chapter():								#
#															#
#############################################################
def eat_a_replace_chapter(line):

	chapter_cvt = "<a name=\".*?\">(.*?)</a>"
	chapter_re  = re.compile(chapter_cvt, re.I|re.DOTALL)

	line        = chapter_re.sub("\n<chapter>\g<1>", line)

	return line

# enddef eat_a_replace_chapter()

#############################################################
# def eat_spans_replace_format():							#
#															#
#############################################################
def eat_spans_replace_format(line):

	#
	# Some spans contain nformatting, so loook for those and
	# replace them with the simple HTML formatting tags
	#    <span class="italic">USA Today</span>
	# to
	#    <i>USA Today</i>
	#
	span_italic = "<span\s*class=.italic.\s*>(.*?)</span>"
	span_bold   = "<span\s*class=.bold.\s*>(.*?)</span>"
	span_bold2  = "<span\s*style=.font-weight:\s*bold;.>(.*?)</p>"
	span_sub    = "<span\s*class=.sub.\s*>(.*?)</span>"
	span_sup    = "<span\s*class=.sup.\s*>(.*?)</span>"
	#
	# Convert to <center></center>
	# Originally included a style commend, but this one is more generic
	# <p style="text align:center"></p>
	# <p style="center"></p>
	#
	p1_center   = "<p\s*style=.text-align:\s*center;.\s*>(.*?)</p>"
	p2_center   = "<p\s*class=.center.\s*>(.*?)</p>"
	p_drop      = "<p\s*class=.drop.\s*>(.*?)</p>"

	itlc_re     = re.compile(span_italic,    re.I|re.DOTALL)
	bold_re     = re.compile(span_bold,      re.I|re.DOTALL)
	bld2_re     = re.compile(span_bold2,     re.I|re.DOTALL)
	sub_re      = re.compile(span_sub,       re.I|re.DOTALL)
	sup_re      = re.compile(span_sup,       re.I|re.DOTALL)
	center1_re  = re.compile(p1_center,      re.I|re.DOTALL)
	center2_re  = re.compile(p2_center,      re.I|re.DOTALL)
	dropcap_re  = re.compile(p_drop,         re.I|re.DOTALL)

	line = itlc_re.sub("<i>\g<0></i>",    line)
	line = bold_re.sub("<b>\g<0></b>",    line)
	line = bld2_re.sub("<b>\g<0></b>",    line)
	line = sub_re.sub("<sub>\g<0></sub>", line)
	line = sup_re.sub("<sup>\g<0></sup>", line)

	line = center1_re.sub("<center>\n\g<1>\n</center>", line)
	line = center2_re.sub("<center>\n\g<1>\n</center>", line)
	line = dropcap_re.sub("<p>\g<1>", line)

	return line

# enddef eat_spans_replace_format()


#############################################################
# def convert_html_ampersands():							#
#															#
#############################################################
def convert_html_ampersands(line):

	#
	# Basically, just global replace with equivalents
	#

	#
	# The only exception is if we want to use our algorithm
	# for curly quotes, rather than trusting existing HTML
	#
	if html_quotes :
		line = line.replace("&ldquo;", u"\u201C") # OPEN
		line = line.replace("&rdquo;", u"\u201D") # CLOSE
		line = line.replace("&lsquo;", u"\u2018") # OPEN
		line = line.replace("&rsquo;", u"\u2019") # CLOSE
		line = line.replace("&#8220;", u"\u201C")
		line = line.replace("&#8221;", u"\u201D")
		line = line.replace("&#8216;", u"\u2018")
		line = line.replace("&#8217;", u"\u2019")
		line = line.replace("&#147;",  u"\u201C")
		line = line.replace("&#148;",  u"\u201D")
		line = line.replace("&#145;",  u"\u2018") # OPEN
		line = line.replace("&#146;",  u"\u2019") # CLOSE
	else :
		line = line.replace("&ldquo;", u"\"")
		line = line.replace("&rdquo;", u"\"")
		line = line.replace("&lsquo;", u"\'")
		line = line.replace("&rsquo;", u"\'")
		line = line.replace("&#8220;", u"\"")
		line = line.replace("&#8221;", u"\"")
		line = line.replace("&#147;",  u"\"")
		line = line.replace("&#148;",  u"\"")
		line = line.replace("&#8216;", u"'")
		line = line.replace("&#8217;", u"'")
		line = line.replace("&#145;",  u"'")
		line = line.replace("&#146;",  u"'")
	#endif

	line = line.replace("&quot;",     u"\"")
	line = line.replace("&mdash;",    u"\u2013")
	line = line.replace("&ndash;",    u"\u2013")
	line = line.replace("&#8211;",    u"\u2013")
	line = line.replace("&#8212;",    u"\u2013")
	line = line.replace("&#151;",     u"\u2013")

	line = line.replace("&amp;",      u"\u0026")
	line = line.replace("&#38;",      u"\u0026")

	line = line.replace("&lt;",       u"\u003C")
	line = line.replace("&#60;",      u"\u003C")

	line = line.replace("&gt;",       u"\u003E")
	line = line.replace("&#62;",      u"\u003E")

	line = line.replace("&nbsp;",     u"\u00A0")
	line = line.replace("&#160;",     u"\u00A0")

	line = line.replace("&iexcl;",    u"\u00A1")
	line = line.replace("&#161;",     u"\u00A1")

	line = line.replace("&cent;",     u"\u00A2")
	line = line.replace("&#162;",     u"\u00A2")

	line = line.replace("&pound;",    u"\u00A3")
	line = line.replace("&#163;",     u"\u00A3")

	line = line.replace("&curren;",   u"\u00A4")
	line = line.replace("&#164;",     u"\u00A4")

	line = line.replace("&yen;",      u"\u00A5")
	line = line.replace("&#165;",     u"\u00A5")

	line = line.replace("&brvbar;",   u"\u00A6")
	line = line.replace("&#166;",     u"\u00A6")

	line = line.replace("&sect;",     u"\u00A7")
	line = line.replace("&#167;",     u"\u00A7")

	line = line.replace("&die;",      u"\u00A8")

	line = line.replace("&copy;",     u"\u00A9")
	line = line.replace("&#169;",     u"\u00A9")

	line = line.replace("&ordf;",     u"\u00AA")
	line = line.replace("&#170;",     u"\u00AA")

	line = line.replace("&laquo;",    u"\u00AB")
	line = line.replace("&#171;",     u"\u00AB")

	line = line.replace("&not;",      u"\u00AC")
	line = line.replace("&#172;",     u"\u00AC")

	line = line.replace("&shy;",      u"\u00AD")
	line = line.replace("&#173;",     u"\u00AD")

	line = line.replace("&reg;",      u"\u00AE")
	line = line.replace("&#174;",     u"\u00AE")

	line = line.replace("&macron;",   u"\u00AF")
	line = line.replace("&#175;",     u"\u00AF")

	line = line.replace("&deg;",      u"\u00B0")
	line = line.replace("&degree;",   u"\u00B0")
	line = line.replace("&#176;",     u"\u00B0")

	line = line.replace("&plusmn;",   u"\u00B1")
	line = line.replace("&#177;",     u"\u00B1")

	line = line.replace("&sup2;",     u"\u00B2")
	line = line.replace("&#178;",     u"\u00B2")

	line = line.replace("&sup3;",     u"\u00B3")
	line = line.replace("&#179;",     u"\u00B3")

	line = line.replace("&acute;",    u"\u00B4")
	line = line.replace("&#180;",     u"\u00B4")

	line = line.replace("&micro;",    u"\u00B5")
	line = line.replace("&#181;",     u"\u00B5")

	line = line.replace("&para;",     u"\u00B6")
	line = line.replace("&#182;",     u"\u00B6")

	line = line.replace("&middot;",   u"\u00B7")
	line = line.replace("&#183;",     u"\u00B7")

	# Option-8 (heavy dot)
	line = line.replace("&#149;",     u"\u2022")

	line = line.replace("&Cedilla;",  u"\u00B8")
	line = line.replace("&#184;",     u"\u00B8")

	line = line.replace("&sup1;",     u"\u00B9")
	line = line.replace("&#185;",     u"\u00B9")

	line = line.replace("&ordm;",     u"\u00BA")
	line = line.replace("&#186;",     u"\u00BA")

	line = line.replace("&raquo;",    u"\u00BB")
	line = line.replace("&#187;",     u"\u00BB")

	line = line.replace("&frac14;",   u"\u00BC")
	line = line.replace("&#188;",     u"\u00BC")

	line = line.replace("&frac12;",   u"\u00BD")
	line = line.replace("&#189;",     u"\u00BD")

	line = line.replace("&frac34;",   u"\u00BE")
	line = line.replace("&#190;",     u"\u00BE")

	line = line.replace("&iquest;",   u"\u00BF")
	line = line.replace("&#191;",     u"\u00BF")

	line = line.replace("&Agrave;",   u"\u00C0")
	line = line.replace("&#192;",     u"\u00C0")

	line = line.replace("&Aacute;",   u"\u00C1")
	line = line.replace("&#193;",     u"\u00C1")

	line = line.replace("&Acirc;",    u"\u00C2")
	line = line.replace("&#194;",     u"\u00C2")

	line = line.replace("&Atilde;",   u"\u00C3")
	line = line.replace("&#195;",     u"\u00C3")

	line = line.replace("&Auml;",     u"\u00C4")
	line = line.replace("&#196;",     u"\u00C4")

	line = line.replace("&Aring;",    u"\u00C5")
	line = line.replace("&#197;",     u"\u00C5")

	line = line.replace("&AElig;",    u"\u00C6")
	line = line.replace("&#198;",     u"\u00C6")

	line = line.replace("&Ccedil;",   u"\u00C7")
	line = line.replace("&#199;",     u"\u00C7")

	line = line.replace("&Egrave;",   u"\u00C8")
	line = line.replace("&#200;",     u"\u00C8")

	line = line.replace("&Eacute;",   u"\u00C9")
	line = line.replace("&#201;",     u"\u00C9")

	line = line.replace("&Ecirc;",    u"\u00CA")
	line = line.replace("&#202;",     u"\u00CA")

	line = line.replace("&Euml;",     u"\u00CB")
	line = line.replace("&#203;",     u"\u00CB")

	line = line.replace("&Igrave;",   u"\u00CC")
	line = line.replace("&#204;",     u"\u00CC")

	line = line.replace("&Iacute;",   u"\u00CD")
	line = line.replace("&#205;",     u"\u00CD")

	line = line.replace("&Icirc;",    u"\u00CE")
	line = line.replace("&#206;",     u"\u00CE")

	line = line.replace("&Iuml;",     u"\u00CF")
	line = line.replace("&#207;",     u"\u00CF")

	line = line.replace("&ETH;",      u"\u00D0")
	line = line.replace("&#208;",     u"\u00D0")

	line = line.replace("&Ntilde;",   u"\u00D1")
	line = line.replace("&#209;",     u"\u00D1")

	line = line.replace("&Ograve;",   u"\u00D2")
	line = line.replace("&#210;",     u"\u00D2")

	line = line.replace("&Oacute;",   u"\u00D3")
	line = line.replace("&#211;",     u"\u00D3")

	line = line.replace("&Ocirc;",    u"\u00D4")
	line = line.replace("&#212;",     u"\u00D4")

	line = line.replace("&Otilde;",   u"\u00D5")
	line = line.replace("&#213;",     u"\u00D5")

	line = line.replace("&Ouml;",     u"\u00D6")
	line = line.replace("&#214;",     u"\u00D6")

	line = line.replace("&times;",    u"\u00D7")
	line = line.replace("&#215;",     u"\u00D7")

	line = line.replace("&Oslash;",   u"\u00D8")
	line = line.replace("&#216;",     u"\u00D8")

	line = line.replace("&Ugrave;",   u"\u00D9")
	line = line.replace("&#217;",     u"\u00D9")

	line = line.replace("&Uacute;",   u"\u00DA")
	line = line.replace("&#218;",     u"\u00DA")

	line = line.replace("&Ucirc;",    u"\u00DB")
	line = line.replace("&#219;",     u"\u00DB")

	line = line.replace("&Uuml;",     u"\u00DC")
	line = line.replace("&#220;",     u"\u00DC")

	line = line.replace("&Yacute;",   u"\u00DD")
	line = line.replace("&#221;",     u"\u00DD")

	line = line.replace("&THORN;",    u"\u00DE")
	line = line.replace("&#222;",     u"\u00DE")

	line = line.replace("&szlig;",    u"\u00DF")
	line = line.replace("&#223;",     u"\u00DF")

	line = line.replace("&agrave;",   u"\u00E0")
	line = line.replace("&#224;",     u"\u00E0")

	line = line.replace("&aacute;",   u"\u00E1")
	line = line.replace("&#225;",     u"\u00E1")

	line = line.replace("&acirc;",    u"\u00E2")
	line = line.replace("&#226;",     u"\u00E2")

	line = line.replace("&atilde;",   u"\u00E3")
	line = line.replace("&#227;",     u"\u00E3")

	line = line.replace("&auml;",     u"\u00E4")
	line = line.replace("&#228;",     u"\u00E4")

	line = line.replace("&aring;",    u"\u00E5")
	line = line.replace("&#229;",     u"\u00E5")

	line = line.replace("&aelig;",    u"\u00E6")
	line = line.replace("&#230;",     u"\u00E6")

	line = line.replace("&ccedil;",   u"\u00E7")
	line = line.replace("&#231;",     u"\u00E7")

	line = line.replace("&egrave;",   u"\u00E8")
	line = line.replace("&#232;",     u"\u00E8")

	line = line.replace("&eacute;",   u"\u00E9")
	line = line.replace("&#233;",     u"\u00E9")

	line = line.replace("&ecirc;",    u"\u00EA")
	line = line.replace("&#234;",     u"\u00EA")

	line = line.replace("&euml;",     u"\u00EB")
	line = line.replace("&#235;",     u"\u00EB")

	line = line.replace("&igrave;",   u"\u00EC")
	line = line.replace("&#236;",     u"\u00EC")

	line = line.replace("&iacute;",   u"\u00ED")
	line = line.replace("&#237;",     u"\u00ED")

	line = line.replace("&icirc;",    u"\u00EE")
	line = line.replace("&#238;",     u"\u00EE")

	line = line.replace("&iuml;",     u"\u00EF")
	line = line.replace("&#239;",     u"\u00EF")

	line = line.replace("&eth;",      u"\u00F0")
	line = line.replace("&#240;",     u"\u00F0")

	line = line.replace("&ntilde;",   u"\u00F1")
	line = line.replace("&#241;",     u"\u00F1")

	line = line.replace("&ograve;",   u"\u00F2")
	line = line.replace("&#242;",     u"\u00F2")

	line = line.replace("&oacute;",   u"\u00F3")
	line = line.replace("&#243;",     u"\u00F3")

	line = line.replace("&ocirc;",    u"\u00F4")
	line = line.replace("&#244;",     u"\u00F4")

	line = line.replace("&otilde;",   u"\u00F5")
	line = line.replace("&#245;",     u"\u00F5")

	line = line.replace("&ouml;",     u"\u00F6")
	line = line.replace("&#246;",     u"\u00F6")

	line = line.replace("&divide;",   u"\u00F7")
	line = line.replace("&#247;",     u"\u00F7")

	line = line.replace("&oslash;",   u"\u00F8")
	line = line.replace("&#248;",     u"\u00F8")

	line = line.replace("&ugrave;",   u"\u00F9")
	line = line.replace("&#249;",     u"\u00F9")

	line = line.replace("&uacute;",   u"\u00FA")
	line = line.replace("&#250;",     u"\u00FA")

	line = line.replace("&ucirc;",    u"\u00FB")
	line = line.replace("&#251;",     u"\u00FB")

	line = line.replace("&uuml;",     u"\u00FC")
	line = line.replace("&#252;",     u"\u00FC")

	line = line.replace("&yacute;",   u"\u00FD")
	line = line.replace("&#253;",     u"\u00FD")

	line = line.replace("&thorn;",    u"\u00FE")
	line = line.replace("&#254;",     u"\u00FE")

	line = line.replace("&yuml;",     u"\u00FF")
	line = line.replace("&#255;",     u"\u00FF")

	line = line.replace("&lowast;",   u"\u2217")
	line = line.replace("&#8727;",    u"\u2217")

	line = line.replace("&minus;",    u"\u2212")
	line = line.replace("&#8722;",    u"\u2212")

	line = line.replace("&cong;",     u"\u2245")
	line = line.replace("&#8773;",    u"\u2245")

	line = line.replace("&Agr;",      u"\u0391")
	line = line.replace("&Bgr;",      u"\u0392")
	line = line.replace("&KHgr;",     u"\u03A7")

	line = line.replace("&Delta;",    u"\u0394")
	line = line.replace("&#916;",     u"\u0394")

	line = line.replace("&Egr;",      u"\u0395")
	line = line.replace("&PHgr;",     u"\u03A6")

	line = line.replace("&Gamma;",    u"\u0393")
	line = line.replace("&#915;",     u"\u0393")

	line = line.replace("&EEgr;",     u"\u0397")
	line = line.replace("&Igr;",      u"\u0399")

	line = line.replace("&thetav;",   u"\u03D1")
	line = line.replace("&Kgr;",      u"\u039A")

	line = line.replace("&Lambda;",   u"\u039B")
	line = line.replace("&#923;",     u"\u039B")

	line = line.replace("&Mgr;",      u"\u039C")
	line = line.replace("&Ngr;",      u"\u039D")
	line = line.replace("&Ogr;",      u"\u039F")

	line = line.replace("&Pi;",       u"\u03A0")
	line = line.replace("&#928;",     u"\u03A0")

	line = line.replace("&Theta;",    u"\u0398")
	line = line.replace("&#920;",     u"\u0398")

	line = line.replace("&Rgr;",      u"\u03A1")

	line = line.replace("&Sigma;",    u"\u03A3")
	line = line.replace("&#931;",     u"\u03A3")

	line = line.replace("&Tgr;",      u"\u03A4")

	line = line.replace("&Upsi;",     u"\u03A5")
	line = line.replace("&#933;",     u"\u03A5")

	line = line.replace("&Omega;",    u"\u03A9")
	line = line.replace("&#937;",     u"\u03A9")

	line = line.replace("&Xi;",       u"\u039E")
	line = line.replace("&#958;",     u"\u039E")

	line = line.replace("&Psi;",      u"\u03A8")
	line = line.replace("&#936;",     u"\u03A8")

	line = line.replace("&Zgr;",      u"\u0396")
	line = line.replace("&there4;",   u"\u2234")
	line = line.replace("&perp;",     u"\u22A5")

	line = line.replace("&alpha;",    u"\u03B1")
	line = line.replace("&#945;",     u"\u03B1")

	line = line.replace("&beta;",     u"\u03B2")
	line = line.replace("&#946;",     u"\u03B2")

	line = line.replace("&gamma;",    u"\u03B3")
	line = line.replace("&#947;",     u"\u03B3")

	line = line.replace("&delta;",    u"\u03B4")
	line = line.replace("&#948;",     u"\u03B4")

	line = line.replace("&epsi;",     u"\u03B5")
	line = line.replace("&#949;",     u"\u03B5")

	line = line.replace("&zeta;",     u"\u03B6")
	line = line.replace("&#950;",     u"\u03B6")

	line = line.replace("&eta;",      u"\u03B7")
	line = line.replace("&#951;",     u"\u03B7")

	line = line.replace("&thetas;",   u"\u03B8")
	line = line.replace("&#952;",     u"\u03B8")

	line = line.replace("&iota;",     u"\u03B9")
	line = line.replace("&#953;",     u"\u03B9")

	line = line.replace("&kappa;",    u"\u03BA")
	line = line.replace("&#954;",     u"\u03BA")

	line = line.replace("&lambda;",   u"\u03BB")
	line = line.replace("&#955;",     u"\u03BB")

	line = line.replace("&mu;",       u"\u03BC")
	line = line.replace("&#956;",     u"\u03BC")

	line = line.replace("&nu;",       u"\u03BD")
	line = line.replace("&#957;",     u"\u03BD")

	line = line.replace("&xi;",       u"\u03BE")
	line = line.replace("&#958;",     u"\u03BE")

	line = line.replace("&ogr;",      u"\u03BF")

	line = line.replace("&pi;",       u"\u03C0")
	line = line.replace("&#960;",     u"\u03C0")

	line = line.replace("&rho;",      u"\u03C1")
	line = line.replace("&#961;",     u"\u03C1")

	line = line.replace("&sfgr;",     u"\u03C2")
	line = line.replace("&#962;",     u"\u03C2")

	line = line.replace("&sigma;",    u"\u03C3")
	line = line.replace("&#963;",     u"\u03C3")

	line = line.replace("&tau;",      u"\u03C4")
	line = line.replace("&#964;",     u"\u03C4")

	line = line.replace("&upsi;",     u"\u03C5")
	line = line.replace("&#965;",     u"\u03C5")

	line = line.replace("&phis;",     u"\u03C6")
	line = line.replace("&#966;",     u"\u03C6")

	line = line.replace("&phiv;",     u"\u03D5")
	line = line.replace("&#966;",     u"\u03D5")

	line = line.replace("&chi;",      u"\u03C7")
	line = line.replace("&#967;",     u"\u03C7")

	line = line.replace("&psi;",      u"\u03C8")
	line = line.replace("&#968;",     u"\u03C8")

	line = line.replace("&omega;",    u"\u03C9")
	line = line.replace("&#969;",     u"\u03C9")

	line = line.replace("&piv;",      u"\u03D6")
	line = line.replace("&#982;",     u"\u03D6")

	line = line.replace("&sim;",      u"\u223C")
	line = line.replace("&#8764;",    u"\u223C")

	line = line.replace("&vprime;",   u"\u2032")
	line = line.replace("&#8242;",    u"\u2032")

	line = line.replace("&le;",       u"\u2264")
	line = line.replace("&#8804;",    u"\u2264")

	line = line.replace("&infin;",    u"\u221E")
	line = line.replace("&#8734;",    u"\u221E")

	line = line.replace("&fnof;",     u"\u0192")
	line = line.replace("&#402;",     u"\u0192")

	line = line.replace("&clubs;",    u"\u2663")
	line = line.replace("&#9827;",    u"\u2663")

	line = line.replace("&diams;",    u"\u2666")
	line = line.replace("&#9830;",    u"\u2666")

	line = line.replace("&hearts;",   u"\u2665")
	line = line.replace("&#9829;",    u"\u2665")

	line = line.replace("&spades;",   u"\u2660")
	line = line.replace("&#9824;",    u"\u2660")

	line = line.replace("&harr;",     u"\u2194")
	line = line.replace("&#8596;",    u"\u2194")

	line = line.replace("&larr;",     u"\u2190")
	line = line.replace("&#8656;",    u"\u2190")

	line = line.replace("&uarr;",     u"\u2191")
	line = line.replace("&#8657;",    u"\u2191")

	line = line.replace("&rarr;",     u"\u2192")
	line = line.replace("&#8658;",    u"\u2192")

	line = line.replace("&darr;",     u"\u2193")
	line = line.replace("&#8659;",    u"\u2193")

	line = line.replace("&Prime;",    u"\u2033")
	line = line.replace("&#8243;",    u"\u2033")

	line = line.replace("&ge;",       u"\u2265")
	line = line.replace("&#8805;",    u"\u2265")

	line = line.replace("&prop;",     u"\u221D")
	line = line.replace("&#8733;",    u"\u221D")

	line = line.replace("&part;",     u"\u2202")
	line = line.replace("&#8706;",    u"\u2202")

	line = line.replace("&bull;",     u"\u2022")
	line = line.replace("&#8226;",    u"\u2022")

	line = line.replace("&ne;",       u"\u2260")
	line = line.replace("&#8800;",    u"\u2260")

	line = line.replace("&equiv;",    u"\u2261")
	line = line.replace("&#8801;",    u"\u2261")

	line = line.replace("&ap;",       u"\u2248")
	line = line.replace("&#8776;",    u"\u2248")

	line = line.replace("&hellip;",   u"\u2026")
	line = line.replace("&#8230;",    u"\u2026")

	line = line.replace("&aleph;",    u"\u2135")
	line = line.replace("&#8501;",    u"\u2135")

	line = line.replace("&image;",    u"\u2111")
	line = line.replace("&#8465;",    u"\u2111")

	line = line.replace("&real;",     u"\u211C")
	line = line.replace("&#8476;",    u"\u211C")

	line = line.replace("&weierp;",   u"\u2118")
	line = line.replace("&#8472;",    u"\u2118")

	line = line.replace("&otimes;",   u"\u2297")
	line = line.replace("&#8855;",    u"\u2297")

	line = line.replace("&oplus;",    u"\u2295")
	line = line.replace("&#8853;",    u"\u2295")

	line = line.replace("&empty;",    u"\u2205")
	line = line.replace("&#8709;",    u"\u2205")

	line = line.replace("&cap;",      u"\u2229")
	line = line.replace("&#8745;",    u"\u2229")

	line = line.replace("&cup;",      u"\u222A")
	line = line.replace("&#8746;",    u"\u222A")

	line = line.replace("&sup;",      u"\u2283")
	line = line.replace("&#8835;",    u"\u2283")

	line = line.replace("&supe;",     u"\u2287")
	line = line.replace("&#8839;",    u"\u2287")

	line = line.replace("&nsub;",     u"\u2284")
	line = line.replace("&#8836;",    u"\u2284")

	line = line.replace("&sub;",      u"\u2282")
	line = line.replace("&#8834;",    u"\u2282")

	line = line.replace("&sube;",     u"\u2286")
	line = line.replace("&#8838;",    u"\u2286")

	line = line.replace("&isin;",     u"\u2208")
	line = line.replace("&#8712;",    u"\u2208")

	line = line.replace("&notin;",    u"\u2209")
	line = line.replace("&#8713;",    u"\u2209")

	line = line.replace("&ang;",      u"\u2220")
	line = line.replace("&#8736;",    u"\u2220")

	line = line.replace("&nabla;",    u"\u2207")
	line = line.replace("&#8711;",    u"\u2207")

	line = line.replace("&trade;",    u"\u2122")
	line = line.replace("&#8482;",    u"\u2122")

	line = line.replace("&prod;",     u"\u220F")
	line = line.replace("&#8719;",    u"\u220F")

	line = line.replace("&radic;",    u"\u221A")
	line = line.replace("&#8730;",    u"\u221A")

	line = line.replace("&sdot;",     u"\u22C5")
	line = line.replace("&#8901;",    u"\u22C5")

	line = line.replace("&and;",      u"\u2227")
	line = line.replace("&#8743;",    u"\u2227")

	line = line.replace("&or;",       u"\u2228")
	line = line.replace("&#8744;",    u"\u2228")

	line = line.replace("&hArr;",     u"\u21D4")
	line = line.replace("&#8660;",    u"\u21D4")

	line = line.replace("&lArr;",     u"\u21D0")
	line = line.replace("&#8656;",    u"\u21D0")

	line = line.replace("&uArr;",     u"\u21D1")
	line = line.replace("&#8657;",    u"\u21D1")

	line = line.replace("&rArr;",     u"\u21D2")
	line = line.replace("&#8658;",    u"\u21D2")

	line = line.replace("&dArr;",     u"\u21D3")
	line = line.replace("&#8659;",    u"\u21D3")

	line = line.replace("&loz;",      u"\u25CA")
	line = line.replace("&#9674;",    u"\u25CA")

	line = line.replace("&lang;",     u"\u2329")
	line = line.replace("&#9001;",    u"\u2329")

	line = line.replace("&sum;",      u"\u2211")
	line = line.replace("&#8721;",    u"\u2211")

	line = line.replace("&lceil;",    u"\u2308")
	line = line.replace("&#8968;",    u"\u2308")

	line = line.replace("&lfloor;",   u"\u230A")
	line = line.replace("&#8970;",    u"\u230A")

	line = line.replace("&rang;",     u"\u232A")
	line = line.replace("&#9002;",    u"\u232A")

	line = line.replace("&int;",      u"\u222B")
	line = line.replace("&#8747;",    u"\u222B")

	return line

# enddef convert_html_ampersands()
