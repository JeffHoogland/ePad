#ePad - a simple text editor written in Elementary and Python
#
#By: Jeff Hoogland
#Started On: 03/16/2014

import sys
import os
from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl import elementary
from efl.elementary.window import StandardWindow
from efl.elementary.box import Box
from efl.elementary.button import Button
from efl.elementary.entry import Entry, ELM_TEXT_FORMAT_PLAIN_UTF8
from efl.elementary.popup import Popup, ELM_WRAP_CHAR
from efl.elementary.toolbar import Toolbar, ELM_TOOLBAR_SHRINK_MENU, \
    ELM_OBJECT_SELECT_MODE_NONE
from efl.elementary.flip import Flip, ELM_FLIP_ROTATE_X_CENTER_AXIS, \
    ELM_FLIP_ROTATE_Y_CENTER_AXIS, ELM_FLIP_ROTATE_XZ_CENTER_AXIS, \
    ELM_FLIP_ROTATE_YZ_CENTER_AXIS, ELM_FLIP_CUBE_LEFT, ELM_FLIP_CUBE_RIGHT, \
    ELM_FLIP_CUBE_UP, ELM_FLIP_CUBE_DOWN, ELM_FLIP_PAGE_LEFT, \
    ELM_FLIP_PAGE_RIGHT, ELM_FLIP_PAGE_UP, ELM_FLIP_PAGE_DOWN, \
    ELM_FLIP_DIRECTION_UP, ELM_FLIP_DIRECTION_DOWN, \
    ELM_FLIP_DIRECTION_LEFT, ELM_FLIP_DIRECTION_RIGHT, \
    ELM_FLIP_INTERACTION_NONE, ELM_FLIP_INTERACTION_ROTATE, \
    ELM_FLIP_INTERACTION_CUBE, ELM_FLIP_INTERACTION_PAGE
from efl.elementary.fileselector import Fileselector, \
    ELM_FILESELECTOR_SORT_LAST, ELM_FILESELECTOR_LIST, ELM_FILESELECTOR_GRID, \
    ELM_FILESELECTOR_SORT_BY_FILENAME_ASC, ELM_FILESELECTOR_SORT_BY_FILENAME_DESC, \
    ELM_FILESELECTOR_SORT_BY_TYPE_ASC, ELM_FILESELECTOR_SORT_BY_TYPE_DESC, \
    ELM_FILESELECTOR_SORT_BY_SIZE_ASC, ELM_FILESELECTOR_SORT_BY_SIZE_DESC, \
    ELM_FILESELECTOR_SORT_BY_MODIFIED_ASC, ELM_FILESELECTOR_SORT_BY_MODIFIED_DESC
from efl.elementary.transit import Transit, ELM_TRANSIT_EFFECT_WIPE_TYPE_HIDE, \
    ELM_TRANSIT_EFFECT_WIPE_DIR_RIGHT, ELM_TRANSIT_EFFECT_FLIP_AXIS_X, \
    ELM_TRANSIT_EFFECT_FLIP_AXIS_Y, ELM_TRANSIT_TWEEN_MODE_ACCELERATE, \
    ELM_TRANSIT_TWEEN_MODE_DECELERATE, TransitCustomEffect


EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.5
ALIGN_CENTER = 0.5, 0.5

