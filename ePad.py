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
__contirbutors__ = ["Jeff Hoogland", "Robert Wiley", "Kai Huuhko", "Scimmia22"]
__copyright__ = "Copyright (C) 2014 Bodhi Linux"
__version__ = "0.5.8 Beta"
__description__ = 'A simple text editor for the Enlightenment Desktop.'
__github__ = 'https://github.com/JeffHoogland/ePad'
__source__ = 'Source code and bug reports: {0}'.format(__github__)
PY_EFL = "https://git.enlightenment.org/bindings/python/python-efl.git/"


def printErr(*objs):
    print(*objs, file=sys.stderr)

import sys
import os
import time
try:
    from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
    from efl import elementary
    from efl.elementary.window import StandardWindow, Window
    from efl.elementary.window import ELM_WIN_DIALOG_BASIC
    from efl.elementary.background import Background
    from efl.elementary.box import Box
    from efl.elementary.button import Button
    from efl.elementary.label import Label
    from efl.elementary.icon import Icon
    from efl.elementary.entry import Entry, ELM_TEXT_FORMAT_PLAIN_UTF8, \
        markup_to_utf8
    from efl.elementary.popup import Popup
    from efl.elementary.toolbar import Toolbar, ELM_OBJECT_SELECT_MODE_NONE
    from efl.elementary.flip import Flip, ELM_FLIP_ROTATE_XZ_CENTER_AXIS, \
        ELM_FLIP_ROTATE_YZ_CENTER_AXIS, ELM_FLIP_INTERACTION_ROTATE
    from efl.elementary.fileselector import Fileselector
    from efl.elementary.transit import Transit, \
        ELM_TRANSIT_EFFECT_WIPE_TYPE_HIDE, ELM_TRANSIT_EFFECT_WIPE_DIR_RIGHT
    from efl.elementary.check import Check

    # Imported here to stop class resolver complaining when an input event
    # applies to an internal layout object
    from efl.elementary.layout import Layout
    # Imported here to stop ValueError exception msgs in Fileselector dialog
    from efl.elementary.genlist import Genlist
except ImportError:
    printErr("ImportError: Please install Python-EFL:\n            ", PY_EFL)
    exit(1)

EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
EXPAND_NONE = 0.0, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.5
ALIGN_CENTER = 0.5, 0.5
ALIGN_RIGHT = 1.0, 0.5
PADDING = 15, 0
WORD_WRAP = False
SHOW_POS = True
CASE_SENSITIVE = True
WHOLE_WORD = False


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

        self.mainTb = ePadToolbar(self, self.mainWindow)
        self.mainTb.show()
        self.mainBox.pack_end(self.mainTb)
        self.find = findWin(self, self.mainWindow)
        self.find.hide()
        # Initialize Text entry box
        print("Word wrap Initialized: {0}".format(self.wordwrap))
        self.entryInit()

        # Add label to show current cursor position
        if SHOW_POS:
            self.line_label = Label(self.mainWindow,
                                    size_hint_weight=EXPAND_HORIZ,
                                    size_hint_align=ALIGN_RIGHT)
            self.curChanged(self.mainEn, self.line_label)
            self.line_label.show()
            self.mainBox.pack_end(self.line_label)
            self.mainEn.callback_cursor_changed_add(self.curChanged,
                                                    self.line_label)

        # Build our file selector for saving/loading files
        self.fileBox = Box(self.mainWindow,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.fileBox.show()

        self.fileLabel = Label(self.mainWindow,
                               size_hint_weight=EXPAND_HORIZ,
                               size_hint_align=FILL_BOTH, text="")
        self.fileLabel.show()

        self.fileSelector = Fileselector(self.mainWindow, is_save=False,
                                         expandable=False, folder_only=False,
                                         path=os.getenv("HOME"),
                                         size_hint_weight=EXPAND_BOTH,
                                         size_hint_align=FILL_BOTH)
        self.fileSelector.callback_done_add(self.fileSelected)
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

    def entryInit(self):
        self.mainEn = Entry(self.mainWindow, scrollable=True,
                            line_wrap=self.wordwrap, autosave=False,
                            size_hint_weight=EXPAND_BOTH,
                            size_hint_align=FILL_BOTH)
        self.mainEn.callback_changed_user_add(self.textEdited)
        self.mainEn.elm_event_callback_add(self.eventsCb)
        # self.mainEn.markup_filter_append(self.textFilter)
        self.mainEn.show()
        try:
            self.mainBox.pack_before(self.mainEn, self.line_label)
        except AttributeError:
            # line_label has not been initialized on first run
            #   Should have better logic on all this
            self.mainBox.pack_end(self.mainEn)

    def curChanged(self, entry, label):
        # get linear index into current text
        index = entry.cursor_pos_get()
        # Replace <br /> tag with single char
        #   to simplify (line, col) calculation
        tmp_text = markup_to_utf8(entry.entry_get())
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

    def fileSelected(self, fs, file_selected, onStartup=False):
        if not onStartup:
            self.flip.go(ELM_FLIP_INTERACTION_ROTATE)
        print(file_selected)
        IsSave = fs.is_save_get()
        if file_selected:
            if IsSave:
                newfile = open(file_selected, 'w')
                tmp_text = self.mainEn.entry_get()
                newfile.write(tmp_text)
                newfile.close()
                self.mainEn.file_set(file_selected, ELM_TEXT_FORMAT_PLAIN_UTF8)
                self.mainEn.entry_set(tmp_text)
                self.mainEn.file_save()
                self.mainWindow.title_set("%s - ePad"
                                          % os.path.basename(file_selected))
                self.isSaved = True
                self.isNewFile = False
            else:
                try:
                    self.mainEn.file_set(file_selected,
                                         ELM_TEXT_FORMAT_PLAIN_UTF8)
                except RuntimeError:
                    print("Empty file: {0}".format(file_selected))
                self.mainWindow.title_set("%s - ePad"
                                          % os.path.basename(file_selected))

    def newFile(self, obj=None, ignoreSave=False):
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

    def openFile(self, obj=None, ignoreSave=False):
        if self.isSaved is True or ignoreSave is True:
            self.fileSelector.is_save_set(False)
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

    def saveAs(self):
        self.fileSelector.is_save_set(True)
        self.fileLabel.text = "<b>Save new file to where:</b>"
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)

    def saveFile(self, obj=False):
        if self.mainEn.file_get()[0] is None or self.isNewFile:
            self.saveAs()
        else:
            self.mainEn.file_save()
            self.mainWindow.title_set("%s - ePad"
                                      % os.path.basename(self.mainEn.file[0]))
            self.isSaved = True

    def closeChecks(self, obj):
        print(self.isSaved)
        if self.isSaved is False and self.confirmPopup is None:
            self.confirmSave(self.closeApp)
        else:
            self.closeApp()

    def closePopup(self, bt, confirmPopup):
        self.confirmPopup.delete()
        self.confirmPopup = None

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

    def showFind(self):
        self.find.findDialog.show()

    def launch(self, startingFile=False):
        if startingFile:
            self.fileSelected(self.fileSelector, startingFile, True)
        self.mainWindow.show()


