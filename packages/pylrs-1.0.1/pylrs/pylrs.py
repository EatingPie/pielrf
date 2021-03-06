"""
    pylrs.py -- a package to create LRS (and LRF) e-Books for the Sony PRS-500.
"""

import os
import re
import codecs
import sys
from datetime import date
try:
    from elementtree.ElementTree import (Element, SubElement)
except ImportError:
    from xml.etree.ElementTree import (Element, SubElement)

from elements import ElementWriter
from pylrf import (LrfWriter, LrfObject, LrfTag, LrfToc,
        STREAM_COMPRESSED, LrfTagStream, LrfStreamBase, IMAGE_TYPE_ENCODING,
        BINDING_DIRECTION_ENCODING, LINE_TYPE_ENCODING, LrfFileStream,
        STREAM_FORCE_COMPRESSED)

PYLRS_VERSION = "1.0.1"

DEFAULT_SOURCE_ENCODING = "cp1252"      # defualt is us-windows character set
DEFAULT_GENREADING      = "f"           # default is yes to lrf, no to lrs

#
# Acknowledgement:
#   This software would not have been possible without the pioneering
#   efforts of the author of lrf2lrs.py, Igor Skochinsky.
#
# Copyright (c) 2007 Mike Higgins (Falstaff)
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# Check www.falstaffshouse.com for possible updates to this code.
# Email contact: falstaff (at) falstaffshouse.com

#
# Change History:
#
# V1.0 06 Feb 2007
# Initial Release.
#

#
# Current limitations and bugs:
#   Bug: using two instances of Book() at the same time can cause
#        incorrect output if any default styles are used.  Workaround:
#        supply all styles explicitly, or use only one Book class at a time.
#   Bug: Does not check if most setting values are valid unless lrf is created.
#
#   Unsupported objects: MiniPage, SimpleTextBlock, Canvas, Window,
#                        PopUpWindow, Sound, Import, SoundStream,
#                        ObjectInfo
#
#   Does not support background images for blocks or pages.
#
#   The only button type supported are JumpButtons.
#
#   None of the Japanese language tags are supported.
#
#   Other unsupported tags: PageDiv, SoundStop, Wait, pos,
#                           Plot, Image (outside of ImageBlock), 
#                           EmpLine, EmpDots
#
#   Tested on Python 2.4 and 2.5, Windows XP and PRS-500.
#

class LrsError(Exception):
    pass


def _checkExists(filename):
    if not os.path.exists(filename):
        raise LrsError, "file '%s' not found" % filename


def _formatXml(root):
    """ A helper to make the LRS output look nicer. """
    for elem in root.getiterator():
        if len(elem) > 0 and (not elem.text or not elem.text.strip()):
            elem.text = "\n"
        if not elem.tail or not elem.tail.strip():
            elem.tail = "\n"



def ElementWithText(tag, text, **extra):
    """ A shorthand function to create Elements with text. """
    e = Element(tag, **extra)
    e.text = text
    return e



def ElementWithReading(tag, text, reading=False):
    """ A helper function that creates reading attributes. """
    
    # note: old lrs2lrf parser only allows reading = ""

    if text is None:
        readingText = ""
    elif isinstance(text, basestring):
        readingText = text
    else:
        # assumed to be a sequence of (name, sortas)
        readingText = text[1]
        text = text[0]

    if not reading:
        readingText = ""

    return ElementWithText(tag, text, reading=readingText)



def appendTextElements(e, contentsList, se):
    """ A helper function to convert text streams into the proper elements. """

    def uconcat(text, newText, se):
        if type(newText) != type(text):
            if type(text) is str:
                text = text.decode(se)
            else:
                newText = newText.decode(se)
                
        return text + newText


    e.text = ""
    lastElement = None

    for content in contentsList:
        if not isinstance(content, Text):
            newElement = content.toElement(se)
            if newElement is None:
                continue
            lastElement = newElement
            lastElement.tail = ""
            e.append(lastElement)
        else:
            if lastElement is None:
                e.text = uconcat(e.text, content.text, se)
            else:
                lastElement.tail = uconcat(lastElement.tail, content.text, se)



class Delegator(object):
    """ A mixin class to create delegated methods that create elements. """
    def __init__(self, delegates):
        self.delegates = delegates
        self.delegatedMethods = []
        #self.delegatedSettingsDict = {}
        #self.delegatedSettings = []
        for d in delegates:
            d.parent = self
            methods = d.getMethods()
            self.delegatedMethods += methods
            for m in methods:
                setattr(self, m, getattr(d, m))

            """
            for setting in d.getSettings():
                if isinstance(setting, basestring):
                    setting = (d, setting)
                delegates = \
                        self.delegatedSettingsDict.setdefault(setting[1], [])
                delegates.append(setting[0])
                self.delegatedSettings.append(setting)
            """
                    

    def applySetting(self, name, value, testValid=False):
        applied = False
        if name in self.getSettings():
            setattr(self, name, value)
            applied = True
            
        for d in self.delegates:
            if hasattr(d, "applySetting"):
                applied = applied or d.applySetting(name, value)
            else:
                if name in d.getSettings():
                    setattr(d, name, value)
                    applied = True
            
        if testValid and not applied:
            raise LrsError, "setting %s not valid" % name
 
        return applied
     
     
    def applySettings(self, settings, testValid=False):
        for (setting, value) in settings.items():
            self.applySetting(setting, value, testValid)
            """
            if setting not in self.delegatedSettingsDict:
                raise LrsError, "setting %s not valid" % setting
            delegates = self.delegatedSettingsDict[setting]
            for d in delegates:
                setattr(d, setting, value)
            """


    def appendDelegates(self, element, sourceEncoding):
        for d in self.delegates:
            e = d.toElement(sourceEncoding)
            if e is not None:
                if isinstance(e, list):
                    for e1 in e: element.append(e1)
                else:
                    element.append(e)


    def appendReferencedObjects(self, parent):
        for d in self.delegates:
            d.appendReferencedObjects(parent)
 
            
    def getMethods(self):
        return self.delegatedMethods


    def getSettings(self):
        return []
    

    def toLrfDelegates(self, lrfWriter):
        for d in self.delegates:
            d.toLrf(lrfWriter)


    def toLrf(self, lrfWriter):
        self.toLrfDelegates(lrfWriter)



class LrsAttributes(object):
    """ A mixin class to handle default and user supplied attributes. """
    def __init__(self, defaults, alsoAllow=None, **settings):
        if alsoAllow is None:
            alsoAllow = []
        self.attrs = defaults.copy()
        for (name, value) in settings.items():
            if name not in self.attrs and name not in alsoAllow:
                raise LrsError, "%s does not support setting %s" % \
                        (self.__class__.__name__, name)
            if type(value) is int:
                value = str(value)
            self.attrs[name] = value


class LrsContainer(object):
    """ This class is a mixin class for elements that are contained in or
        contain an unknown number of other elements.
    """
    def __init__(self, validChildren):
        self.parent = None
        self.contents = []
        self.validChildren = validChildren
            
        
    def appendReferencedObjects(self, parent):
        for c in self.contents:
            c.appendReferencedObjects(parent)
            
            
    def setParent(self, parent):
        if self.parent is not None:
            raise LrsError, "object already has parent"

        self.parent = parent


    def append(self, content, convertText=True):
        """ 
            Appends valid objects to container.  Can auto-covert text strings
            to Text objects.
        """
        for validChild in self.validChildren:
            if isinstance(content, validChild):
                break
        else:
            raise LrsError, "can't append %s to %s" % \
                    (content.__class__.__name__,
                    self.__class__.__name__)

        if convertText and isinstance(content, basestring):
            content = Text(content)

        content.setParent(self)
        
        if isinstance(content, LrsObject):
            content.assignId()
            
        self.contents.append(content)
        return self



