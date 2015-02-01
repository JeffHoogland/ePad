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
__version__ = "0.6.2"
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
from efl.elementary.list import List
from efl.elementary.frame import Frame
from efl.elementary.entry import Entry, ELM_TEXT_FORMAT_PLAIN_UTF8, \
        markup_to_utf8, ELM_WRAP_NONE, ELM_WRAP_MIXED
from efl.elementary.popup import Popup
from efl.elementary.toolbar import Toolbar, ELM_OBJECT_SELECT_MODE_DEFAULT
from efl.elementary.flip import Flip, ELM_FLIP_ROTATE_XZ_CENTER_AXIS, \
        ELM_FLIP_ROTATE_YZ_CENTER_AXIS, ELM_FLIP_INTERACTION_ROTATE
from efl.elementary.table import Table
from efl.elementary.transit import Transit, \
        ELM_TRANSIT_EFFECT_WIPE_TYPE_HIDE, ELM_TRANSIT_EFFECT_WIPE_DIR_RIGHT
from efl.elementary.check import Check
from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
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


def toggleHidden(fileSelector):
    if not hasattr(toggleHidden, 'count'):
        toggleHidden.count = 0
    if toggleHidden.count == 1:
        showHidden = fileSelector.hidden_visible_get()
        fileSelector.hidden_visible_set(not showHidden)
        SHOW_HIDDEN = not showHidden
    # Modulo 4 Hack because this function is called
    #   four times each time Ctrl-h is pressed
    toggleHidden.count = (toggleHidden.count + 1) % 4


# Same Modulo 4 Hack because this function is called
    #   four times each time Ctrl-q is pressed
