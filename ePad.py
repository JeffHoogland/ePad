#!/usr/bin/python
# encoding: utf-8

# ePad - a simple text editor written in Elementary and Python
#
# This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function  # May as well bite the bullet

__author__ = "Jeff Hoogland"
__contributors__ = ["Jeff Hoogland", "Robert Wiley", "Kai Huuhko", "Scimmia22"]
__copyright__ = "Copyright (C) 2014 Bodhi Linux"
__version__ = "0.9.0"
__description__ = 'A simple text editor for the Enlightenment Desktop.'
__github__ = 'https://github.com/JeffHoogland/ePad'
__source__ = 'Source code and bug reports: {0}'.format(__github__)
PY_EFL = "https://git.enlightenment.org/bindings/python/python-efl.git/"

AUTHORS = """
<br>
<align=center>
<hilight>Jeff Hoogland (Jef91)</hilight><br>
<link><a href=http://www.jeffhoogland.com>Contact</a></link><br><br>

<hilight>Robert Wiley (ylee)</hilight><br><br>

<hilight>Kai Huuhko (kukko)</hilight><br><br>
</align>
"""

LICENSE = """<br>
<align=center>
<hilight>
GNU GENERAL PUBLIC LICENSE<br>
Version 3, 29 June 2007<br><br>
</hilight>

This program is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version.<br><br>

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU General Public License for more details.<br><br>

You should have received a copy of the GNU General Public License 
along with this program. If not, see<br>
<link><a href=http://www.gnu.org/licenses>http://www.gnu.org/licenses/</a></link>
</align>
<br>
"""

INFO = """
<align=center>
<hilight>ePad</hilight> is a simple text editor written in Elementary and Python.<br> 
<br>
<br>
</align>
"""


import argparse
import errno
import sys
import os
import time
import urllib
import re

from efl import ecore
from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl import elementary
from efl.elementary.window import StandardWindow, Window
from efl.elementary.window import ELM_WIN_DIALOG_BASIC
from efl.elementary.background import Background
from efl.elementary.box import Box
from efl.elementary.button import Button
from efl.elementary.label import Label, ELM_WRAP_WORD
from efl.elementary.icon import Icon
from efl.elementary.need import need_ethumb
from efl.elementary.notify import Notify, ELM_NOTIFY_ALIGN_FILL
from efl.elementary.separator import Separator
from efl.elementary.scroller import Scroller
from efl.elementary.image import Image
from efl.elementary.frame import Frame
from efl.elementary.list import List
from efl.elementary.frame import Frame
from efl.elementary.entry import Entry, ELM_TEXT_FORMAT_PLAIN_UTF8, \
        markup_to_utf8, utf8_to_markup, ELM_WRAP_NONE, ELM_WRAP_MIXED
from efl.elementary.popup import Popup
from efl.elementary.toolbar import Toolbar, ELM_OBJECT_SELECT_MODE_DEFAULT
from efl.elementary.flip import Flip, ELM_FLIP_ROTATE_XZ_CENTER_AXIS, \
        ELM_FLIP_ROTATE_YZ_CENTER_AXIS, ELM_FLIP_INTERACTION_ROTATE
from efl.elementary.table import Table
from efl.elementary.transit import Transit, \
        ELM_TRANSIT_EFFECT_WIPE_TYPE_HIDE, ELM_TRANSIT_EFFECT_WIPE_DIR_RIGHT
from efl.elementary.check import Check
from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl.elementary.naviframe import Naviframe
from efl.ecore import Exe

# Imported here to stop class resolver complaining when an input event
# applies to an internal layout object
from efl.elementary.layout import Layout

from elmextensions import AboutWindow
from elmextensions import FileSelector

EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.5
EXPAND_NONE = 0.0, 0.0
ALIGN_CENTER = 0.5, 0.5
ALIGN_RIGHT = 1.0, 0.5
ALIGN_LEFT = 0.0, 0.5
PADDING = 15, 0
# User options
WORD_WRAP = ELM_WRAP_NONE
SHOW_POS = True
NOTIFY_ROOT = True
SHOW_HIDDEN = False
NEW_INSTANCE = True

def printErr(*objs):
    print(*objs, file=sys.stderr)

def errorPopup(window, errorMsg):
    errorPopup = Popup(window, size_hint_weight=EXPAND_BOTH)
    errorPopup.callback_block_clicked_add(lambda obj: errorPopup.delete())

    # Add a table to hold dialog image and text to Popup
    tb = Table(errorPopup, size_hint_weight=EXPAND_BOTH)
    errorPopup.part_content_set("default", tb)
    tb.show()

    # Add dialog-error Image to table
    need_ethumb()
    icon = Icon(errorPopup, thumb='True')
    icon.standard_set('dialog-warning')
    # Using gksudo or sudo fails to load Image here
    #   unless options specify using preserving their existing environment.
    #   may also fail to load other icons but does not raise an exception
    #   in that situation.
    # Works fine using eSudo as a gksudo alternative,
    #   other alternatives not tested
    try:
        dialogImage = Image(errorPopup,
                            size_hint_weight=EXPAND_HORIZ,
                            size_hint_align=FILL_BOTH,
                            file=icon.file_get())
        tb.pack(dialogImage, 0, 0, 1, 1)
        dialogImage.show()
    except RuntimeError:
        # An error message is displayed for this same error
        #   when aboutWin is initialized so no need to redisplay.
        pass
    # Add dialog text to table
    dialogLabel = Label(errorPopup, line_wrap=ELM_WRAP_WORD,
                        size_hint_weight=EXPAND_HORIZ,
                        size_hint_align=FILL_BOTH)
    dialogLabel.text = errorMsg
    tb.pack(dialogLabel, 1, 0, 1, 1)
    dialogLabel.show()

    # Ok Button
    ok_btt = Button(errorPopup)
    ok_btt.text = "Ok"
    ok_btt.callback_clicked_add(lambda obj: errorPopup.delete())
    ok_btt.show()

    # add button to popup
    errorPopup.part_content_set("button3", ok_btt)
    errorPopup.show()