class LrsObject(object):
    """ A mixin class for elements that need an object id. """
    NextObjId = 0
 
    @classmethod
    def getNextObjId(selfClass):
        selfClass.NextObjId += 1
        return selfClass.NextObjId

    def __init__(self, assignId=False):
        if assignId:
            self.objId = LrsObject.getNextObjId()
        else:
            self.objId = 0


    def assignId(self):
        if self.objId != 0:
            raise LrsError, "id already assigned to " + self.__class__.__name__
        
        self.objId = LrsObject.getNextObjId()
        
        
    def lrsObjectElement(self, name, objlabel="objlabel", labelName=None,
            labelDecorate=True, **settings):
        element = Element(name)
        element.attrib["objid"] = str(self.objId)
        if labelName is None:
            labelName = name
        if labelDecorate:
            label = "%s.%d" % (labelName, self.objId)
        else:
            label = str(self.objId)
        element.attrib[objlabel] = label
        element.attrib.update(settings)
        return element



class Book(Delegator):
    """ 
        Main class for any lrs or lrf.  All objects must be appended to
        the Book class in some way or another in order to be rendered as
        an LRS or LRF file.
        
        The following settings are available on the contructor of Book:

        author="book author" or author=("book author, "sort as")
        Author of the book.
        
        title="book title" or title=("book title", "sort as")
        Title of the book.
 
        sourceencoding="codec"
        Gives the assumed encoding for all non-unicode strings.
        
        
        thumbnail="thumbnail file name"
        A small (80x80?) graphics file with a thumbnail of the book's cover.
        
        bookid="book id"
        A unique id for the book.

        textstyledefault=<dictionary of settings>
        Sets the default values for all TextStyles.

        pagetstyledefault=<dictionary of settings>
        Sets the default values for all PageStyles.

        blockstyledefault=<dictionary of settings>
        Sets the default values for all BlockStyles.

        booksetting=BookSetting()
        Override the default BookSetting.

        setdefault=SetDefault()
        Override the defalut SetDefault.
        
        There are several other settings -- see the BookInfo class for more.       
    """
    def __init__(self, textstyledefault=None, blockstyledefault=None,
                       pagestyledefault=None,
                       optimizeTags=False,
                       optimizeCompression=False,
                       **settings):

        self.parent = None  # we are the top of the parent chain

        if "thumbnail" in settings:
            _checkExists(settings["thumbnail"])

        # highly experimental -- use with caution
        self.optimizeTags = optimizeTags
        self.optimizeCompression = optimizeCompression

        TextStyle.resetDefaults()
        BlockStyle.resetDefaults()
        PageStyle.resetDefaults()

        if textstyledefault is not None:
            TextStyle.setDefaults(textstyledefault)

        if blockstyledefault is not None:
            BlockStyle.setDefaults(blockstyledefault)

        if pagestyledefault is not None:
            PageStyle.setDefaults(pagestyledefault)

        Page.defaultPageStyle = PageStyle()
        TextBlock.defaultTextStyle = TextStyle()
        TextBlock.defaultBlockStyle = BlockStyle()
        LrsObject.nextObjId = 1

        Delegator.__init__(self, [BookInformation(), Main(),
            Template(), Style(), Solos(), Objects()])

        self.sourceencoding = None
        
        # apply default settings
        self.applySetting("genreading", DEFAULT_GENREADING)
        self.applySetting("sourceencoding", DEFAULT_SOURCE_ENCODING)
        
        self.applySettings(settings, testValid=True)
    

    def getSettings(self):
        return ["sourceencoding"]
    
    
    def append(self, content):
        """ Find and invoke the correct appender for this content. """

        className = content.__class__.__name__
        try:
            method = getattr(self, "append" + className)
        except AttributeError:
            raise LrsError, "can't append %s to Book" % className

        method(content)


    def renderLrs(self, lrsFilename):
        lrsFile = codecs.open(lrsFilename, "wb", encoding="utf-16")
        self.render(lrsFile)
        lrsFile.close()


    def renderLrf(self, lrfFilename):
        self.appendReferencedObjects(self)
        lrfFile = file(lrfFilename, "wb")
        lrfWriter = LrfWriter(self.sourceencoding)

        lrfWriter.optimizeTags = self.optimizeTags
        lrfWriter.optimizeCompression = self.optimizeCompression

        self.toLrf(lrfWriter)
        lrfWriter.writeFile(lrfFile)
        lrfFile.close()


    def toElement(self, se):
        root = Element("BBeBXylog", version="1.0")
        root.append(Element("Property"))
        self.appendDelegates(root, self.sourceencoding)
        return root


    def render(self, f):
        """ Write the book as an LRS to file f. """

        self.appendReferencedObjects(self)
        
        # create the root node, and populate with the parts of the book

        root = self.toElement(self.sourceencoding)

        # now, add some newlines to make it easier to look at

        _formatXml(root)

        writer = ElementWriter(root, header=True,
                               sourceEncoding=self.sourceencoding,
                               spaceBeforeClose=False)
        writer.write(f)
        
       
        





class BookInformation(Delegator):
    """ Just a container for the Info and TableOfContents elements. """
    def __init__(self):
        Delegator.__init__(self, [Info(), TableOfContents()])


    def toElement(self, se):
        bi = Element("BookInformation")
        self.appendDelegates(bi, se)
        return bi



class Info(Delegator):
    """ Just a container for the BookInfo and DocInfo elements. """
    def __init__(self):
        self.genreading = DEFAULT_GENREADING
        Delegator.__init__(self, [BookInfo(), DocInfo()])


    def getSettings(self):
        return ["genreading"] #+ self.delegatedSettings


    def toElement(self, se):
        info = Element("Info", version="1.1")
        info.append(
            self.delegates[0].toElement(se, reading="s" in self.genreading))
        info.append(self.delegates[1].toElement(se))
        return info


    def toLrf(self, lrfWriter):
        # this info is set in XML form in the LRF
        info = Element("Info", version="1.1")
        #self.appendDelegates(info)
        info.append(
            self.delegates[0].toElement(lrfWriter.getSourceEncoding(), reading="f" in self.genreading))
        info.append(self.delegates[1].toElement(lrfWriter.getSourceEncoding()))

        # look for the thumbnail file and get the filename      
        tnail = info.find("DocInfo/CThumbnail")
        if tnail is not None:
            lrfWriter.setThumbnailFile(tnail.get("file"))
            # does not work: info.remove(tnail)


        _formatXml(info)
        
        # fix up the doc info to match the LRF format
        # NB: generates an encoding attribute, which lrs2lrf does not
        xmlInfo = ElementWriter(info, header=True, sourceEncoding=lrfWriter.getSourceEncoding(),
                                spaceBeforeClose=False).toString()
        
        xmlInfo = re.sub(r"<CThumbnail.*?>\n", "", xmlInfo)
        xmlInfo = xmlInfo.replace("SumPage>", "Page>")
        lrfWriter.docInfoXml = xmlInfo