class ePadToolbar(Toolbar):
    def __init__(self, parent, canvas):
        Toolbar.__init__(self, canvas)
        self._parent = parent
        self._canvas = canvas

        self.homogeneous = False
        self.size_hint_weight = (0.0, 0.0)
        self.size_hint_align = (EVAS_HINT_FILL, 0.0)
        self.select_mode = ELM_OBJECT_SELECT_MODE_NONE

        self.menu_parent = canvas

        self.item_append("document-new", "New",
                         lambda self, obj: self._parent.newFile())
        self.item_append("document-open", "Open",
                         lambda self, obj: self._parent.openFile())
        self.item_append("document-save", "Save",
                         lambda self, obj: self._parent.saveFile())
        self.item_append("document-save-as", "Save As",
                         lambda self, obj: self._parent.saveAs())
        self.item_append("edit-find", "Find",
                         lambda self, obj: self._parent.showFind())
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
        it = menu.item_add(None, "Wordwrap", None, self.optionsWWPress)
        chk = Check(canvas, disabled=True)
        it.content = chk

        # ---------------------------

        self.item_append("dialog-information", "About", self.aboutPress)

    def optionsWWPress(self, obj, it):
        wordwrap = self._parent.mainEn.line_wrap
        wordwrap = not wordwrap
        self._parent.mainEn.line_wrap = wordwrap
        it.content.state = wordwrap
        # FIXME: is this variable needed for anything?
        self._parent.wordwrap = wordwrap

    def copyPress(self, obj, it):
        self._parent.mainEn.selection_copy()

    def pastePress(self, obj, it):
        self._parent.mainEn.selection_paste()

    def cutPress(self, obj, it):
        self._parent.mainEn.selection_cut()

    def selectAllPress(self, obj, it):
        self._parent.mainEn.select_all()

    def aboutPress(self, obj, it):
        # About popup
        self.popupAbout = Popup(self._canvas, size_hint_weight=EXPAND_BOTH)
        self.popupAbout.part_text_set("title,text",
                                      "ePad version {0}".format(__version__))
        self.popupAbout.text = (
            "A simple text editor written in "
            "python and elementary<br><br> "
            "By: Jeff Hoogland"
            )
        bt = Button(self._canvas, text="Done")
        bt.callback_clicked_add(self.aboutClose)
        self.popupAbout.part_content_set("button1", bt)
        self.popupAbout.show()

    def aboutClose(self, bt):
        self.popupAbout.delete()


