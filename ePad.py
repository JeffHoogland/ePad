#ePad - a simple text editor written in Elementary and Python
#
#By: Jeff Hoogland
#Started On: 03/16/2014

from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl import elementary
from efl.elementary.window import StandardWindow
from efl.elementary.box import Box
from efl.elementary.button import Button
from efl.elementary.entry import Entry
from efl.elementary.toolbar import Toolbar, ELM_TOOLBAR_SHRINK_MENU, \
    ELM_OBJECT_SELECT_MODE_NONE

EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.5
ALIGN_CENTER = 0.5, 0.5

class Interface(object):
    def __init__( self ):
        self.mainWindow = StandardWindow("ePad", "ePad - Untitled", autodel=True, size=(600, 400))
        self.mainWindow.callback_delete_request_add(self.closeChecks)

        self.mainBox = Box(self.mainWindow, size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.mainBox.show()

        self.mainTb = Toolbar(self.mainWindow, homogeneous=False, size_hint_weight=(0.0, 0.0), size_hint_align=(EVAS_HINT_FILL, 0.0))
        self.mainTb.item_append("document-new", "New", self.newPress)
        self.mainTb.item_append("document-open", "Open", self.openPress)
        self.mainTb.item_append("document-save", "Save", self.savePress)
        self.mainTb.item_append("document-save-as", "Save As", self.saveAsPress)

        self.mainEn = Entry(self.mainWindow, size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.mainEn.scrollable_set(True) # creates scrollbars rather than enlarge window
        self.mainEn.line_wrap_set(False) # does not allow line wrap (can be changed by user)
        self.mainEn.autosave_set(False) # set to false to reduce disk I/O
        self.mainEn.show()
        
        self.mainTb.show()

        self.mainBox.pack_end(self.mainTb)
        self.mainBox.pack_end(self.mainEn)

        self.mainWindow.resize_object_add(self.mainBox)

    def newPress( self, obj, it ):
        it.selected_set(False)

    def openPress( self, obj, it ):
        it.selected_set(False)

    def savePress( self, obj, it ):
        it.selected_set(False)

    def saveAsPress( self, obj, it ):
        it.selected_set(False)

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