class TableOfContents(object):
    def __init__(self):
        self.tocEntries = []

 
    def appendReferencedObjects(self, parent):
        pass
            
    
    def getMethods(self):
        return ["addTocEntry"]

 
    def getSettings(self):
        return []


    def addTocEntry(self, tocLabel, textBlock):
        if not isinstance(textBlock, TextBlock):
            raise LrsError, "TOC destination must be a TextBlock"

        if textBlock.parent is None or not isinstance(textBlock.parent, Page):
            raise LrsError, "TOC text block must be already appended to a page"

        if textBlock.parent.parent is None:
            raise LrsError, \
                    "TOC destination page must be already appended to a book"

        self.tocEntries.append(TocLabel(tocLabel, textBlock))
        textBlock.tocLabel = tocLabel
 
        
    def toElement(self, se):
        if len(self.tocEntries) == 0:
            return None

        toc = Element("TOC")
        
        for t in self.tocEntries:
            toc.append(t.toElement(se))
            
        return toc
    

    def toLrf(self, lrfWriter):
        if len(self.tocEntries) == 0:
            return

        toc = []
        for t in self.tocEntries:
            toc.append((t.textBlock.parent.objId, t.textBlock.objId, t.label))

        lrfToc = LrfToc(LrsObject.getNextObjId(), toc, lrfWriter.getSourceEncoding())
        lrfWriter.append(lrfToc)
        lrfWriter.setTocObject(lrfToc)



class TocLabel(object):
    def __init__(self, label, textBlock):
        self.label = label
        self.textBlock = textBlock
        
        
    def toElement(self, se):
        return ElementWithText("TocLabel", self.label,
                 refobj=str(self.textBlock.objId),
                 refpage=str(self.textBlock.parent.objId))
    


class BookInfo(object):
    def __init__(self):
        self.title = "Untitled"        
        self.author = "Anonymous"       
        self.bookid = None
        self.pi = None
        self.isbn = None
        self.publisher = None
        self.freetext = "\n\n"
        self.label = None
        self.category = None
        self.classification = None

    def appendReferencedObjects(self, parent):
        pass
    
    
    def getMethods(self):
        return []


    def getSettings(self):
        return ["author", "title", "bookid", "isbn", "publisher", 
                "freetext", "label", "category", "classification"]


    def _appendISBN(self, bi):
        pi = Element("ProductIdentifier")
        isbnElement = ElementWithText("ISBNPrintable", self.isbn)
        isbnValueElement = ElementWithText("ISBNValue",
                self.isbn.replace("-", ""))

        pi.append(isbnElement)
        pi.append(isbnValueElement)
        bi.append(pi)


    def toElement(self, se, reading=False):
        bi = Element("BookInfo")
        bi.append(ElementWithReading("Title", self.title, reading=reading))
        bi.append(ElementWithReading("Author", self.author, reading=reading))
        bi.append(ElementWithText("BookID", self.bookid))
        if self.isbn is not None:
            self._appendISBN(bi)

        if self.publisher is not None:
            bi.append(ElementWithReading("Publisher", self.publisher))

        bi.append(ElementWithReading("Label", self.label, reading=reading))
        bi.append(ElementWithText("Category", self.category))
        bi.append(ElementWithText("Classification", self.classification))
        bi.append(ElementWithText("FreeText", self.freetext))
        return bi



class DocInfo(object):
    def __init__(self):
        self.thumbnail = None
        self.language = "en"
        self.creator  = None
        self.creationdate = date.today().isoformat()
        self.producer = "pylrs 0.1"
        self.numberofpages = "0"


    def appendReferencedObjects(self, parent):
        pass
    
    
    def getMethods(self):
        return []

 
    def getSettings(self):
        return ["thumbnail", "language", "creator", "creationdate",
                "producer", "numberofpages"]


    def toElement(self, se):
        docInfo = Element("DocInfo")

        if self.thumbnail is not None:
            docInfo.append(Element("CThumbnail", file=self.thumbnail))

        docInfo.append(ElementWithText("Language", self.language))
        docInfo.append(ElementWithText("Creator", self.creator))
        docInfo.append(ElementWithText("CreationDate", self.creationdate))
        docInfo.append(ElementWithText("Producer", self.producer))
        docInfo.append(ElementWithText("SumPage", str(self.numberofpages)))
        return docInfo



class Main(LrsContainer):
    def __init__(self):
        LrsContainer.__init__(self, [Page])     
        

    def getMethods(self):
        return ["appendPage", "appendTocPage", "appendChapter", "Page"]


    def getSettings(self):
        return []


    def Page(self, *args, **kwargs):
        p = Page(*args, **kwargs)
        self.append(p)
        return p


    def appendPage(self, page):
        self.append(page)

    def appendTocPage(self, page):
        self.append(page)

    def appendChapter(self, page):
        self.append(page)


    def toElement(self, sourceEncoding):
        main = Element(self.__class__.__name__)

        for page in self.contents:
            main.append(page.toElement(sourceEncoding))
            
        return main


    def toLrf(self, lrfWriter):
        pageIds = []

        # set this id now so that pages can see it
        pageTreeId = LrsObject.getNextObjId()
        lrfWriter.setPageTreeId(pageTreeId)

        # create a list of all the page object ids while dumping the pages

        for p in self.contents:
            pageIds.append(p.objId)
            p.toLrf(lrfWriter)

        # create a page tree object

        pageTree = LrfObject("PageTree", pageTreeId)
        pageTree.appendLrfTag(LrfTag("PageList", pageIds))

        lrfWriter.append(pageTree)
        


class Solos(LrsContainer):
    def __init__(self):
        LrsContainer.__init__(self, [Solo])     
        

    def getMethods(self):
        return ["appendSolo", "Solo"]


    def getSettings(self):
        return []


    def Solo(self, *args, **kwargs):
        p = Solo(*args, **kwargs)
        self.append(p)
        return p


    def appendSolo(self, solo):
        self.append(solo)

        
    def toLrf(self, lrfWriter):
        for s in self.contents:
            s.toLrf(lrfWriter)
            
 
    def toElement(self, se):
        solos = []
        for s in self.contents:
            solos.append(s.toElement(se))
            
        if len(solos) == 0:
            return None
        
        
        return solos
    
    
    
class Solo(Main):
    pass


class Template(object):
    """ Does nothing that I know of. """
    
    def appendReferencedObjects(self, parent):
        pass
    
    
    def getMethods(self):
        return []


    def getSettings(self):
        return []


    def toElement(self, se):
        t = Element("Template")
        t.attrib["version"] = "1.0"
        return t

    def toLrf(self, lrfWriter):
        # does nothing
        pass



class Style(LrsContainer, Delegator):
    def __init__(self):
        LrsContainer.__init__(self, [PageStyle, TextStyle, BlockStyle])
        Delegator.__init__(self, [BookStyle()])
        self.bookStyle = self.delegates[0]
        self.appendPageStyle = self.appendTextStyle = \
                self.appendBlockStyle = self.append
        

    def appendReferencedObjects(self, parent):
        LrsContainer.appendReferencedObjects(self, parent)


    def getMethods(self):
        return ["PageStyle", "TextStyle", "BlockStyle",
                "appendPageStyle", "appendTextStyle", "appendBlockStyle"] + \
                        self.delegatedMethods

    

    def getSettings(self):
        return [(self.bookStyle, x) for x in self.bookStyle.getSettings()]


    def PageStyle(self, *args, **kwargs):
        ps = PageStyle(*args, **kwargs)
        self.append(ps)
        return ps
    
   
    def TextStyle(self, *args, **kwargs):
        ts = TextStyle(*args, **kwargs)
        self.append(ts)
        return ts
    
 
    def BlockStyle(self, *args, **kwargs):
        bs = BlockStyle(*args, **kwargs)
        self.append(bs)
        return bs


    def toElement(self, se):
        style = Element("Style")
        style.append(self.bookStyle.toElement(se))
        
        for content in self.contents:
            style.append(content.toElement(se))
        
        return style


    def toLrf(self, lrfWriter):
        self.bookStyle.toLrf(lrfWriter)

        for s in self.contents:
            s.toLrf(lrfWriter)
    