#A hack to work around elm keypress sucking a fat one
def threeCount(ourCallback):
    if not hasattr(threeCount, 'count'):
        threeCount.count = 0
    if threeCount.count == 0:
        ourCallback()
    #print(threeCount.count)
    threeCount.count = (threeCount.count + 1) % 3

def closeMenu(obj, label):
    if not hasattr(closeMenu, 'count'):
        closeMenu.count = 0
    if not hasattr(closeMenu, 'name'):
        closeMenu.lastItem = label
    if closeMenu.lastItem != label:
        closeMenu.count = 0
    if closeMenu.count:
        obj.selected_set(False)
        obj.menu_get().close()
    closeMenu.count = (closeMenu.count + 1) % 2


def resetCloseMenuCount(obj):
        global closeMenu
        if hasattr(closeMenu, 'count'):
            closeMenu.count = 0


class Interface(object):
    def __init__(self):
        self.isSaved = True
        self.isNewFile = False
        self.confirmPopup = None
        self.lineNums = True
        
        self.mainWindow = StandardWindow("epad", "Untitled - ePad",
                                         size=(600, 400))
        self.mainWindow.callback_delete_request_add(self.closeChecks)
        self.mainWindow.elm_event_callback_add(self.eventsCb)
        #self.mainWindow.repeat_events_set(False)

        icon = Icon(self.mainWindow,
                    size_hint_weight=EXPAND_BOTH,
                    size_hint_align=FILL_BOTH)
        icon.standard_set('accessories-text-editor')
        icon.show()
        self.mainWindow.icon_object_set(icon.object_get())

        self.mainBox = Box(self.mainWindow,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.mainBox.show()

        self.newInstance = NEW_INSTANCE
        self.mainTb = ePadToolbar(self, self.mainWindow)
        self.mainTb.focus_allow = False
        self.mainTb.show()
        
        self.mainBox.pack_end(self.mainTb)
        
        # Root User Notification
        if os.geteuid() == 0:
            printErr("Caution: Root User")
            if NOTIFY_ROOT:
                notifyBox = Box(self.mainWindow, horizontal=True)
                notifyBox.show()
                notify = Notify(self.mainWindow, size_hint_weight=EXPAND_BOTH,
                                align=(ELM_NOTIFY_ALIGN_FILL, 0.0),
                                content=notifyBox)
                notifyLabel = Label(self.mainWindow)
                notifyLabel.text = "<b><i>Root User</i></b>"
                notifyBox.pack_end(notifyLabel)
                notifyLabel.show()
                self.mainBox.pack_end(notifyBox)

        self.findBox = ePadFindBox(self, self.mainWindow)
        self.findVisible = False
        
        self.scr = Scroller(self.mainBox,
                           size_hint_weight=EXPAND_HORIZ,
                           size_hint_align=FILL_BOTH)
        self.scr.content_min_limit(False, True)
        
        self.buttonBox = Box(self.scr,
                           size_hint_weight=EXPAND_HORIZ,
                           size_hint_align=ALIGN_LEFT)
        self.buttonBox.horizontal = True
        self.buttonBox.show()
        
        self.scr.content = self.buttonBox
        self.scr.show()
        
        self.mainBox.pack_end(self.scr)
        
        self.nf = Naviframe(self.mainWindow,
                               size_hint_weight=EXPAND_BOTH,
                               size_hint_align=FILL_BOTH)
        self.nf.show()
        
        self.fileEntries = []
        
        self.mainBox.pack_end(self.nf)

        # Build our file selector for saving/loading files
        self.fileBox = Box(self.mainWindow,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.fileBox.show()

        self.fileLabel = Label(self.mainWindow,
                               size_hint_weight=EXPAND_HORIZ,
                               size_hint_align=FILL_BOTH, text="")
        self.fileLabel.show()
        self.lastDir = os.getenv("HOME")
        self.fileSelector = FileSelector(self.mainWindow,
                                         defaultPath=self.lastDir,
                                         defaultPopulate=False,
                                         size_hint_weight=EXPAND_BOTH,
                                         size_hint_align=FILL_BOTH)
        self.fileSelector.callback_activated_add(self.fileSelected)
        self.fileSelector.callback_directory_open_add(self.updateLastDir)
        self.fileSelector.callback_cancel_add(self.fileSelCancelPressed)
        self.fileSelector.setMode("Open")
        self.fileSelector.show()

        self.fileBox.pack_end(self.fileLabel)
        self.fileBox.pack_end(self.fileSelector)

        # Flip object has the file selector on one side
        #   and the GUI on the other
        self.flip = Flip(self.mainWindow, size_hint_weight=EXPAND_BOTH,
                         size_hint_align=FILL_BOTH)
        self.flip.part_content_set("front", self.mainBox)
        self.flip.part_content_set("back", self.fileBox)
        self.mainWindow.resize_object_add(self.flip)
        self.flip.show()
    
    def addFile(self, filePath):
        entryBox = ePadEntry(self, self.nf, self.lineNums)
        entryBox.show()
        
        self.fileEntries.append(entryBox)
        
        self.nf.item_simple_push(entryBox)
        
        if filePath != "Untitled":
            entryBox.openFile(filePath)
            btnText = filePath.split("/")[-1]
        else:
            btnText = "Untitled"
        
        btn = Button(self.buttonBox, style="anchor")
        btn.text = btnText
        btn.data["entry"] = entryBox
        btn.callback_clicked_add(self.showFile)
        btn.show()
        
        icn = Icon(self.mainWindow)
        icn.standard_set("gtk-close")
        icn.show()
        
        cls = Button(self.buttonBox, content=icn, style="anchor")
        cls.data["entry"] = entryBox
        cls.callback_clicked_add(self.closeFile)
        cls.show()
        
        sep = Separator(self.buttonBox)
        sep.show()
        
        self.buttonBox.pack_end(btn)
        self.buttonBox.pack_end(cls)
        self.buttonBox.pack_end(sep)
        
        #Arguments go: btn, cls, sep
        entryBox.setWidgets(btn, cls, sep)
        
        self.setFile(entryBox, btn.text)
    
    def setFile(self, entryBox, winTitle):
        self.nf.item_simple_push(entryBox)
        self.mainWindow.title = "%s - ePad" % (winTitle)
        self.entryBox = entryBox
    
    def closeFile(self, btn, altBtn=False, forceClose=False):
        if altBtn:
            btn = altBtn
            
        if btn.data["entry"].isSaved or forceClose:
            self.buttonBox.unpack(btn.data["entry"].close)
            self.buttonBox.unpack(btn.data["entry"].button)
            self.buttonBox.unpack(btn.data["entry"].sep)
            
            self.fileEntries.remove(btn.data["entry"])
            
            if len(self.fileEntries):
                if self.entryBox == btn.data["entry"]:
                    self.setFile(self.fileEntries[0], self.fileEntries[0].button.text)
            else:
                self.addFile("Untitled")
            
            btn.delete()
            btn.data["entry"].button.delete()
            btn.data["entry"].close.delete()
            btn.data["entry"].sep.delete()
        else:
            btn.data["entry"].closeChecks(self.closeFile)
    
    def showFile(self, btn):
        if self.entryBox != btn.data["entry"]:
            self.setFile(btn.data["entry"], btn.text)

    def newFile(self, obj=None, ignoreSave=False):
        self.addFile("Untitled")

    def openFile(self, obj=None, ignoreSave=False):
        self.fileSelector.setMode("Open")
        self.fileLabel.text = "<b>Select a text file to open:</b>"
        if self.fileSelector.filepathEntry.text != self.lastDir:
            self.fileSelector.populateFiles(self.lastDir)
        self.flip.go(ELM_FLIP_ROTATE_YZ_CENTER_AXIS)

    def fileSelCancelPressed(self, fs):
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)
        
    def showFind(self, obj=None):
        if not self.findVisible:
            self.mainBox.pack_before(self.findBox, self.scr)
            self.findBox.findEntry.text = self.entryBox.mainEn.selection_get()
            self.findBox.findEntry.focus_set(True)
            self.findBox.findEntry.cursor_end_set()
            self.findBox.show()
            self.findVisible = True
        else:
            self.hideFind()
    
    def hideFind(self, obj=None):
        if self.findVisible:
            self.mainBox.unpack(self.findBox)
            self.findBox.hide()
            self.findVisible = False

    def saveAs(self):
        self.fileSelector.setMode("Save")
        self.fileLabel.text = "<b>Save new file to where:</b>"
        if self.fileSelector.filepathEntry.text != self.lastDir:
            self.fileSelector.populateFiles(self.lastDir)
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)

    def saveFile(self, obj=False):
        if self.entryBox.mainEn.file_get()[0] is None or self.isNewFile:
            self.saveAs()
        else:
            file_selected = self.entryBox.mainEn.file_get()[0]
            # Detect save errors as entry.file_save currently returns no errors
            #   even in the case where the file fails to save :(
            try:
                newfile = open(file_selected, 'w')
            except IOError as err:
                if err.errno == errno.EACCES:
                    errorMsg = ("Permision denied: <b>'%s'</b>."
                                "<br><br>Operation failed !!!"
                                % (file_selected))
                    errorPopup(self.mainWindow, errorMsg)
                else:
                    errorMsg = ("ERROR: %s: '%s'"
                                "<br><br>Operation failed !!!"
                                % (err.strerror, file_selected))
                    errorPopup(self.mainWindow, errorMsg)
                return
            newfile.close()
            # if entry is empty and the file does not exists then
            #   entry.file_save will destroy the file created about by the
            #   open statement above for some odd reason ...
            if not self.entryBox.mainEn.is_empty:
                self.entryBox.mainEn.file_save()
            self.mainWindow.title_set("%s - ePad"
                                      % os.path.basename(self.entryBox.mainEn.file[0]))
            self.entryBox.button.text = os.path.basename(self.entryBox.mainEn.file[0])
            self.entryBox.isSaved = True

    def fileSelected(self, fs, file_selected, onStartup=False):
        if not onStartup:
            self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)
            # Markup can end up in file names because file_selector name_entry
            #   is an elementary entry. So lets sanitize file_selected.
            file_selected = markup_to_utf8(file_selected)
        if file_selected:
            print("File Selected: {0}".format(file_selected))
            self.lastDir = os.path.dirname(file_selected)
            # This fails if file_selected does not exist yet
            
            fs.fileEntry.text = file_selected.split("/")[-1]

        IsSave = fs.mode

        if file_selected:
            if IsSave == "save":
                if os.path.isdir(file_selected):
                    current_file = os.path.basename(file_selected)
                    errorMsg = ("<b>'%s'</b> is a folder."
                                "<br><br>Operation failed !!!"
                                % (current_file))
                    errorPopup(self.mainWindow, errorMsg)
                    return
                elif os.path.exists(file_selected):
                    self.entryBox.fileExists(file_selected)
                    return
                else:
                    self.entryBox.doSelected(file_selected)
                    return
            else:
                self.addFile(file_selected)

    def updateLastDir(self, path):
        self.lastDir = path

    def showAbout(self):
        self.about.launch()

    def closeApp(self, obj=False, trash=False):
        elementary.exit()
    
    def closeChecks(self, obj=False):
        allSaved = True
        
        for en in self.fileEntries:
            if not en.isSaved:
                allSaved = False
        
        if allSaved:
            self.closeApp()
        else:
            self.unsavedWorkPopup()
    
    def closePopup(self, bt, confirmPopup):
        self.confirmPopup.delete()
        self.confirmPopup = None
    
    def unsavedWorkPopup(self):
        self.confirmPopup = Popup(self.mainWindow,
                                  size_hint_weight=EXPAND_BOTH)

        # Add a table to hold dialog image and text to Popup
        tb = Table(self.confirmPopup, size_hint_weight=EXPAND_BOTH)
        self.confirmPopup.part_content_set("default", tb)
        tb.show()

        # Add dialog-error Image to table
        need_ethumb()
        icon = Icon(self.confirmPopup, thumb='True')
        icon.standard_set('dialog-question')
        # Using gksudo or sudo fails to load Image here
        #   unless options specify using preserving their existing environment.
        #   may also fail to load other icons but does not raise an exception
        #   in that situation.
        # Works fine using eSudo as a gksudo alternative,
        #   other alternatives not tested
        try:
            dialogImage = Image(self.confirmPopup,
                                size_hint_weight=EXPAND_HORIZ,
                                size_hint_align=FILL_BOTH,
                                file=icon.file_get())
            tb.pack(dialogImage, 0, 0, 1, 1)
            dialogImage.show()
        except RuntimeError:
            # An error message is displayed for this same error
            #   when aboutWin is initialized so no need to redisplay.
            pass
        # Add dialog text to table
        dialogLabel = Label(self.confirmPopup, line_wrap=ELM_WRAP_WORD,
                            size_hint_weight=EXPAND_HORIZ,
                            size_hint_align=FILL_BOTH)
        dialogLabel.text = "You have unsaved work. Close anyways?<br><br>"
        tb.pack(dialogLabel, 1, 0, 1, 1)
        dialogLabel.show()

        # Close without saving button
        no_btt = Button(self.mainWindow)
        no_btt.text = "No"
        no_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        no_btt.show()
        # Save the file and then close button
        sav_btt = Button(self.mainWindow)
        sav_btt.text = "Yes"
        sav_btt.callback_clicked_add(self.closeApp)
        sav_btt.show()

        # add buttons to popup
        self.confirmPopup.part_content_set("button1", no_btt)
        self.confirmPopup.part_content_set("button3", sav_btt)
        self.confirmPopup.show()

    def eventsCb(self, obj, src, event_type, event):
        #print(obj)
        #print(src)
        #print(event.key.lower())
        #print(event_type)
        #print("")
        
        try:
            event.key
        except:
            return False
        
        if event.modifier_is_set("Control"):
            if event.key.lower() == "n":
                #newFile(self.newFile)
                threeCount(self.newFile)
            elif event.key.lower() == "s" and event.modifier_is_set("Shift"):
                self.saveAs()
            elif event.key.lower() == "s":
                self.saveFile()
            elif event.key.lower() == "z" and event.modifier_is_set("Shift"):
                threeCount(self.entryBox.reDo)
            elif event.key.lower() == "z":
                threeCount(self.entryBox.unDo)
            elif event.key.lower() == "o":
                self.openFile()
            elif event.key.lower() == "h":
                if not self.flip.front_visible_get():
                    #toggleHidden(self.fileSelector)
                    threeCount(self.fileSelector.toggleHidden)
            elif event.key.lower() == "q":
                #closeCtrlChecks(self)
                threeCount(self.closeChecks)
            elif event.key.lower() == "f":
                #toggleFind(self)
                threeCount(self.showFind)
            
        if event.key.lower() in ["space", "backspace", "return"]:
            threeCount(self.entryBox.takeSnapShot)

    def launch(self, start=[]):
        if start[0]:
            for count, ourFile in enumerate(start[0]):
                if os.path.dirname(ourFile) == '':
                    start[0][count] = os.getcwd() + '/' + ourFile
        
        if start and start[0]:
            for count, ourFile in enumerate(start[0]):
                if os.path.isdir(os.path.dirname(ourFile)):
                    if os.path.isfile(ourFile):
                        #print(ourFile)
                        self.addFile(ourFile)
                else:
                    print("Error: {0} is an Invalid Path".format(ourFile))
                    errorMsg = ("<b>'%s'</b> is an Invalid path."
                                "<br><br>Open failed !!!" % (ourFile))
                    errorPopup(self.mainWindow, errorMsg)
        if start and start[1]:
            if os.path.isdir(start[1]):
                print("Initializing file selection path: {0}".format(start[1]))
                self.lastDir = start[1]
            else:
                print("Error: {0} is an Invalid Path".format(start[1]))
        
        if not len(self.fileEntries):
            self.addFile("Untitled")
        
        self.mainWindow.show()