class findWin(Window):
    def __init__(self, parent, canvas):

        # Dialog Window Basics
        self.findDialog = Window('find', ELM_WIN_DIALOG_BASIC,  title='Find')
        self.findDialog.callback_delete_request_add(self.closeFind)

        self._parent = parent
        self._canvas = canvas
        #    Set Window Icon
        #       Icons work  in ubuntu min everything compiled
        #       but not bodhi rc3
        icon = Icon(self.findDialog,
                    size_hint_weight=EXPAND_BOTH,
                    size_hint_align=FILL_BOTH)
        icon.standard_set('edit-find')
        icon.show()
        self.findDialog.icon_object_set(icon.object_get())
        #    Set Dialog background
        background = Background(self.findDialog, size_hint_weight=EXPAND_BOTH)
        self.findDialog.resize_object_add(background)
        background.show()
        #    Main box to hold shit
        mainBox = Box(self.findDialog, size_hint_weight=EXPAND_BOTH)
        self.findDialog.resize_object_add(mainBox)
        mainBox.show()

        # Search Section
        #    Horizontal Box to hold search stuff
        seachBox = Box(self.findDialog, horizontal=True,
                       size_hint_weight=EXPAND_HORIZ,
                       size_hint_align=FILL_BOTH, padding=PADDING)
        seachBox.show()
        mainBox.pack_end(seachBox)
        #    Label for search entry
        seachLabel = Label(self.findDialog, text="Search for:",
                           size_hint_weight=EXPAND_NONE,
                           size_hint_align=FILL_HORIZ)
        seachBox.pack_end(seachLabel)
        seachLabel.show()
        #    Search Entry
        self.sent = Entry(self.findDialog, scrollable=True, single_line=True,
                          size_hint_weight=EXPAND_HORIZ,
                          size_hint_align=FILL_HORIZ)
        self.sent.callback_activated_add(self.find)  # Enter activates find fn
        self.sent.show()
        seachBox.pack_end(self.sent)

        #    Check boxs for Search Options
        #   FIXME: add callbacks  These states should be in config file
        caseCk = Check(self.findDialog, text="Case sensitive",
                       size_hint_weight=EXPAND_BOTH,
                       size_hint_align=FILL_HORIZ, state=CASE_SENSITIVE)
        caseCk.callback_changed_add(self.ckCase)
        caseCk.show()
        mainBox.pack_end(caseCk)
        wordCk = Check(self.findDialog, text="Match only a whole word",
                       size_hint_weight=EXPAND_BOTH,
                       size_hint_align=FILL_HORIZ, state=WHOLE_WORD)
        wordCk.callback_changed_add(self.ckWord)
        wordCk.show()
        mainBox.pack_end(wordCk)

        # Dialog Buttons
        #    Horizontal Box for Dialog Buttons
        buttonBox = Box(self.findDialog, horizontal=True,
                        size_hint_weight=EXPAND_HORIZ,
                        size_hint_align=FILL_BOTH, padding=PADDING)
        buttonBox.size_hint_weight_set(EVAS_HINT_EXPAND, 0.0)
        buttonBox.show()
        mainBox.pack_end(buttonBox)
        #    Cancel Button
        cancelBtn = Button(self.findDialog, text="Cancel",
                           size_hint_weight=EXPAND_NONE)
        cancelBtn.callback_clicked_add(self.closeFind)
        cancelBtn.show()
        buttonBox.pack_end(cancelBtn)
        #    Ok Button
        okBtn = Button(self.findDialog, text=" Find ",
                       size_hint_weight=EXPAND_NONE)
        okBtn.callback_clicked_add(self.find)
        okBtn.show()
        buttonBox.pack_end(okBtn)

        # Ensure the min height
        self.findDialog.resize(300, 1)
        # self.findDialog.show()

    def find(self, obj):
        searchStr = self.sent.entry_get()
        if searchStr:
            print('Search string: {0}'.format(searchStr))
        else:
            print('Search string is Null')
        self.notImplemented()
        self.findDialog.hide()

    def closeFind(self, obj=False, trash=False):
        self.findDialog.hide()

    def launch(self, startingFile=False):
        self.findDialog.show()

    def ckCase(self, obj):
        global CASE_SENSITIVE
        CASE_SENSITIVE = not CASE_SENSITIVE
        print("CASE_SENSITIVE = {0}".format(CASE_SENSITIVE))

    def ckWord(self, obj):
        global WHOLE_WORD
        WHOLE_WORD = not WHOLE_WORD
        print("WHOLE_WORD = {0}".format(WHOLE_WORD))

    def notImplemented(self):
        # About popup
        self.popupAlert = Popup(self._canvas, size_hint_weight=EXPAND_BOTH)

        self.popupAlert.text = 'Shit: Not Implemented yet'
        bt = Button(self._canvas, text="Ok")
        bt.callback_clicked_add(self.niClose)
        self.popupAlert.part_content_set("button1", bt)
        self.popupAlert.show()

    def niClose(self, bt):
        self.popupAlert.delete()

if __name__ == "__main__":
    import argparse as ag

    # Parse Arguments
    #   More arguments will be added with increased functionality
    parser = ag.ArgumentParser(prog='ePad',
                               description=__description__,
                               epilog=__source__)
    parser.add_argument('filepath', nargs='?', metavar='filename',
                        help='path to file to open')
    parser.add_argument('--version', action='version', 
                        version='%(prog)s {0}'.format(__version__))
    results = parser.parse_args()
    ourFile = results.filepath

    # Start App
    elementary.init()
    GUI = Interface()
    if ourFile:
        if ourFile[0:7] == "file://":
            print(ourFile)
            ourFile = ourFile[7:-1]
        print(ourFile)
        GUI.launch(ourFile)
    else:
        GUI.launch()
    elementary.run()

    # Shutdown App
    elementary.shutdown()