class BookStyle(LrsObject, LrsContainer):
    def __init__(self):
        LrsObject.__init__(self, assignId=True)
        LrsContainer.__init__(self, [Font])
        self.styledefault = StyleDefault()
        self.booksetting = BookSetting()
        self.appendFont = self.append
        
        
    def getSettings(self):
        return ["styledefault", "booksetting"]
        
        
    def getMethods(self):
        return ["Font", "appendFont"]

    
    def Font(self, *args, **kwargs):
        f = Font(*args, **kwargs)
        self.append(f)
        return


    def toElement(self, se):
        bookStyle = self.lrsObjectElement("BookStyle", objlabel="stylelabel",
                labelDecorate=False)
        bookStyle.append(self.styledefault.toElement(se))
        bookStyle.append(self.booksetting.toElement(se))
        for font in self.contents:
            bookStyle.append(font.toElement(se))
            
        return bookStyle


    def toLrf(self, lrfWriter):
        bookAtr = LrfObject("BookAtr", self.objId)
        bookAtr.appendLrfTag(LrfTag("ChildPageTree", lrfWriter.getPageTreeId()))
        bookAtr.appendTagDict(self.styledefault.attrs)

        self.booksetting.toLrf(lrfWriter)

        lrfWriter.append(bookAtr)
        lrfWriter.setRootObject(bookAtr)
        
        for font in self.contents:
            font.toLrf(lrfWriter)
    
    
 
class StyleDefault(LrsAttributes):
    """
        Supply some defaults for all TextBlocks.
        The legal values are a subset of what is allowed on a
        TextBlock -- ruby, emphasis, and waitprop settings.
    """
    defaults = dict(rubyalign="start", rubyadjust="none", 
                rubyoverhang="none", empdotsposition="before",
                empdotsfontname="Dutch801 Rm BT Roman",
                empdotscode="0x002e", emplineposition="before",
                emplinetype = "solid", setwaitprop="noreplay")

    alsoAllow = ["refempdotsfont"]

    def __init__(self, **settings):       
        LrsAttributes.__init__(self, self.defaults,
                alsoAllow=self.alsoAllow, **settings)
        
        
    def toElement(self, se):
        return Element("SetDefault", self.attrs)
    
    

class BookSetting(LrsAttributes):
    def __init__(self, **settings):
        defaults = dict(bindingdirection="Lr", dpi="1600",
                screenheight="800", screenwidth="600", colordepth="24")
        LrsAttributes.__init__(self, defaults, **settings)

    
    def toLrf(self, lrfWriter):
        a = self.attrs
        lrfWriter.dpi = int(a["dpi"])
        lrfWriter.bindingdirection = \
                BINDING_DIRECTION_ENCODING[a["bindingdirection"]]
        lrfWriter.height = int(a["screenheight"])
        lrfWriter.width = int(a["screenwidth"])
        lrfWriter.colorDepth = int(a["colordepth"])

    def toElement(self, se):
        return Element("BookSetting", self.attrs)
 
    

class LrsStyle(LrsObject, LrsAttributes, LrsContainer):
    """ A mixin class for styles. """
    def __init__(self, elementName, defaults=None, alsoAllow=None, **overrides):
        if defaults is None:
            defaults = {}

        LrsObject.__init__(self)
        LrsAttributes.__init__(self, defaults, alsoAllow=alsoAllow, **overrides)
        LrsContainer.__init__(self, [])
        self.elementName = elementName  
        self.objectsAppended = False
        #self.label = "%s.%d" % (elementName, self.objId)
        #self.label = str(self.objId)
        #self.parent = None
        

    @classmethod
    def resetDefaults(selfClass):
        selfClass.defaults = selfClass.baseDefaults.copy()


    @classmethod
    def setDefaults(selfClass, settings):
        for name, value in settings.items():
            if name not in selfClass.validSettings:
                raise LrsError, "default setting %s not recognized"
            selfClass.defaults[name] = value


    def getLabel(self):
        return str(self.objId)
 
    
    def toElement(self, se):
        element = Element(self.elementName, stylelabel=self.getLabel(),
                objid=str(self.objId))
        element.attrib.update(self.attrs)
        return element


    def toLrf(self, lrfWriter):
        obj = LrfObject(self.elementName, self.objId)
        obj.appendTagDict(self.attrs, self.__class__.__name__)
        lrfWriter.append(obj)
        
        
class TextStyle(LrsStyle):
    """ 
        The text style of a TextBlock.  Default is 10 pt. Times Roman.

        Setting         Value                   Default
        --------        -----                   -------
        align           "head","center","foot"  "head" (left aligned)
        baselineskip    points * 10             120 (12 pt. distance between
                                                  bottoms of lines)
        fontsize        points * 10             100 (10 pt.)
        fontweight      1 to 1000               400 (normal, 800 is bold)
        fontwidth       points * 10 or -10      -10 (use values from font)
        linespace       points * 10             10 (min space btw. lines?)
        wordspace       points * 10             25 (min space btw. each word)

    """
    baseDefaults = dict(
            columnsep="0", charspace="0",
            textlinewidth="0", align="head", linecolor="0x00000000",
            column="1", fontsize="100", fontwidth="-10", fontescapement="0",
            fontorientation="0", fontweight="400",
            fontfacename="Dutch801 Rm BT Roman",
            textcolor="0x00000000", wordspace="25", letterspace="0",
            baselineskip="120", linespace="10", parindent="0", parskip="0",
            textbgcolor="0xFF000000")

    alsoAllow = ["empdotscode", "empdotsfontname", "refempdotsfont",
                 "rubyadjust", "rubyalign", "rubyoverhang",
                 "empdotsposition", "emplineposition", "emplinetype"]

    validSettings = baseDefaults.keys() + alsoAllow

    defaults = baseDefaults.copy()

    def __init__(self, **overrides):
        LrsStyle.__init__(self, "TextStyle", self.defaults,
                alsoAllow=self.alsoAllow, **overrides)

    def copy(self):
        tb = TextStyle()
        tb.attrs = self.attrs.copy()
        return tb



class BlockStyle(LrsStyle):
    """
        The block style of a TextBlock.  Default is an expandable 560 pixel
        wide area with no space for headers or footers.

        Setting      Value                  Default
        --------     -----                  -------
        blockwidth   pixels                 560
        sidemargin   pixels                 0
    """
    
    baseDefaults = dict(
            bgimagemode="fix", framemode="square", blockwidth="560",
            blockheight="100", blockrule="horz-adjustable", layout="LrTb",
            framewidth="0", framecolor="0x00000000", topskip="0",
            sidemargin="0", footskip="0", bgcolor="0xFF000000")

    validSettings = baseDefaults.keys()
    defaults = baseDefaults.copy()

    def __init__(self, **overrides):
        LrsStyle.__init__(self, "BlockStyle", self.defaults, **overrides)

  
        