def closeCtrlChecks(win):
    if not hasattr(closeCtrlChecks, 'count'):
        closeCtrlChecks.count = 0
    if closeCtrlChecks.count == 3:
        win.closeChecks(win)
    closeCtrlChecks.count = (closeCtrlChecks.count + 1) % 4


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
        self.mainWindow = StandardWindow("epad", "Untitled - ePad",
                                         size=(600, 400))
        self.mainWindow.callback_delete_request_add(self.closeChecks)
        self.mainWindow.elm_event_callback_add(self.eventsCb)

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
        # Initialize Text entry box and line label

        self.lineList = Entry(self.mainWindow,
                           size_hint_weight=(0.052, EVAS_HINT_EXPAND),
                           size_hint_align=FILL_BOTH)
        self.lineList.text_style_user_push("DEFAULT='font_size=14'")
        self.lineList.editable_set(False)
        self.currentLinesShown = 1
        self.lineList.entry_append("<font_size=14>1<br>")
        self.lineList.show()
        
        self.lineNums = True

        self.entryBox = Box(self.mainWindow,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.entryBox.horizontal = True
        self.entryBox.show()
        
        self.scr = Scroller(self.mainWindow,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.scr.content = self.entryBox
        self.scr.show()
        
        self.entryBox.pack_end(self.lineList)
        self.mainBox.pack_end(self.scr)

        # FIXME: self.wordwrap initialized by ePadToolbar
        print("Word wrap Initialized: {0}".format(self.wordwrap))
        self.entryInit()

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

        self.isSaved = True
        self.isNewFile = False
        self.confirmPopup = None
        self.fileExistsFlag = False

    def entryInit(self):
        self.mainEn = Entry(self.mainWindow, scrollable=True,
                            line_wrap=self.wordwrap, autosave=False,
                            size_hint_weight=EXPAND_BOTH,
                            size_hint_align=FILL_BOTH)
        self.mainEn.callback_changed_user_add(self.textEdited)
        self.mainEn.elm_event_callback_add(self.eventsCb)
        self.mainEn.callback_clicked_add(resetCloseMenuCount)
        self.mainEn.text_style_user_push("DEFAULT='font_size=14'")
        # delete line lable if it exist so we can create and add new one
        #    Later need to rethink logic here
        try:
            self.line_label.delete()
        except AttributeError:
            pass
        # Add label to show current cursor position
        if SHOW_POS:
            self.line_label = Label(self.mainWindow,
                                    size_hint_weight=EXPAND_HORIZ,
                                    size_hint_align=ALIGN_RIGHT)

            self.mainEn.callback_cursor_changed_add(self.curChanged,
                                                    self.line_label)
            self.curChanged(self.mainEn, self.line_label)
            self.line_label.show()
            self.mainBox.pack_end(self.line_label)
        # self.mainEn.markup_filter_append(self.textFilter)
        self.totalLines = 0
        self.mainEn.show()
        self.mainEn.focus_set(True)
        self.entryBox.pack_end(self.mainEn)

    def checkLineNumbers(self):
        if self.currentLinesShown != self.totalLines:
            if self.currentLinesShown < self.totalLines:
                for i in range(self.currentLinesShown, self.totalLines):
                    linNum = i+1
                    self.lineList.entry_append("<font_size=14>%s<br>"%linNum)
            else:
                self.lineList.entry_set("")
                for i in range(self.totalLines):
                    linNum = i+1
                    self.lineList.entry_append("<font_size=14>%s<br>"%linNum)
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

    def textEdited(self, obj):
        current_file = self.mainEn.file[0]
        current_file = \
            os.path.basename(current_file) if \
            current_file and not self.isNewFile else \
            "Untitled"
        self.mainWindow.title = "*%s - ePad" % (current_file)
        self.isSaved = False

    def newFile(self, obj=None, ignoreSave=False):
        if self.newInstance:

            # sh does not properly handle space between -d and path
            command = "epad -d'{0}'".format(self.lastDir)
            print("Launching new instance: {0}".format(command))
            ecore.Exe(command, ecore.ECORE_EXE_PIPE_READ |
                      ecore.ECORE_EXE_PIPE_ERROR | ecore.ECORE_EXE_PIPE_WRITE)
            return
        if self.isSaved is True or ignoreSave is True:
            trans = Transit()
            trans.object_add(self.mainEn)
            trans.auto_reverse = True

            trans.effect_wipe_add(
                ELM_TRANSIT_EFFECT_WIPE_TYPE_HIDE,
                ELM_TRANSIT_EFFECT_WIPE_DIR_RIGHT)

            trans.duration = 0.5
            trans.go()

            time.sleep(0.5)

            self.mainWindow.title_set("Untitled - ePad")
            self.mainEn.delete()
            self.entryInit()
            self.isNewFile = True

        elif self.confirmPopup is None:
            self.confirmSave(self.newFile)
        self.mainEn.focus_set(True)

    def openFile(self, obj=None, ignoreSave=False):
        if self.isSaved is True or ignoreSave is True:
            self.fileSelector.setMode("Open")
            self.fileLabel.text = "<b>Select a text file to open:</b>"
            self.flip.go(ELM_FLIP_ROTATE_YZ_CENTER_AXIS)
        elif self.confirmPopup is None:
            self.confirmSave(self.openFile)

    def confirmSave(self, ourCallback=None):
        self.confirmPopup = Popup(self.mainWindow,
                                  size_hint_weight=EXPAND_BOTH)
        self.confirmPopup.part_text_set("title,text", "File Unsaved")
        current_file = self.mainEn.file[0]
        current_file = \
            os.path.basename(current_file) if current_file else "Untitled"
        self.confirmPopup.text = "Save changes to '%s'?" % (current_file)
        # Close without saving button
        no_btt = Button(self.mainWindow)
        no_btt.text = "No"
        no_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        if ourCallback is not None:
            no_btt.callback_clicked_add(ourCallback, True)
        no_btt.show()
        # cancel close request
        cancel_btt = Button(self.mainWindow)
        cancel_btt.text = "Cancel"
        cancel_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        cancel_btt.show()
        # Save the file and then close button
        sav_btt = Button(self.mainWindow)
        sav_btt.text = "Yes"
        sav_btt.callback_clicked_add(self.saveFile)
        sav_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        sav_btt.show()

        # add buttons to popup
        self.confirmPopup.part_content_set("button1", no_btt)
        self.confirmPopup.part_content_set("button2", cancel_btt)
        self.confirmPopup.part_content_set("button3", sav_btt)
        self.confirmPopup.show()

    def fileSelCancelPressed(self, fs):
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)

    def saveAs(self):
        self.fileSelector.setMode("Save")
        self.fileLabel.text = "<b>Save new file to where:</b>"
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)

    def saveFile(self, obj=False):
        if self.mainEn.file_get()[0] is None or self.isNewFile:
            self.saveAs()
        else:
            file_selected = self.mainEn.file_get()[0]
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
            if not self.mainEn.is_empty:
                self.mainEn.file_save()
            self.mainWindow.title_set("%s - ePad"
                                      % os.path.basename(self.mainEn.file[0]))
            self.isSaved = True

    def doSelected(self, obj):

        # Something I should avoid but here I prefer a polymorphic function
        if isinstance(obj, Button):
            file_selected = self.fileSelector.selected_get()
        else:
            file_selected = obj

        IsSave = self.fileSelector.mode
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
                        errorPopup(self.mainWindow, errorMsg)
                    else:
                        errorMsg = ("ERROR: %s: '%s'"
                                    "<br><br>Operation failed !!!</br>"
                                    % (err.strerror, file_selected))
                        errorPopup(self.mainWindow, errorMsg)
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
                self.mainWindow.title_set("%s - ePad"
                                          % os.path.basename(file_selected))
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
                    errorPopup(self.mainWindow, errorMsg)
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
                        errorPopup(self.mainWindow, errorMsg)
                        return
                    else:
                        print("ERROR: {0}: '{1}'".format(err.strerror,
                              file_selected))
                        errorMsg = ("ERROR: %s: '%s'"
                                    "<br><br>Operation failed !!!</br>"
                                    % (err.strerror, file_selected))
                        errorPopup(self.mainWindow, errorMsg)
                        return
                try:
                    self.mainEn.file_set(file_selected,
                                         ELM_TEXT_FORMAT_PLAIN_UTF8)
                except RuntimeError as msg:
                    # Entry.file_set fails on empty files
                    print("Empty file: {0}".format(file_selected))
                self.mainWindow.title_set("%s - ePad"
                                          % os.path.basename(file_selected))

                self.mainEn.focus_set(True)

    def fileExists(self, filePath):

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
        current_file = os.path.basename(filePath)
        dialogLabel.text = "'%s' already exists. Overwrite?<br><br>" \
                           % (current_file)
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
        sav_btt.callback_clicked_add(self.doSelected)
        sav_btt.callback_clicked_add(self.closePopup, self.confirmPopup)
        sav_btt.show()

        # add buttons to popup
        self.confirmPopup.part_content_set("button1", no_btt)
        self.confirmPopup.part_content_set("button3", sav_btt)
        self.confirmPopup.show()

    def fileSelected(self, fs, file_selected, onStartup=False):
        if not onStartup:
            self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)
            # Markup can end up in file names because file_selector name_entry
            #   is an elementary entry. So lets sanitize file_selected.
            file_selected = markup_to_utf8(file_selected)
        if file_selected:
            print("File Selected: {0}".format(file_selected))
            self.lastDir = os.path.dirname(file_selected)
            fs.populateFiles(self.lastDir)
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
                    self.fileExistsFlag = True
                    self.fileExists(file_selected)
                    return
        self.doSelected(file_selected)

    def updateLastDir(self, path):
        self.lastDir = path

    def closeChecks(self, obj):
        print("File is Saved: ", self.isSaved)
        if not self.flip.front_visible_get():
            self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)
        elif self.isSaved is False and self.confirmPopup is None:
            self.confirmSave(self.closeApp)
        else:
            self.closeApp()

    def closePopup(self, bt, confirmPopup):
        self.confirmPopup.delete()
        self.confirmPopup = None

    def showAbout(self):
        self.about.launch()

    def closeApp(self, obj=False, trash=False):
        elementary.exit()

    def eventsCb(self, obj, src, event_type, event):
        if event.modifier_is_set("Control"):
            if event.key.lower() == "n":
                self.newFile()
            elif event.key.lower() == "s" and event.modifier_is_set("Shift"):
                self.saveAs()
            elif event.key.lower() == "s":
                self.saveFile()
            elif event.key.lower() == "o":
                self.openFile()
            elif event.key.lower() == "h":
                if not self.flip.front_visible_get():
                    toggleHidden(self.fileSelector)
            elif event.key.lower() == "q":
                closeCtrlChecks(self)

    # Legacy hack no longer needed
    #  there was an issue in elementary entry where it would
    #  accept those character controls

    # def textFilter( self, obj, theText, data ):
    #    # Block ctrl+hot keys used in eventsCb
    #    #
    #    #             Ctrl O   Ctrl N   Ctrl S
    #    ctrl_block = [chr(14), chr(15), chr(19)]
    #    if theText in ctrl_block:
    #        return None
    #    else:
    #        return theText

    def launch(self, start=[]):
        if start and start[0] and os.path.dirname(start[0]) == '':
                start[0] = os.getcwd() + '/' + start[0]
        if start and start[0]:
            if os.path.isdir(os.path.dirname(start[0])):
                self.fileSelected(self.fileSelector, start[0], True)
            else:
                print("Error: {0} is an Invalid Path".format(start))
                errorMsg = ("<b>'%s'</b> is an Invalid path."
                            "<br><br>Open failed !!!" % (start))
                errorPopup(self.mainWindow, errorMsg)
        if start and start[1]:
            if os.path.isdir(start[1]):
                print("Initializing file selection path: {0}".format(start[1]))
                self.fileSelector.populateFiles(start[1])
                self.lastDir = start[1]
            else:
                print("Error: {0} is an Invalid Path".format(start[1]))
        self.mainWindow.show()


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
        tb_it = self.item_append("edit", "Edit")
        tb_it.menu = True
        menu = tb_it.menu
        menu.item_add(None, "Copy", "edit-copy", self.copyPress)
        menu.item_add(None, "Paste", "edit-paste", self.pastePress)
        menu.item_add(None, "Cut", "edit-cut", self.cutPress)
        menu.item_separator_add()
        menu.item_add(None, "Select All", "edit-select-all",
                      self.selectAllPress)
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
        
        it = menu.item_add(None, "New Instance", None, self.optionsNew)
        chk = Check(canvas, disabled=True)
        it.content = chk
        if self._parent.newInstance:
            it.content.state = True
        else:
            it.content.state = False

        # ---------------------------

        self.item_append("dialog-information", "About",
                         self.showAbout)

    def showAbout(self, obj, it):
        AboutWindow(self, title="ePad", standardicon="accessories-text-editor", \
                        version=__version__, authors=AUTHORS, \
                        licen=LICENSE, webaddress=__github__, \
                        info=INFO)

    def optionsWWPress(self, obj, it):
        wordwrap = self._parent.mainEn.line_wrap
        if wordwrap == ELM_WRAP_MIXED:
            wordwrap = ELM_WRAP_NONE
            it.content.state = False
        else:
            wordwrap = ELM_WRAP_MIXED
            it.content.state = True
        self._parent.mainEn.line_wrap = wordwrap
        # FIXME: is this variable needed for anything?
        self._parent.wordwrap = wordwrap
        resetCloseMenuCount(None)

    def copyPress(self, obj, it):
        self._parent.mainEn.selection_copy()
        resetCloseMenuCount(None)

    def itemClicked(self, obj):
        item = obj.selected_item_get()
        if item.menu_get() is None and item.selected_get():
            item.selected_set(False)
        elif item.menu_get():
            closeMenu(item, item.text_get())

    def pastePress(self, obj, it):
        self._parent.mainEn.selection_paste()
        resetCloseMenuCount(None)

    def cutPress(self, obj, it):
        self._parent.mainEn.selection_cut()
        resetCloseMenuCount(None)

    def selectAllPress(self, obj, it):
        self._parent.mainEn.select_all()
        resetCloseMenuCount(None)

    def optionsNew(self, obj, it):
        self._parent.newInstance = not self._parent.newInstance
        if self._parent.newInstance:
            it.content.state = True
        else:
            it.content.state = False
        resetCloseMenuCount(None)
    
    def optionsLineNums(self, obj, it):
        self._parent.lineNums = not self._parent.lineNums
        if self._parent.lineNums:
            it.content.state = True
            self._parent.lineList.show()
            self._parent.lineList.size_hint_weight=(0.052, EVAS_HINT_EXPAND)
            self._parent.checkLineNumbers()
        else:
            it.content.state = False
            self._parent.lineList.size_hint_weight=(0.0, 0.0)
            self._parent.lineList.hide()

class CustomFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    # parts.append('%s %s' % (option_string, args_string))
                    parts.append('%s' % option_string)
                parts[-1] += ' %s' % args_string
            return ', '.join(parts)

if __name__ == "__main__":

    # Parse Arguments
    #   More arguments will be added with increased functionality

    parser = argparse.ArgumentParser(prog='epad',
                                     description=__description__,
                                     epilog=__source__,
                                     formatter_class=CustomFormatter)
    location = parser.add_mutually_exclusive_group()
    location.add_argument('filepath', nargs='?', metavar='filename',
                          help='path to file to open')
    # FIXME: add default value to directory option
    #           and remove fileSelector set_path code where not needed
    location.add_argument('-d', '--directory', action='store', metavar='',
                          help='initial directory for file selection')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s {0}'.format(__version__))
    results = parser.parse_args()
    ourFile, initDir = results.filepath, results.directory

    # Start App
    elementary.init()
    GUI = Interface()
    if ourFile:
        if ourFile[0:7] == "file://":
            # print(ourFile)
            try:
                ourFile = urllib.url2pathname(ourFile[7:])
            except AttributeError:
                # Python3
                import urllib.request
                ourFile = urllib.request.url2pathname(ourFile[7:])

        print("Opening file: '{0}'".format(ourFile))
        GUI.launch([ourFile, None])
    elif initDir:
        GUI.launch([None, initDir])
    else:
        GUI.launch([None, os.getcwd()])
    elementary.run()

    # Shutdown App
    elementary.shutdown()