class ePadEntry(Box):
    def __init__(self, parent, canvas, lineNums):
        Box.__init__(self, canvas)
        self._parent = parent
        self._canvas = canvas
        
        self.size_hint_weight = EXPAND_BOTH
        self.size_hint_align = FILL_BOTH
        
        self.entryBox = Box(self._canvas,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.entryBox.horizontal = True
        self.entryBox.show()

        # Initialize Text entry box and line label
        self.lineList = Entry(self._canvas, 
                           scrollable=False, editable=False,
                           size_hint_weight=(0.0, EVAS_HINT_EXPAND),
                           size_hint_align=(0.0, 0.0),
                           line_wrap=ELM_WRAP_NONE)
        self.lineList.text_style_user_push("DEFAULT='font_size=14'")
        self.currentLinesShown = 1
        self.lineList.text_set("1<br>")
        
        self.lineNums = lineNums
        
        self.mainEn = Entry(self._canvas, scrollable=False,
                            line_wrap=self._parent.wordwrap, autosave=False,
                            size_hint_weight=(0.85, EVAS_HINT_EXPAND),
                            size_hint_align=FILL_BOTH)
        self.mainEn.callback_changed_user_add(self.textEdited)
        self.mainEn.callback_clicked_add(resetCloseMenuCount)
        self.mainEn.callback_selection_cut_add(self.takeSnapShot)
        self.mainEn.callback_selection_paste_add(self.takeSnapShot)
        self.mainEn.text_style_user_push("DEFAULT='font_size=14'")
        
        self.totalLines = 0
        self.mainEn.show()
        self.mainEn.focus_set(True)
        
        if lineNums:
            self.lineList.show()
            self.entryBox.pack_end(self.lineList)
        self.entryBox.pack_end(self.mainEn)
        
        self.scr = Scroller(self._canvas,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.scr.content = self.entryBox
        self.scr.show()
        
        self.pack_end(self.scr)
        
        # Add label to show current cursor position
        if SHOW_POS:
            self.line_label = Label(self._canvas,
                                    size_hint_weight=EXPAND_HORIZ,
                                    size_hint_align=ALIGN_RIGHT)

            self.mainEn.callback_cursor_changed_add(self.curChanged,
                                                    self.line_label)
            self.curChanged(self.mainEn, self.line_label)
            self.line_label.show()
            self.pack_end(self.line_label)
            
        self.button = None
        self.close = None
        self.sep = None
        self.isNewFile = True
        self.isSaved = True
        self.doArchive = []
        self.doSpot = 0
        self.takeSnapShot()
    
    def takeSnapShot(self, obj=None):
        if self.doSpot != len(self.doArchive)-1:
            for i in range(self.doSpot+1, len(self.doArchive)):
                self.doArchive.pop(self.doSpot+1)
            
        curPos = self.mainEn.cursor_pos_get()
        entryGet = self.mainEn.entry_get()
        
        if self.doSpot == 0:
            self.saveSnapShot(curPos, entryGet)
        elif entryGet != self.doArchive[self.doSpot][1]:
            self.saveSnapShot(curPos, entryGet)
    
    def saveSnapShot(self, curPos, entryGet):
        self.doArchive.append([curPos, entryGet])
            
        if len(self.doArchive) > 30:
            self.doArchive.pop(0)
            
        self.doSpot = len(self.doArchive) - 1
            
        #print("Taking snapshot")
    
    def unDo(self):
        if self.doSpot > 0:
            #A check if this is the first time we are undoing that we store the latest data
            if self.doSpot == len(self.doArchive) - 1:
                if self.doArchive[self.doSpot][1] != self.mainEn.entry_get():
                    self.takeSnapShot()
            #print("undoing")
            self.doSpot -= 1
            self.mainEn.entry_set(self.doArchive[self.doSpot][1])
            self.mainEn.cursor_pos_set(self.doArchive[self.doSpot][0])
    
    def reDo(self):
        if self.doSpot + 1 < len(self.doArchive):
            #print("redoing")
            self.doSpot += 1
            self.mainEn.entry_set(self.doArchive[self.doSpot][1])
            self.mainEn.cursor_pos_set(self.doArchive[self.doSpot][0])
    
    def checkLineNumbers(self):
        if self.currentLinesShown < self.totalLines:
            lines = ""
            for i in range(self.currentLinesShown+1, self.totalLines+1):
                lines = "%s%s<br>"%(lines, i)
            self.lineList.entry_append("%s"%lines)
            self.currentLinesShown = self.totalLines
        elif self.currentLinesShown > self.totalLines:
            lines = ""
            
            for i in range(1, self.totalLines+1):
                lines = "%s%s<br>"%(lines, i)
            
            self.lineList.entry_set(lines)
            
            self.currentLinesShown = self.totalLines
            
    def curChanged(self, entry, label):
        # get linear index into current text
        index = entry.cursor_pos_get()
        # Replace <br /> tag with single char
        #   to simplify (line, col) calculation
        tmp_text = markup_to_utf8(entry.entry_get())
        self.totalLines = tmp_text.count("\n")+1
        if self.lineNums:
            self.checkLineNumbers()
        line = tmp_text[:index].count("\n") + 1
        col = len(tmp_text[:index].split("\n")[-1]) + 1
        # Update label text with line, col
        label.text = "Ln {0} Col {1} ".format(line, col)
    
    def textEdited(self, obj=None):
        current_file = self.mainEn.file[0]
        current_file = \
            os.path.basename(current_file) if \
            current_file and not self.isNewFile else \
            "Untitled"
        self._parent.mainWindow.title = "*%s - ePad" % (current_file)
        self.button.text = "*%s"%current_file
        self.isSaved = False
    
    def openFile(self, filePath):
        try:
            self.mainEn.file_set(filePath, ELM_TEXT_FORMAT_PLAIN_UTF8)
        except RuntimeError as msg:
            print("Empty file: {0}".format(filePath))
        self.isNewFile = False
        #Reset undo/redo tracks when we open a file
        self.doArchive = []
        self.doSpot = 0
        self.takeSnapShot()
    
    def setWidgets(self, btn, cls, sep):
        self.button = btn
        self.close = cls
        self.sep = sep
        
    def closeChecks(self, ourCallback=None):
        print("File is Saved: ", self.isSaved)
        self.confirmSave(ourCallback)
        
    def confirmSave(self, ourCallback=None):
        self.confirmPopup = Popup(self._parent.mainWindow,
                                  size_hint_weight=EXPAND_BOTH)
        self.confirmPopup.part_text_set("title,text", "File Unsaved")
        current_file = self.mainEn.file[0]
        current_file = \
            os.path.basename(current_file) if current_file else "Untitled"
        self.confirmPopup.text = "Save changes to '%s'?" % (current_file)
        # Close without saving button
        no_btt = Button(self._parent.mainWindow)
        no_btt.text = "No"
        no_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        if ourCallback is not None:
            no_btt.callback_clicked_add(ourCallback, self.button, True)
        no_btt.show()
        # cancel close request
        cancel_btt = Button(self._parent.mainWindow)
        cancel_btt.text = "Cancel"
        cancel_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        cancel_btt.show()
        # Save the file and then close button
        sav_btt = Button(self._parent.mainWindow)
        sav_btt.text = "Yes"
        sav_btt.callback_clicked_add(self._parent.saveFile)
        sav_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        sav_btt.show()

        # add buttons to popup
        self.confirmPopup.part_content_set("button1", no_btt)
        self.confirmPopup.part_content_set("button2", cancel_btt)
        self.confirmPopup.part_content_set("button3", sav_btt)
        self.confirmPopup.show()
    
    def closePopup(self, bt, confirmPopup):
        self.confirmPopup.delete()
        self.confirmPopup = None
        
    def fileExists(self, filePath):
        self.confirmPopup = Popup(self._parent.mainWindow,
                                  size_hint_weight=EXPAND_BOTH)

        # Add a table to hold dialog image and text to Popup
        tb = Table(self.confirmPopup, size_hint_weight=EXPAND_BOTH)
        self.confirmPopup.part_content_set("default", tb)
        tb.show()

        # Add dialog-error Image to table
        need_ethumb()
        icon = Icon(self.confirmPopup, thumb='True')
        icon.standard_set('dialog-question')
        # Using gksudo or sudo fails to load Image here
        #   unless options specify using preserving their existing environment.
        #   may also fail to load other icons but does not raise an exception
        #   in that situation.
        # Works fine using eSudo as a gksudo alternative,
        #   other alternatives not tested
        try:
            dialogImage = Image(self.confirmPopup,
                                size_hint_weight=EXPAND_HORIZ,
                                size_hint_align=FILL_BOTH,
                                file=icon.file_get())
            tb.pack(dialogImage, 0, 0, 1, 1)
            dialogImage.show()
        except RuntimeError:
            # An error message is displayed for this same error
            #   when aboutWin is initialized so no need to redisplay.
            pass
        # Add dialog text to table
        dialogLabel = Label(self.confirmPopup, line_wrap=ELM_WRAP_WORD,
                            size_hint_weight=EXPAND_HORIZ,
                            size_hint_align=FILL_BOTH)
        current_file = os.path.basename(filePath)
        dialogLabel.text = "'%s' already exists. Overwrite?<br><br>" \
                           % (current_file)
        tb.pack(dialogLabel, 1, 0, 1, 1)
        dialogLabel.show()

        # Close without saving button
        no_btt = Button(self._parent.mainWindow)
        no_btt.text = "No"
        no_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        no_btt.show()
        # Save the file and then close button
        sav_btt = Button(self._parent.mainWindow)
        sav_btt.text = "Yes"
        sav_btt.callback_clicked_add(self.doSelected)
        sav_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        sav_btt.show()

        # add buttons to popup
        self.confirmPopup.part_content_set("button1", no_btt)
        self.confirmPopup.part_content_set("button3", sav_btt)
        self.confirmPopup.show()
        
    def doSelected(self, obj):
        # Something I should avoid but here I prefer a polymorphic function
        if isinstance(obj, Button):
            file_selected = self._parent.fileSelector.selected_get()
        else:
            file_selected = obj

        IsSave = self._parent.fileSelector.mode
        if file_selected:
            if IsSave == "save":
                try:
                    newfile = open(file_selected, 'w')
                except IOError as err:
                    print("ERROR: {0}: '{1}'".format(err.strerror,
                                                     file_selected))
                    if err.errno == errno.EACCES:
                        errorMsg = ("Permision denied: <b>'%s'</b>."
                                    "<br><br>Operation failed !!!</br>"
                                    % (file_selected))
                        errorPopup(self._parent.mainWindow, errorMsg)
                    else:
                        errorMsg = ("ERROR: %s: '%s'"
                                    "<br><br>Operation failed !!!</br>"
                                    % (err.strerror, file_selected))
                        errorPopup(self._parent.mainWindow, errorMsg)
                    return
                tmp_text = self.mainEn.entry_get()
                # FIXME: Why save twice?
                newfile.write(tmp_text)
                newfile.close()
                # Suppress error message when empty file is saved
                try:
                    self.mainEn.file_set(file_selected,
                                         ELM_TEXT_FORMAT_PLAIN_UTF8)
                except RuntimeError:
                    print("Empty file saved:{0}".format(file_selected))
                self.mainEn.entry_set(tmp_text)
                # if empty file entry.file_save destroys file :(
                if len(tmp_text):
                    self.mainEn.file_save()
                self._parent.mainWindow.title_set("%s - ePad"
                                          % os.path.basename(file_selected))
                self.button.text = os.path.basename(file_selected)
                self.isSaved = True
                self.isNewFile = False
            else:
                if os.path.isdir(file_selected):
                    print("ERROR: {0}: is a directory. "
                          "Could not set file.".format(file_selected))
                    current_file = os.path.basename(file_selected)
                    errorMsg = ("<b>'%s'</b> is a folder."
                                "<br><br>Operation failed !!!</br>"
                                % (current_file))
                    errorPopup(self._parent.mainWindow, errorMsg)
                    return
                # Test to see if file can be opened to catch permission errors
                #   as entry.file_set function does not differentiate
                #   different possible errors.
                try:
                    with open(file_selected) as f:
                        tmp_text = f.readline()
                except IOError as err:

                    if err.errno == errno.ENOENT:
                        print("Creating New file '{0}'".format(file_selected))
                        # self.fileSelector.current_name_set(file_selected)
                        self.isSaved = False
                    elif err.errno == errno.EACCES:
                        print("ERROR: {0}: '{1}'".format(err.strerror,
                              file_selected))
                        errorMsg = ("Permision denied: <b>'%s'</b>."
                                    "<br><br>Operation failed !!!</br>"
                                    % (file_selected))
                        errorPopup(self._parent.mainWindow, errorMsg)
                        return
                    else:
                        print("ERROR: {0}: '{1}'".format(err.strerror,
                              file_selected))
                        errorMsg = ("ERROR: %s: '%s'"
                                    "<br><br>Operation failed !!!</br>"
                                    % (err.strerror, file_selected))
                        errorPopup(self._parent.mainWindow, errorMsg)
                        return
                try:
                    self.mainEn.file_set(file_selected,
                                         ELM_TEXT_FORMAT_PLAIN_UTF8)
                except RuntimeError as msg:
                    # Entry.file_set fails on empty files
                    print("Empty file: {0}".format(file_selected))
                self._parent.mainWindow.title_set("%s - ePad"
                                          % os.path.basename(file_selected))

                self.button.text = os.path.basename(file_selected)

                self.mainEn.focus_set(True)
    

class ePadFindBox(Box):
    def __init__(self, parent, canvas):
        Box.__init__(self, canvas)
        self._parent = parent
        self._canvas = canvas
        
        self.size_hint_weight = EXPAND_HORIZ
        self.size_hint_align = FILL_HORIZ
        
        self.currentFind = None
        self.lastSearch = None
        
        frameBox = Box(self._canvas, size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        frameBox.horizontal = True
        frameBox.show()
        
        findBox = Frame(self._canvas, size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        findBox.text = "Find Text:"
        findBox.show()
        
        self.findEntry = Entry(self._canvas, size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        self.findEntry.single_line_set(True)
        self.findEntry.scrollable_set(True)
        self.findEntry.callback_activated_add(self.findPressed)
        self.findEntry.show()
        
        findBox.content = self.findEntry
        
        replaceBox = Frame(self._canvas, size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        replaceBox.text = "Replace Text:"
        replaceBox.show()
        
        self.replaceEntry = Entry(self._canvas, size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        self.replaceEntry.single_line_set(True)
        self.replaceEntry.scrollable_set(True)
        self.replaceEntry.show()
        
        replaceBox.content = self.replaceEntry
        
        frameBox.pack_end(findBox)
        frameBox.pack_end(replaceBox)
        
        buttonBox = Box(self._canvas, size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        buttonBox.horizontal = True
        buttonBox.show()
        
        findButton = Button(self._canvas)
        findButton.text = "Find Next"
        findButton.callback_pressed_add(self.findPressed)
        findButton.show()
        
        replaceButton = Button(self._canvas)
        replaceButton.text = "Replace All"
        replaceButton.callback_pressed_add(self.replacePressed)
        replaceButton.show()
        
        closeButton = Button(self._canvas)
        closeButton.text = "Done"
        closeButton.callback_pressed_add(self._parent.showFind)
        closeButton.show()
        
        self.caseCheck = Check(self._canvas)
        self.caseCheck.text = "Case Sensitive"
        self.caseCheck.show()
        
        buttonBox.pack_end(self.caseCheck)
        buttonBox.pack_end(findButton)
        buttonBox.pack_end(replaceButton)
        buttonBox.pack_end(closeButton)
        
        self.pack_end(frameBox)
        self.pack_end(buttonBox)
        
    def replacePressed(self, obj):
        tmp_text = markup_to_utf8(self._parent.entryBox.mainEn.entry_get())
        if not self.caseCheck.state_get():
            search_string = self.findEntry.text.lower()
            locations = list(self.findAll(tmp_text.lower(), search_string))
        else:
            search_string = self.findEntry.text
            locations = list(self.findAll(tmp_text, search_string))
        search_length = len(search_string)
        if search_length:
            replace_string = self.replaceEntry.text
            if replace_string:
                if len(locations):
                    if not self.caseCheck.state_get():
                        ourRe = re.compile(search_string, re.IGNORECASE)
                    else:
                        ourRe = re.compile(search_string)
                    tmp_text = ourRe.sub(replace_string, tmp_text).encode('utf-8').strip()
                    tmp_text = utf8_to_markup(tmp_text)
                    curPos = self._parent.entryBox.mainEn.cursor_pos_get()
                    self._parent.entryBox.mainEn.text_set(tmp_text)
                    try:
                        self._parent.entryBox.mainEn.cursor_pos_set(curPos)
                    except:
                        print("Error: Can't set cursor position")
                    self._parent.entryBox.textEdited()
                    self._parent.entryBox.takeSnapShot()
                else:
                    errorPopup(self._parent.mainWindow, "Text %s not found. Nothing replaced."%search_string)
            else:
                errorPopup(self._parent.mainWindow, "No replacement string entered.")
        else:
            errorPopup(self._parent.mainWindow, "No find string entered.")
    
    def findPressed(self, obj):
        if not self.caseCheck.state_get():
            search_string = self.findEntry.text.lower()
            tmp_text = markup_to_utf8(self._parent.entryBox.mainEn.entry_get()).lower()
        else:
            search_string = self.findEntry.text
            tmp_text = markup_to_utf8(self._parent.entryBox.mainEn.entry_get())
        search_length = len(search_string)
        if search_length:
            locations = list(self.findAll(tmp_text, search_string))
            if len(locations):
                if self.currentFind == None or search_string != self.lastSearch:
                    self.lastSearch = search_string
                    self.currentFind = locations[0]
                else:
                    lastFind = locations.index(self.currentFind)
                    if lastFind < len(locations)-1:
                        self.currentFind = locations[lastFind+1]
                    else:
                        self.currentFind = locations[0]
                self._parent.entryBox.mainEn.select_region_set(self.currentFind, self.currentFind+search_length)
            else:
                errorPopup(self._parent.mainWindow, "Text %s not found."%search_string)
        else:
            errorPopup(self._parent.mainWindow, "No find string entered.")

    def findAll(self, a_str, sub):
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1: return
            yield start
            start += len(sub) + 1

    
class ePadToolbar(Toolbar):
    def __init__(self, parent, canvas):
        Toolbar.__init__(self, canvas)
        self._parent = parent
        self._canvas = canvas

        self.homogeneous = False
        self.size_hint_weight = (0.0, 0.0)
        self.size_hint_align = (EVAS_HINT_FILL, 0.0)
        self.select_mode = ELM_OBJECT_SELECT_MODE_DEFAULT
        self.callback_clicked_add(self.itemClicked)

        self.menu_parent = canvas

        self.item_append("document-new", "New",
                         lambda self, obj: self._parent.newFile())
        self.item_append("document-open", "Open",
                         lambda self, obj: self._parent.openFile())
        self.item_append("document-save", "Save",
                         lambda self, obj: self._parent.saveFile())
        self.item_append("document-save-as", "Save As",
                         lambda self, obj: self._parent.saveAs())
        # -- Edit Dropdown Menu --
        tb_it = self.item_append("gtk-edit", "Edit")
        tb_it.menu = True
        menu = tb_it.menu
        menu.item_add(None, "Undo", "edit-undo", self.unDoPress)
        menu.item_add(None, "Redo", "edit-redo", self.reDoPress)
        menu.item_separator_add()
        menu.item_add(None, "Copy", "edit-copy", self.copyPress)
        menu.item_add(None, "Paste", "edit-paste", self.pastePress)
        menu.item_add(None, "Cut", "edit-cut", self.cutPress)
        menu.item_separator_add()
        menu.item_add(None, "Select All", "edit-select-all",
                      self.selectAllPress)
        
        self.item_append("gtk-find", "Find",
                         lambda self, obj: self._parent.showFind())
        # -----------------------
        #
        # -- Options Dropdown Menu --
        #
        # self.item_append("settings", "Options", self.optionsPress)
        tb_it = self.item_append("preferences-desktop", "Options")
        tb_it.menu = True
        menu = tb_it.menu
        self._parent.wordwrap = WORD_WRAP
        '''it = menu.item_add(None, "Wordwrap", None, self.optionsWWPress)
        chk = Check(canvas, disabled=True)
        it.content = chk
        if self._parent.wordwrap == ELM_WRAP_MIXED:
            it.content.state = True
        else:
            it.content.state = False'''
            
        it = menu.item_add(None, "Line Numbers", None, self.optionsLineNums)
        chk = Check(canvas, disabled=True)
        it.content = chk
        it.content.state = True
        
        '''it = menu.item_add(None, "New Instance", None, self.optionsNew)
        chk = Check(canvas, disabled=True)
        it.content = chk
        if self._parent.newInstance:
            it.content.state = True
        else:
            it.content.state = False'''

        # ---------------------------

        self.item_append("dialog-information", "About",
                         self.showAbout)

    def showAbout(self, obj, it):
        AboutWindow(self, title="ePad", standardicon="accessories-text-editor", \
                        version=__version__, authors=AUTHORS, \
                        licen=LICENSE, webaddress=__github__, \
                        info=INFO)

    def optionsWWPress(self, obj, it):
        wordwrap = self._parent.entryBox.mainEn.line_wrap
        if wordwrap == ELM_WRAP_MIXED:
            wordwrap = ELM_WRAP_NONE
            it.content.state = False
        else:
            wordwrap = ELM_WRAP_MIXED
            it.content.state = True
        self._parent.entryBox.mainEn.line_wrap = wordwrap
        resetCloseMenuCount(None)

    def unDoPress(self, obj, it):
        self._parent.entryBox.unDo()
        resetCloseMenuCount(None)
    
    def reDoPress(self, obj, it):
        self._parent.entryBox.reDo()
        resetCloseMenuCount(None)

    def copyPress(self, obj, it):
        self._parent.entryBox.mainEn.selection_copy()
        resetCloseMenuCount(None)

    def itemClicked(self, obj):
        item = obj.selected_item_get()
        if item.menu_get() is None and item.selected_get():
            item.selected_set(False)
        elif item.menu_get():
            closeMenu(item, item.text_get())

    def pastePress(self, obj, it):
        self._parent.entryBox.mainEn.selection_paste()
        resetCloseMenuCount(None)

    def cutPress(self, obj, it):
        self._parent.entryBox.mainEn.selection_cut()
        resetCloseMenuCount(None)

    def selectAllPress(self, obj, it):
        self._parent.entryBox.mainEn.select_all()
        resetCloseMenuCount(None)

    def optionsNew(self, obj, it):
        self._parent.newInstance = not self._parent.newInstance
        if self._parent.newInstance:
            it.content.state = True
        else:
            it.content.state = False
        resetCloseMenuCount(None)
    
    def optionsLineNums(self, obj, it):
        self._parent.entryBox.lineNums = not self._parent.entryBox.lineNums
        self._parent.lineNums = not self._parent.lineNums
        if self._parent.entryBox.lineNums:
            it.content.state = True
            for en in self._parent.fileEntries:
                en.entryBox.pack_before(en.lineList, en.mainEn)
                en.checkLineNumbers()
                en.lineList.show()
        else:
            it.content.state = False
            for en in self._parent.fileEntries:
                en.entryBox.unpack(en.lineList)
                en.lineList.hide()

if __name__ == "__main__":

    ourFiles = sys.argv
    
    #Remove ePad.py from the arguments
    del ourFiles[0]
    
    #print(ourFiles)

    # Start App
    elementary.init()
    GUI = Interface()
    if ourFiles:
        print("Opening files: '{0}'".format(ourFiles))
        GUI.launch([ourFiles, None])
    else:
        GUI.launch([None, os.getcwd()])
    elementary.run()

    # Shutdown App
    elementary.shutdown()