class PageStyle(LrsStyle):
    """
        Setting         Value                   Default
        --------        -----                   -------
        evensidemargin  pixels                  20
        oddsidemargin   pixels                  20
        topmargin       pixels                  20
    """
    baseDefaults = dict(
            topmargin="20", headheight="0", headsep="0",
            oddsidemargin="20", textheight="800", textwidth="600",
            footspace="0", evensidemargin="20", footheight="0",
            layout="LrTb", bgimagemode="fix", pageposition="any",
            setwaitprop="noreplay", setemptyview="show")
   
    alsoAllow = ["header", "evenheader", "oddheader",
                 "footer", "evenfooter", "oddfooter"]

    validSettings = baseDefaults.keys() + alsoAllow
    defaults = baseDefaults.copy()

    @classmethod
    def translateHeaderAndFooter(selfClass, parent, settings):
        selfClass._fixup(parent, "header", settings)
        selfClass._fixup(parent, "footer", settings)


    @classmethod
    def _fixup(selfClass, parent, basename, settings):
        evenbase = "even" + basename
        oddbase = "odd" + basename
        if basename in settings:
            baseObj = settings[basename]
            del settings[basename]
            settings[evenbase] = settings[oddbase] = baseObj

        if evenbase in settings:
            evenObj = settings[evenbase]
            del settings[evenbase]
            if evenObj.parent is None:
                parent.append(evenObj)
            settings[evenbase + "id"] = str(evenObj.objId)

        if oddbase in settings:
            oddObj = settings[oddbase]
            del settings[oddbase]
            if oddObj.parent is None:
                parent.append(oddObj)
            settings[oddbase + "id"] = str(oddObj.objId)


    def appendReferencedObjects(self, parent):
        if self.objectsAppended:
            return
        PageStyle.translateHeaderAndFooter(parent, self.attrs)
        self.objectsAppended = True



    def __init__(self, **settings): 
        #self.fixHeaderSettings(settings)
        LrsStyle.__init__(self, "PageStyle", self.defaults,
                alsoAllow=self.alsoAllow, **settings)

    
class Page(LrsObject, LrsContainer):
    """
        Pages are added to Books.  Pages can be supplied a PageStyle.
        If they are not, Page.defaultPageStyle will be used.
    """
    defaultPageStyle = PageStyle()

    def __init__(self, *args, **settings):
        LrsObject.__init__(self)
        LrsContainer.__init__(self, [TextBlock, BlockSpace, RuledLine,
            ImageBlock])

        if len(args) > 0:
            pageStyle = args[0]
        else:
            pageStyle = Page.defaultPageStyle

        self.pageStyle = pageStyle

        for settingName in settings.keys():
            if settingName not in PageStyle.defaults and \
                    settingName not in PageStyle.alsoAllow:
                raise LrsError, "setting %s not allowed on Page" % settingName

        # TODO: should these be copied?
        self.settings = settings


    def appendReferencedObjects(self, parent):
        PageStyle.translateHeaderAndFooter(parent, self.settings)

        self.pageStyle.appendReferencedObjects(parent)

        if self.pageStyle.parent is None:
            parent.append(self.pageStyle)

        LrsContainer.appendReferencedObjects(self, parent)
            

    def RuledLine(self, *args, **kwargs):
        rl = RuledLine(*args, **kwargs)
        self.append(rl)
        return rl


    def BlockSpace(self, *args, **kwargs):
        bs = BlockSpace(*args, **kwargs)
        self.append(bs)
        return bs


    def TextBlock(self, *args, **kwargs):
        """ Create and append a new text block (shortcut). """
        tb = TextBlock(*args, **kwargs)
        self.append(tb)
        return tb


    def ImageBlock(self, *args, **kwargs):
        """ Create and append and new Image block (shorthand). """
        ib = ImageBlock(*args, **kwargs)
        self.append(ib)
        return ib
    

    def addLrfObject(self, objId):
        self.stream.appendLrfTag(LrfTag("Link", objId))


    def appendLrfTag(self, lrfTag):
        self.stream.appendLrfTag(lrfTag)


    def toLrf(self, lrfWriter):
        # tags:
        # ObjectList
        # Link to pagestyle
        # Parent page tree id
        # stream of tags
        
        p = LrfObject("Page", self.objId)
        lrfWriter.append(p)
        
        pageContent = set()
        self.stream = LrfTagStream(0) 
        for content in self.contents:
            content.toLrfContainer(lrfWriter, self)
            if hasattr(content, "getReferencedObjIds"):
                pageContent.update(content.getReferencedObjIds())


        #print "page contents:", pageContent
        p.appendLrfTag(LrfTag("ObjectList", pageContent))
        p.appendLrfTag(LrfTag("Link", self.pageStyle.objId))
        p.appendLrfTag(LrfTag("ParentPageTree", lrfWriter.getPageTreeId()))
        p.appendTagDict(self.settings)
        p.appendLrfTags(self.stream.getStreamTags(lrfWriter.getSourceEncoding()))


    def toElement(self, sourceEncoding):
        page = self.lrsObjectElement("Page")       
        page.set("pagestyle", self.pageStyle.getLabel())       
        page.attrib.update(self.settings)
        
        for content in self.contents:
            page.append(content.toElement(sourceEncoding))
            
        return page





