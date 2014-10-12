#!/usr/bin/python
# encoding: utf-8

# find.py a find dialog intended for use with ePad
#
# (c)Robert Wiley <ylee>
#
# This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function  # May as well bite the bullet


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
    from efl.elementary.entry import Entry, ELM_TEXT_FORMAT_PLAIN_UTF8
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
FILL_LEFT = EVAS_HINT_FILL, 0.0
ALIGN_CENTER = 0.5, 0.5
ALIGN_RIGHT = 1.0, 0.5
PADDING = 15, 0
WORD_WRAP = False
SHOW_POS = True
CASE_SENSITIVE = True
WHOLE_WORD = False


class findWin(Window):
    def __init__(self):

        # Dialog Window Basics
        self.findDialog = Window("find", ELM_WIN_DIALOG_BASIC)
        self.findDialog.callback_delete_request_add(self.closeFind)
        #    Set Window Icon
        #       Icons work  in ubuntu min everything compiled
        #       but not bodhi rc3
        icon = Icon(self.findDialog,
                    size_hint_weight=EXPAND_BOTH,
                    size_hint_align=FILL_BOTH)
        icon.standard_set('edit-find-replace')
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
        self.findDialog.show()

    def find(self, obj):
        print(self.sent.entry_get())
        elementary.exit()

    def closeFind(self, obj=False, trash=False):
        elementary.exit()

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

if __name__ == "__main__":
    elementary.init()
    GUI = findWin()
    GUI.launch()
    elementary.run()
    elementary.shutdown()
