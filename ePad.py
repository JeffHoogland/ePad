#ePad - a simple text editor written in Elementary and Python
#
#By: Jeff Hoogland
#Started On: 03/16/2014

import sys
import os
import time
from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl.elementary.object import EVAS_CALLBACK_KEY_UP, EVAS_CALLBACK_KEY_DOWN
from efl import elementary
from efl.elementary.window import StandardWindow
from efl.elementary.box import Box
from efl.elementary.button import Button
from efl.elementary.label import Label
from efl.elementary.icon import Icon
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
from efl.elementary.fileselector import Fileselector
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
        self.mainWindow = StandardWindow("ePad", "Untitled - ePad", size=(600, 400))
        self.mainWindow.callback_delete_request_add(self.closeChecks)
        self.mainWindow.elm_event_callback_add(self.eventsCb)

        icon = Icon(self.mainWindow)
        icon.size_hint_weight_set(EVAS_HINT_EXPAND, EVAS_HINT_EXPAND)
        icon.size_hint_align_set(EVAS_HINT_FILL, EVAS_HINT_FILL)
        icon.standard_set('accessories-text-editor') # assumes image icon is in local dir, may need to change later
        icon.show()
        self.mainWindow.icon_object_set(icon.object_get())

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
        self.mainEn.elm_event_callback_add(self.eventsCb)
        self.mainEn.markup_filter_append(self.textFilter)
        self.mainEn.show()
        
        self.mainTb.show()

        self.mainBox.pack_end(self.mainTb)
        self.mainBox.pack_end(self.mainEn)

        #Build our file selector for saving/loading files
        self.fileBox = Box(self.mainWindow, size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.fileBox.show()

        self.fileLabel = Label(self.mainWindow, size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_BOTH)
        self.fileLabel.text = ""
        self.fileLabel.show()

        self.fileSelector = Fileselector(self.mainWindow, is_save=False, expandable=False, folder_only=False,
                      path=os.getenv("HOME"), size_hint_weight=EXPAND_BOTH,
                      size_hint_align=FILL_BOTH)
        self.fileSelector.callback_done_add(self.fileSelected)
        #self.fileSelector.callback_selected_add(fs_cb_selected, win)
        #self.fileSelector.callback_directory_open_add(fs_cb_directory_open, win)
        self.fileSelector.show()

        self.fileBox.pack_end(self.fileLabel)
        self.fileBox.pack_end(self.fileSelector)

        # the flip object has the file selector on one side and the GUI on the other
        self.flip = Flip(self.mainWindow, size_hint_weight=EXPAND_BOTH,
                         size_hint_align=FILL_BOTH)
        self.flip.part_content_set("front", self.mainBox)
        self.flip.part_content_set("back", self.fileBox)
        self.mainWindow.resize_object_add(self.flip)
        self.flip.show()

        self.isSaved = True
        self.isNewFile = False
        self.confirmPopup = None

    def newPress( self, obj, it ):
        self.newFile()
        it.selected_set(False)

    def openPress( self, obj, it ):
        self.openFile()
        it.selected_set(False)

    def savePress( self, obj, it ):
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
            self.mainWindow.title_set("*%s - ePad"%self.mainEn.file_get()[0].split("/")[len(self.mainEn.file_get()[0].split("/"))-1])
        else:
            self.mainWindow.title_set("*Untitlted - ePad")
        self.isSaved = False

    def fileSelected( self, fs, file_selected, onStartup=False ):
        if not onStartup:
            self.flip.go(ELM_FLIP_INTERACTION_ROTATE)
        print file_selected
        IsSave = fs.is_save_get()
        if file_selected:
            if IsSave:
                newfile = open(file_selected,'w') # creates new file
                tmp_text = self.mainEn.entry_get()
                newfile.write(tmp_text)
                newfile.close()
                self.mainEn.file_set(file_selected, ELM_TEXT_FORMAT_PLAIN_UTF8)
                self.mainEn.entry_set(tmp_text)
                self.mainEn.file_save()
                self.mainWindow.title_set("%s - ePad" % file_selected.split("/")[len(file_selected.split("/"))-1])
                self.isSaved = True
                self.isNewFile = False
            else:
                self.mainEn.file_set(file_selected, ELM_TEXT_FORMAT_PLAIN_UTF8)
                self.mainWindow.title_set("%s - ePad" % file_selected.split("/")[len(file_selected.split("/"))-1])

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

    def newFile( self , obj=None, ignoreSave=False ):
        if self.isSaved == True or ignoreSave == True:
            trans = Transit()
            trans.object_add(self.mainEn)
            trans.auto_reverse = True

            trans.effect_wipe_add(
                ELM_TRANSIT_EFFECT_WIPE_TYPE_HIDE,
                ELM_TRANSIT_EFFECT_WIPE_DIR_RIGHT)

            trans.duration = 0.5
            trans.go()
            
            time.sleep(0.5)

            self.mainWindow.title_set("Untitlted - ePad")
            self.mainEn.delete()
            self.mainEn = Entry(self.mainWindow, size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
            self.mainEn.callback_changed_user_add(self.textEdited)
            self.mainEn.scrollable_set(True) # creates scrollbars rather than enlarge window
            self.mainEn.line_wrap_set(False) # does not allow line wrap (can be changed by user)
            self.mainEn.autosave_set(False) # set to false to reduce disk I/O
            self.mainEn.elm_event_callback_add(self.eventsCb)
            self.mainEn.show()
            
            self.mainBox.pack_end(self.mainEn)

            self.isNewFile = True
        elif self.confirmPopup == None:
            self.confirmSave(self.newFile)

    def openFile( self, obj=None, ignoreSave=False ):
        if self.isSaved == True or ignoreSave == True:
            self.fileSelector.is_save_set(False)
            self.fileLabel.text = "<b>Select a text file to open:</b>"
            self.flip.go(ELM_FLIP_ROTATE_YZ_CENTER_AXIS)
        elif self.confirmPopup == None:
            self.confirmSave(self.openFile)

    def confirmSave( self, ourCallback=None ):
        self.confirmPopup = Popup(self.mainWindow, size_hint_weight=EXPAND_BOTH)
        self.confirmPopup.part_text_set("title,text","File Unsaved")
        if self.mainEn.file_get()[0]:
            self.confirmPopup.text = "Save changes to '%s'?" % self.mainEn.file_get()[0].split("/")[len(self.mainEn.file_get()[0].split("/"))-1]
        else:
            self.confirmPopup.text = "Save changes to 'Untitlted'?"
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

    def saveAs( self ):
        self.fileSelector.is_save_set(True)
        self.fileLabel.text = "<b>Save new file to where:</b>"
        self.flip.go(ELM_FLIP_ROTATE_XZ_CENTER_AXIS)

    def saveFile( self, obj=False ):
        if self.mainEn.file_get()[0] == None or self.isNewFile:
            self.saveAs()
        else:
            self.mainEn.file_save()
            self.mainWindow.title_set("%s - ePad"%self.mainEn.file_get()[0].split("/")[len(self.mainEn.file_get()[0].split("/"))-1])
            self.isSaved = True

    def closeChecks( self, obj ):
        print self.isSaved
        if self.isSaved == False and self.confirmPopup == None:
            self.confirmSave(self.closeApp)
        else:
            self.closeApp()

    def closePopup( self, bt, confirmPopup ):
        self.confirmPopup.delete()
        self.confirmPopup = None

    def closeApp( self, obj=False, trash=False ):
        elementary.exit()

    def eventsCb( self, obj, src, event_type, event ):
        #print event_type
        #print event.key
        #print "Control Key Status: %s" %event.modifier_is_set("Control")
        #print "Shift Key Status: %s" %event.modifier_is_set("Shift")
        #print event.modifier_is_set("Alt")
        if event.modifier_is_set("Control"):
            if event.key.lower() == "n":
                self.newFile()
            elif event.key.lower() == "s" and event.modifier_is_set("Shift"):
                self.saveAs()
            elif event.key.lower() == "s":
                self.saveFile()
            elif event.key.lower() == "o":
                self.openFile()

    def textFilter( self, obj, theText, data ):
        #print theText

        #Block ctrl+hot keys
        if theText == "" or theText == "" or theText == "":
            return None
        else:
            return theText

    def launch( self, startingFile=False ):
        if startingFile:
            self.fileSelected(self.fileSelector, startingFile, True)
        self.mainWindow.show()

if __name__ == "__main__":
    elementary.init()

    GUI = Interface()
    if len(sys.argv) > 1:
        ourFile = str(sys.argv[1])
        if ourFile[0:7] == "file://":
            print ourFile
            ourFile = ourFile[7:len(ourFile)]
        print ourFile
        GUI.launch(ourFile)
    else:
        GUI.launch()

    elementary.run()
    elementary.shutdown()