class TextBlock(LrsObject, LrsContainer):
    """
        TextBlocks are added to Pages.  They hold Paragraphs or CRs.
        TextBlocks can be supplied a TextStyle and a BlockStyle as the first
        two arguments to the constructor, but these can be left off
        and defaults will be used (since the spec says you have to have
        them).
        
        If a TextBlock is used in a header, it should be appended to
        the Book, not to a specific Page.
    """
    defaultTextStyle = TextStyle()
    defaultBlockStyle = BlockStyle()

    def __init__(self, *args, **settings):
        LrsObject.__init__(self)
        LrsContainer.__init__(self, [Paragraph, CR])

        textStyle = TextBlock.defaultTextStyle
        blockStyle = TextBlock.defaultBlockStyle
        if len(args) > 0:
            textStyle = args[0]
        if len(args) > 1:
            blockStyle = args[1]
        if len(args) > 2:
            raise LrsError, \
                    "too many style arguments to TextBlock"

        self.textSettings = {}
        self.blockSettings = {}
        for name, value in settings.items():
            if name in TextStyle.validSettings:
                self.textSettings[name] = value
            elif name in BlockStyle.validSettings:
                self.blockSettings[name] = value
            else:
                raise LrsError, "%s not a valid setting for TextBlock" % name

        self.textStyle = textStyle
        self.blockStyle = blockStyle

        # create a textStyle with our current text settings (for Span to find)
        self.currentTextStyle = textStyle.copy()
        self.currentTextStyle.attrs.update(self.textSettings)


    def appendReferencedObjects(self, parent):
        if self.textStyle.parent is None:
            parent.append(self.textStyle)

        if self.blockStyle.parent is None:
            parent.append(self.blockStyle)

        LrsContainer.appendReferencedObjects(self, parent)


    def Paragraph(self, *args, **kwargs):
        """
            Create and append a Paragraph to this TextBlock.  A CR is
            automatically inserted after the Paragraph.  To avoid this 
            behavior, create the Paragraph and append it to the TextBlock
            in a separate call.
        """
        p = Paragraph(*args, **kwargs)
        self.append(p)
        self.append(CR())
        return p


    def toElement(self, sourceEncoding):     
        tb = self.lrsObjectElement("TextBlock", labelName="Block")
        tb.attrib.update(self.textSettings)
        tb.attrib.update(self.blockSettings)
        tb.set("textstyle", self.textStyle.getLabel())
        tb.set("blockstyle", self.blockStyle.getLabel())
        if hasattr(self, "tocLabel"):
            tb.set("toclabel", self.tocLabel)

        for content in self.contents:
            tb.append(content.toElement(sourceEncoding))
            
        return tb

    
    def getReferencedObjIds(self):
        ids = [self.objId, self.extraId, self.blockStyle.objId,
                self.textStyle.objId]
        for content in self.contents:
            if hasattr(content, "getReferencedObjIds"):
                ids.extend(content.getReferencedObjIds())

        return ids


    def toLrf(self, lrfWriter):
        self.toLrfContainer(lrfWriter, lrfWriter)


    def toLrfContainer(self, lrfWriter, container):
        # id really belongs to the outer block

        extraId = LrsObject.getNextObjId()

        b = LrfObject("Block", self.objId)
        b.appendLrfTag(LrfTag("Link", self.blockStyle.objId))
        b.appendLrfTags(
                LrfTagStream(0, [LrfTag("Link", extraId)]). \
                        getStreamTags(lrfWriter.getSourceEncoding()))
        b.appendTagDict(self.blockSettings)
        container.addLrfObject(b.objId)
        lrfWriter.append(b)

        tb = LrfObject("TextBlock", extraId)        
        tb.appendLrfTag(LrfTag("Link", self.textStyle.objId))
        tb.appendTagDict(self.textSettings)
        
        stream = LrfTagStream(STREAM_COMPRESSED)
        for content in self.contents:
            content.toLrfContainer(lrfWriter, stream)

        if lrfWriter.saveStreamTags: # true only if testing
            tb.saveStreamTags = stream.tags

        tb.appendLrfTags(
                stream.getStreamTags(lrfWriter.getSourceEncoding(),
                    optimizeTags=lrfWriter.optimizeTags,
                    optimizeCompression=lrfWriter.optimizeCompression))
        lrfWriter.append(tb)

        self.extraId = extraId


class Paragraph(LrsContainer):
    """
        Note: <P> alone does not make a paragraph.  Only a CR inserted
        into a text block right after a <P> makes a real paragraph.
        Two Paragraphs appended in a row act like a single Paragraph.

        Also note that there are few autoappenders for Paragraph (and
        the things that can go in it.)  It's less confusing (to me) to use
        explicit .append methods to build up the text stream.
    """
    def __init__(self, text=None):
        LrsContainer.__init__(self, [Text, CR, LrsDrawChar, CharButton,
            LrsSimpleChar1, basestring])
        if text is not None:
            self.append(text)


    def CR(self):
        # Okay, here's a single autoappender for this common operation
        cr = CR()
        self.append(cr)
        return cr
    
    
    def getReferencedObjIds(self):
        ids = []
        for content in self.contents:
            if hasattr(content, "getReferencedObjIds"):
                ids.extend(content.getReferencedObjIds())

        return ids


    def toLrfContainer(self, lrfWriter, parent):
        parent.appendLrfTag(LrfTag("pstart", 0))
        for content in self.contents:
            content.toLrfContainer(lrfWriter, parent)
        parent.appendLrfTag(LrfTag("pend"))


    def toElement(self, sourceEncoding):
        p = Element("P")
        appendTextElements(p, self.contents, sourceEncoding)
        return p



class LrsTextTag(LrsContainer):
    def __init__(self, text, validContents):
        LrsContainer.__init__(self, [Text, basestring] + validContents)
        if text is not None:
            self.append(text)


    def toLrfContainer(self, lrfWriter, parent):
        if hasattr(self, "tagName"):
            tagName = self.tagName
        else:
            tagName = self.__class__.__name__

        parent.appendLrfTag(LrfTag(tagName))

        for content in self.contents:
            content.toLrfContainer(lrfWriter, parent)

        parent.appendLrfTag(LrfTag(tagName + "End"))


    def toElement(self, se):
        if hasattr(self, "tagName"):
            tagName = self.tagName
        else:
            tagName = self.__class__.__name__

        p = Element(tagName)
        appendTextElements(p, self.contents, se)
        return p


class LrsSimpleChar1(object):
    pass


class LrsDrawChar(LrsSimpleChar1):
    pass


class Text(LrsContainer):
    """ A object that represents raw text.  Does not have a toElement. """
    def __init__(self, text):
        LrsContainer.__init__(self, [])
        self.text = text

    def toLrfContainer(self, lrfWriter, parent):
        if self.text:
            parent.appendLrfTag(LrfTag("rawtext", self.text))



class CR(LrsDrawChar, LrsContainer):
    """
        A line break (when appended to a Paragraph) or a paragraph break 
        (when appended to a TextBlock).
    """
    def __init__(self):
        LrsContainer.__init__(self, [])


    def toElement(self, se):
        return Element("CR")


    def toLrfContainer(self, lrfWriter, parent):
        parent.appendLrfTag(LrfTag("CR"))



class Italic(LrsDrawChar, LrsTextTag):
    def __init__(self, text=None):
        LrsTextTag.__init__(self, text, [LrsDrawChar])




class Sub(LrsDrawChar, LrsTextTag):
    def __init__(self, text=None):
        LrsTextTag.__init__(self, text, [])



class Sup(LrsDrawChar, LrsTextTag):
    def __init__(self, text=None):
        LrsTextTag.__init__(self, text, [])



class NoBR(LrsDrawChar, LrsTextTag):
    def __init__(self, text=None):
        LrsTextTag.__init__(self, text, [LrsSimpleChar1])


# TODO: Plot, Image

class Space(LrsSimpleChar1, LrsContainer):
    def __init__(self, xsize=0, x=0):
        LrsContainer.__init__(self, [])
        if xsize == 0 and x != 0: xsize = x
        self.xsize = xsize


    def toElement(self, se):
        if self.xsize == 0:
            return

        return Element("Space", xsize=str(self.xsize))


    def toLrfContainer(self, lrfWriter, container):
        if self.xsize != 0:
            container.appendLrfTag(LrfTag("Space", self.xsize))


class Box(LrsSimpleChar1, LrsContainer):
    """
        Draw a box around text.  Unfortunately, does not seem to do
        anything on the PRS-500.
    """
    def __init__(self, linetype="solid"):
        LrsContainer.__init__(self, [Text, basestring])
        if linetype not in LINE_TYPE_ENCODING:
            raise LrsError, linetype + " is not a valid line type"
        self.linetype = linetype


    def toElement(self, se):
        e = Element("Box", linetype=self.linetype)
        appendTextElements(e, self.contents, se)
        return e


    def toLrfContainer(self, lrfWriter, container):
        container.appendLrfTag(LrfTag("Box", self.linetype))
        for content in self.contents:
            content.toLrfContainer(lrfWriter, container)
        container.appendLrfTag(LrfTag("BoxEnd"))



        