class Interface(object):
    def __init__( self ):
        self.mainWindow = StandardWindow("ePad", "Untitled - ePad", autodel=True, size=(600, 400))
        self.mainWindow.callback_delete_request_add(self.closeChecks)

        self.mainBox = Box(self.mainWindow, size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.mainBox.show()

        self.mainTb = Toolbar(self.mainWindow, homogeneous=False, size_hint_weight=(0.0, 0.0), size_hint_align=(EVAS_HINT_FILL, 0.0))
        self.mainTb.item_append("document-new", "New", self.newPress)
        self.mainTb.item_append("document-open", "Open", self.openPress)
        self.mainTb.item_append("document-save", "Save", self.savePress)
        self.mainTb.item_append("document-save-as", "Save As", self.saveAsPress)
        #self.mainTb.item_append("settings", "Options", self.optionsPress)
        self.mainTb.item_append("dialog-information", "About", self.aboutPress)

        self.mainEn = Entry(self.mainWindow, size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.mainEn.callback_changed_user_add(self.textEdited)
        self.mainEn.scrollable_set(True) # creates scrollbars rather than enlarge window
        self.mainEn.line_wrap_set(False) # does not allow line wrap (can be changed by user)
        self.mainEn.autosave_set(False) # set to false to reduce disk I/O
        self.mainEn.show()
        
        self.mainTb.show()

        self.mainBox.pack_end(self.mainTb)
        self.mainBox.pack_end(self.mainEn)

        #Build our file selector for saving/loading files
        self.fileSelector = Fileselector(self.mainWindow, is_save=True, expandable=False, folder_only=False,
                      path=os.getenv("HOME"), size_hint_weight=EXPAND_BOTH,
                      size_hint_align=FILL_BOTH)
        self.fileSelector.callback_done_add(self.fileSelected)
        #self.fileSelector.callback_selected_add(fs_cb_selected, win)
        #self.fileSelector.callback_directory_open_add(fs_cb_directory_open, win)
        self.fileSelector.show()

        # the flip object has the file selector on one side and the GUI on the other
        self.flip = Flip(self.mainWindow, size_hint_weight=EXPAND_BOTH,
                         size_hint_align=FILL_BOTH)
        self.flip.part_content_set("front", self.mainBox)
        self.flip.part_content_set("back", self.fileSelector)
        self.mainWindow.resize_object_add(self.flip)
        self.flip.show()

        self.isSaved = False
        self.isNewFile = False

    def newPress( self, obj, it ):
        self.newFile()
        it.selected_set(False)

    def openPress( self, obj, it ):
        self.openFile()
        it.selected_set(False)

    def savePress( self, obj, it ):
        if self.mainEn.file_get()[0] == None or self.isNewFile:
            self.saveAs()
        else:
            self.saveFile()
        it.selected_set(False)

    def saveAsPress( self, obj, it ):
        self.saveAs()
        it.selected_set(False)

    def optionsPress( self, obj, it ):
        it.selected_set(False)

    def textEdited( self, obj ):
        ourFile = self.mainEn.file_get()[0]
        if ourFile and not self.isNewFile:
            self.mainWindow.title_set("*%s - ePad"%ourFile)
        else:
            self.mainWindow.title_set("*Untitlted - ePad")
        self.isSaved = False

    def fileSelected( self, fs, file_selected ):
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)
        print file_selected
        IsSave = fs.is_save_get()
        if IsSave:
            open(file_selected,'w').close() # creates new file
            tmp_text = self.mainEn.entry_get()
            self.mainEn.file_set(file_selected, ELM_TEXT_FORMAT_PLAIN_UTF8)
            self.mainEn.entry_set(tmp_text)
            self.mainEn.file_save()
            self.mainWindow.title_set("%s - ePad" % file_selected)
            self.isSaved = True
            self.isNewFile = False
        else:
            self.mainEn.file_set(file_selected, ELM_TEXT_FORMAT_PLAIN_UTF8)
            self.mainWindow.title_set("%s - ePad" % file_selected)

    def aboutPress( self, obj, it ):
        #About popup
        self.popupAbout = Popup(self.mainWindow, size_hint_weight=EXPAND_BOTH)
        self.popupAbout.text = "ePad - A simple text editor written in python and elementary<br><br> " \
                     "By: Jeff Hoogland"
        bt = Button(self.mainWindow, text="Done")
        bt.callback_clicked_add(self.aboutClose)
        self.popupAbout.part_content_set("button1", bt)
        self.popupAbout.show()
        it.selected_set(False)

    def aboutClose( self, bt ):
        self.popupAbout.delete()

    def newFile( self ):
        trans = Transit()
        trans.object_add(self.mainEn)
        trans.auto_reverse = True

        trans.effect_wipe_add(
            ELM_TRANSIT_EFFECT_WIPE_TYPE_HIDE,
            ELM_TRANSIT_EFFECT_WIPE_DIR_RIGHT)

        trans.duration = 0.5
        trans.go()

        self.mainWindow.title_set("Untitlted - ePad")
        self.mainEn.entry_set("")
        self.isNewFile = True

    def openFile( self ):
        self.fileSelector.is_save_set(False)
        self.flip.go(ELM_FLIP_ROTATE_YZ_CENTER_AXIS)

    def saveAs( self ):
        self.fileSelector.is_save_set(True)
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)

    def saveFile( self ):
        self.mainEn.file_save()
        self.mainWindow.title_set("%s - ePad"%self.mainEn.file_get()[0])
        self.isSaved = True

    def closeChecks( self, obj ):
        elementary.exit()

    def launch( self ):
        self.mainWindow.show()

if __name__ == "__main__":
    elementary.init()

    GUI = Interface()
    GUI.launch()

    elementary.run()
    elementary.shutdown()