class Span(LrsDrawChar, LrsContainer):
    def __init__(self, text=None, **attrs):
        LrsContainer.__init__(self, [LrsDrawChar, Text, basestring])
        if text is not None:
            self.append(text)

        for attrname in attrs.keys():
            if attrname not in TextStyle.defaults and \
                    attrname not in TextStyle.alsoAllow:
                raise LrsError, "setting %s not allowed on Span" % attrname
        self.attrs = attrs


    def findCurrentTextStyle(self):
        parent = self.parent
        while 1:
            if parent is None or hasattr(parent, "currentTextStyle"):
                break
            parent = parent.parent

        if parent is None:
            raise LrsError, "no enclosing current TextStyle found"

        return parent.currentTextStyle


    def toLrfContainer(self, lrfWriter, container):

        # set the attributes we want changed
        for (name, value) in self.attrs.items():
            container.appendLrfTag(LrfTag(name, value))

        # set a currentTextStyle so nested span can put things back
        oldTextStyle = self.findCurrentTextStyle()
        self.currentTextStyle = oldTextStyle.copy()
        self.currentTextStyle.attrs.update(self.attrs)

        for content in self.contents:
            content.toLrfContainer(lrfWriter, container)

        # put the attributes back the way we found them
        for name in self.attrs.keys():
            container.appendLrfTag(LrfTag(name, oldTextStyle.attrs[name]))


    def toElement(self, se):
        element = Element("Span")
        for (key, value) in self.attrs.items():
            element.set(key, str(value))

        appendTextElements(element, self.contents, se)
        return element


class Bold(Span):
    """ 
        There is no known "bold" lrf tag. Use Span with a fontweight in LRF,
        but use the word Bold in the LRS.
    """
    def __init__(self, text=None):
        Span.__init__(self, text, fontweight=800)

    def toElement(self, se):
        e = Element("Bold")
        appendTextElements(e, self.contents, se)
        return e


class BlockSpace(LrsContainer):
    """ Can be appended to a page to move the text point. """
    def __init__(self, xspace=0, yspace=0, x=0, y=0):
        LrsContainer.__init__(self, [])
        if xspace == 0 and x != 0: xspace = x
        if yspace == 0 and y != 0: yspace = y
        self.xspace = xspace
        self.yspace = yspace


    def toLrfContainer(self, lrfWriter, container):
        if self.xspace != 0:
            container.appendLrfTag(LrfTag("xspace", self.xspace))
        if self.yspace != 0:
            container.appendLrfTag(LrfTag("yspace", self.yspace))


    def toElement(self, se):
        element = Element("BlockSpace")

        if self.xspace != 0:
            element.attrib["xspace"] = str(self.xspace)
        if self.yspace != 0:
            element.attrib["yspace"] = str(self.yspace)

        return element



class CharButton(LrsDrawChar, LrsContainer):
    """
        Define the text and target of a CharButton.  Must be passed a 
        JumpButton that is the destination of the CharButton.

        Only text or SimpleChars can be appended to the CharButton.
    """
    def __init__(self, jumpButton, text=None):
        LrsContainer.__init__(self, [basestring, Text, LrsSimpleChar1])
        if not isinstance(jumpButton, JumpButton):
            raise LrsError, "first argument to CharButton must be a JumpButton"

        self.jumpButton = jumpButton
        if text is not None:
            self.append(text)


    def appendReferencedObjects(self, parent):
        if self.jumpButton.parent is None:
            parent.append(self.jumpButton)


    def getReferencedObjIds(self):
        return [self.jumpButton.objId]


    def toLrfContainer(self, lrfWriter, container):
        container.appendLrfTag(LrfTag("CharButton", self.jumpButton.objId))
        
        for content in self.contents:
            content.toLrfContainer(lrfWriter, container)
            
        container.appendLrfTag(LrfTag("CharButtonEnd"))


    def toElement(self, se):
        cb = Element("CharButton", refobj=str(self.jumpButton.objId))
        appendTextElements(cb, self.contents, se)
        return cb



class Objects(LrsContainer):
    def __init__(self):
        LrsContainer.__init__(self, [JumpButton, TextBlock, HeaderOrFooter,
            ImageStream])
        self.appendJumpButton = self.appendTextBlock = self.appendHeader = \
                self.appendFooter = self.appendImageStream = self.append


    def getMethods(self):
        return ["JumpButton", "appendJumpButton", "TextBlock", 
                "appendTextBlock", "Header", "appendHeader",
                "Footer", "appendFooter",
                "ImageStream", "appendImageStream"]


    def getSettings(self):
        return []



    def JumpButton(self, textBlock):
        b = JumpButton(textBlock)
        self.append(b)
        return b


    def TextBlock(self, *args, **kwargs):
        tb = TextBlock(*args, **kwargs)
        self.append(tb)
        return tb

 
    def Header(self, *args, **kwargs):
        h = Header(*args, **kwargs)
        self.append(h)
        return h


    def Footer(self, *args, **kwargs):
        h = Footer(*args, **kwargs)
        self.append(h)
        return h


    def ImageStream(self, *args, **kwargs):
        i = ImageStream(*args, **kwargs)
        self.append(i)
        return i


    def toElement(self, se):
        o = Element("Objects")

        for content in self.contents:
            o.append(content.toElement(se))

        return o
        

    def toLrf(self, lrfWriter):
        for content in self.contents:
            content.toLrf(lrfWriter)
    

class JumpButton(LrsObject, LrsContainer):
    """
        The target of a CharButton.  Needs a parented TextBlock to jump to.
        Actually creates several elements in the XML.  JumpButtons must
        be eventually appended to a Book (actually, an Object.)
    """
    def __init__(self, textBlock):
        LrsObject.__init__(self)
        LrsContainer.__init__(self, [])
        self.textBlock = textBlock


    def toLrf(self, lrfWriter):
        button = LrfObject("Button", self.objId)
        button.appendLrfTag(LrfTag("buttonflags", 0x10)) # pushbutton
        button.appendLrfTag(LrfTag("PushButtonStart"))
        button.appendLrfTag(LrfTag("buttonactions"))
        button.appendLrfTag(LrfTag("jumpto",
            (self.textBlock.parent.objId, self.textBlock.objId)))
        button.append(LrfTag("endbuttonactions"))
        button.appendLrfTag(LrfTag("PushButtonEnd"))
        lrfWriter.append(button)


    def toElement(self, se):
        b = self.lrsObjectElement("Button")
        pb = SubElement(b, "PushButton")
        jt = SubElement(pb, "JumpTo",
            refpage=str(self.textBlock.parent.objId),
            refobj=str(self.textBlock.objId))
        return b



class RuledLine(LrsContainer, LrsAttributes):
    """ A line.  Default is 500 pixels long, 2 pixels wide. """

    defaults = dict(
            linelength="500", linetype="solid", linewidth="2",
            linecolor="0x00000000")

    def __init__(self, **settings): 
        LrsContainer.__init__(self, [])
        LrsAttributes.__init__(self, self.defaults, **settings)


    def toLrfContainer(self, lrfWriter, container):
        a = self.attrs
        container.appendLrfTag(LrfTag("RuledLine",
            (a["linelength"], a["linetype"], a["linewidth"], a["linecolor"])))


    def toElement(self, se):
        return Element("RuledLine", self.attrs)



class HeaderOrFooter(LrsObject, LrsContainer, LrsAttributes):
    """
        Creates empty header or footer objects.  Append PutObj objects to
        the header or footer to create the text.

        Note: it seems that adding multiple PutObjs to a header or footer
              only shows the last one.
    """
    defaults = dict(framemode="square", layout="LrTb", framewidth="0",
                framecolor="0x00000000", bgcolor="0xFF000000")

    def __init__(self, **settings):        
        LrsObject.__init__(self)
        LrsContainer.__init__(self, [PutObj])
        LrsAttributes.__init__(self, self.defaults, **settings)


    def PutObj(self, *args, **kwargs):
        p = PutObj(*args, **kwargs)
        self.append(p)
        return p


    def toLrf(self, lrfWriter):
        hd = LrfObject(self.__class__.__name__, self.objId)
        hd.appendTagDict(self.attrs)

        stream = LrfTagStream(0)
        for content in self.contents:
            content.toLrfContainer(lrfWriter, stream)

        hd.appendLrfTags(stream.getStreamTags(lrfWriter.getSourceEncoding()))
        lrfWriter.append(hd)


    def toElement(self, se):
        name = self.__class__.__name__
        labelName = name.lower() + "label"
        hd = self.lrsObjectElement(name, objlabel=labelName)
        hd.attrib.update(self.attrs)
        
        for content in self.contents:
            hd.append(content.toElement(se))

        return hd


class Header(HeaderOrFooter):
    pass



class Footer(HeaderOrFooter):
    pass


class PutObj(LrsContainer):
    """ PutObj holds other objects that are drawn on a Canvas or Header. """

    def __init__(self, content, x1=0, y1=0, x=0, y=0):
        LrsContainer.__init__(self, [])
        self.content = content
        if x1 == 0 and x != 0: x1 = x
        if y1 == 0 and y != 0: y1 = y
        self.x1 = x1
        self.y1 = y1


    def appendReferencedObjects(self, parent):
        if self.content.parent is None:
            parent.append(self.content)


    def toLrfContainer(self, lrfWriter, container):
        container.appendLrfTag(LrfTag("PutObj", (self.x1, self.y1,
            self.content.objId)))


    def toElement(self, se):
        return Element("PutObj", x1=str(self.x1), y1=str(self.y1),
                    refobj=str(self.content.objId))



class ImageStream(LrsObject, LrsContainer):
    """ 
        Embed an image file into an Lrf. 
    """
    
    VALID_ENCODINGS = [ "JPEG", "GIF", "BMP", "PNG" ]
    
    def __init__(self, filename, encoding=None, comment=None):
        LrsObject.__init__(self)
        LrsContainer.__init__(self, [])
        _checkExists(filename)
        self.filename = filename
        self.comment = comment
        # TODO: move encoding from extension to lrf module
        if encoding is None:
            extension = os.path.splitext(filename)[1]
            if not extension:
                raise LrsError, \
                        "file must have extension if encoding is not specified"
            extension = extension[1:].upper()

            if extension == "JPG":
                extension = "JPEG"
                
            encoding = extension
        else:
            encoding = encoding.upper()
            
        if encoding not in self.VALID_ENCODINGS:
            raise LrsError, \
                "encoding or file extension not JPEG, GIF, BMP, or PNG"
        
        self.encoding = encoding
        

    def toLrf(self, lrfWriter):
        imageFile = file(self.filename, "rb")
        imageData = imageFile.read()
        imageFile.close()

        isObj = LrfObject("ImageStream", self.objId)
        if self.comment is not None:
            isObj.appendLrfTag(LrfTag("comment", self.comment))

        streamFlags = IMAGE_TYPE_ENCODING[self.encoding]
        stream = LrfStreamBase(streamFlags, imageData)
        isObj.appendLrfTags(stream.getStreamTags())
        lrfWriter.append(isObj)


    def toElement(self, se):
        element = self.lrsObjectElement("ImageStream",
                                objlabel="imagestreamlabel",
                                encoding=self.encoding, file=self.filename)
        element.text = self.comment
        return element



class ImageBlock(LrsObject, LrsContainer, LrsAttributes):
    """ Create an image on a page. """
    # TODO: allow other block attributes

    defaults = dict(blockwidth="600", blockheight="800") 

    def __init__(self, refstream, x0="0", y0="0", x1="600", y1="800", 
                       xsize="600", ysize="800",  blockStyle=None,
                       alttext=None, **settings):       
        LrsObject.__init__(self)
        LrsContainer.__init__(self, [])
        LrsAttributes.__init__(self, self.defaults, **settings)
        self.x0, self.y0, self.x1, self.y1 = int(x0), int(y0), int(x1), int(y1)
        self.xsize, self.ysize = int(xsize), int(ysize)
        self.refstream = refstream
        self.blockStyle = blockStyle
        self.alttext = alttext
 

    def appendReferencedObjects(self, parent):
        if self.refstream.parent is None:
            parent.append(self.refstream)

        if self.blockStyle is not None and self.blockStyle.parent is None:
            parent.append(self.blockStyle)


    def getReferencedObjIds(self):
        objects =  [self.objId, self.extraId, self.refstream.objId]
        if self.blockStyle is not None:
            objects.append(self.blockStyle.objId)

        return objects


    def toLrf(self, lrfWriter):
        self.toLrfContainer(lrfWriter, lrfWriter)


    def toLrfContainer(self, lrfWriter, container):
        # id really belongs to the outer block

        extraId = LrsObject.getNextObjId()

        b = LrfObject("Block", self.objId)
        if self.blockStyle is not None:
            b.appendLrfTag(LrfTag("Link", self.blockStyle.objId))
        b.appendTagDict(self.attrs)

        b.appendLrfTags(
            LrfTagStream(0,
                [LrfTag("Link", extraId)]).getStreamTags(lrfWriter.getSourceEncoding()))
        container.addLrfObject(b.objId)
        lrfWriter.append(b)

        ib = LrfObject("Image", extraId)        
        
        ib.appendLrfTag(LrfTag("ImageRect",
            (self.x0, self.y0, self.x1, self.y1)))
        ib.appendLrfTag(LrfTag("ImageSize", (self.xsize, self.ysize)))
        ib.appendLrfTag(LrfTag("RefObjId", self.refstream.objId))
        if self.alttext:
            ib.appendLrfTag("Comment", self.alttext)

        
        lrfWriter.append(ib)
        self.extraId = extraId


    def toElement(self, se):
        element = self.lrsObjectElement("ImageBlock", **self.attrs)
        element.set("refstream", str(self.refstream.objId))
        for name in ["x0", "y0", "x1", "y1", "xsize", "ysize"]:
            element.set(name, str(getattr(self, name)))
        element.text = self.alttext
        return element



class Font(LrsContainer):
    """ Allows a TrueType file to embedded in an Lrf. """
    def __init__(self, filename, facename):
        LrsContainer.__init__(self, [])
        _checkExists(filename)
        self.filename = filename
        self.facename = facename


    def toLrf(self, lrfWriter):
        font = LrfObject("Font", LrsObject.getNextObjId())
        lrfWriter.registerFontId(font.objId)
        font.appendLrfTag(LrfTag("FontFilename",
            lrfWriter.toUnicode(self.filename)))
        font.appendLrfTag(LrfTag("FontFacename",
            lrfWriter.toUnicode(self.facename)))

        stream = LrfFileStream(STREAM_FORCE_COMPRESSED, self.filename)
        font.appendLrfTags(stream.getStreamTags())

        lrfWriter.append(font)


    def toElement(self, se):
        element = Element("RegistFont", encoding="TTF", fontname=self.facename,
                file=self.filename, fontfilename=self.filename)
        return element



