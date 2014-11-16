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
__version__ = "0.5.8-1"
__description__ = 'A simple text editor for the Enlightenment Desktop.'
__github__ = 'https://github.com/JeffHoogland/ePad'
__source__ = 'Source code and bug reports: {0}'.format(__github__)
PY_EFL = "https://git.enlightenment.org/bindings/python/python-efl.git/"


import errno
import sys
import os
import time
import urllib
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
    from efl.elementary.need import need_ethumb
    from efl.elementary.notify import Notify, ELM_NOTIFY_ALIGN_FILL
    from efl.elementary.separator import Separator
    from efl.elementary.image import Image
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
# User options
WORD_WRAP = True
SHOW_POS = True
NOTIFY_ROOT = True
SHOW_HIDDEN = False


def printErr(*objs):
    print(*objs, file=sys.stderr)


def errorPopup(window, errorMsg):
    errorPopup = Popup(window, size_hint_weight=EXPAND_BOTH)
    errorPopup.text = errorMsg
    errorPopup.callback_block_clicked_add(lambda obj: errorPopup.delete())
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
        self.about = aboutWin(self, self.mainWindow)
        self.about.hide()
        # Initialize Text entry box and line label
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

        self.fileSelector = Fileselector(self.mainWindow, is_save=False,
                                         expandable=False, folder_only=False,
                                         hidden_visible=SHOW_HIDDEN,
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

        self.mainEn.show()
        self.mainEn.focus_set(True)
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
        print("File Selected: '{0}'".format(file_selected))
        IsSave = fs.is_save_get()
        if file_selected:
            if IsSave:
                try:
                    newfile = open(file_selected, 'w')
                except IOError as err:
                    print("ERROR: {0}: '{1}'".format(err.strerror,
                                                     file_selected))
                    if err.errno == errno.EISDIR:
                        current_file = os.path.basename(file_selected)
                        errorMsg = ("<b>'%s'</b> is a folder."
                                    "<br><br>Operation failed !!!"
                                    % (current_file))
                        errorPopup(self.mainWindow, errorMsg)
                    elif err.errno == errno.EACCES:
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
                tmp_text = self.mainEn.entry_get()
                # FIXME: Why save twice?
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
                except RuntimeError, msg:
                    if os.path.isdir(file_selected):
                        print("ERROR: {0}: {1}".format(msg, file_selected))
                        current_file = os.path.basename(file_selected)
                        errorMsg = ("<b>'%s'</b> is a folder."
                                    "<br><br>Operation failed !!!"
                                    % (current_file))
                        errorPopup(self.mainWindow, errorMsg)
                        return
                    print("Empty file: {0}".format(file_selected))
                self.mainWindow.title_set("%s - ePad"
                                          % os.path.basename(file_selected))

                self.mainEn.focus_set(True)

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
        self.mainEn.focus_set(True)

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
            self.mainEn.file_save()
            self.mainWindow.title_set("%s - ePad"
                                      % os.path.basename(self.mainEn.file[0]))
            self.isSaved = True

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
                self.closeChecks(self.mainWindow)

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

    def launch(self, startingFile=False):
        if startingFile:
            if os.path.isdir(os.path.dirname(startingFile)):
                self.fileSelected(self.fileSelector, startingFile, True)
        self.mainWindow.show()
        # if startingFile is False this test fails with error
        try:
            if not os.path.isdir(os.path.dirname(startingFile)):
                print("Error: {0} is an Invalid Path".format(startingFile))
                errorMsg = ("<b>'%s'</b> is an Invalid path."
                            "<br><br>Open failed !!!" % (startingFile))
                errorPopup(self.mainWindow, errorMsg)
        except AttributeError:
            pass


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
        it.content.state = WORD_WRAP

        # ---------------------------

        self.item_append("dialog-information", "About",
                         lambda self, obj: self._parent.showAbout())

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


class aboutWin(Window):
    def __init__(self, parent, canvas):

        self._parent = parent
        self._canvas = canvas
        # Dialog Window Basics
        self.aboutDialog = Window("epad", ELM_WIN_DIALOG_BASIC)
        #
        self.aboutDialog.callback_delete_request_add(self.closeabout)
        #    Set Dialog background
        background = Background(self.aboutDialog, size_hint_weight=EXPAND_BOTH)
        self.aboutDialog.resize_object_add(background)
        background.show()
        #
        mainBox = Box(self.aboutDialog, size_hint_weight=EXPAND_BOTH,
                      size_hint_align=FILL_BOTH)
        self.aboutDialog.resize_object_add(mainBox)
        mainBox.show()
        #
        need_ethumb()
        icon = Icon(self.aboutDialog, thumb='True')
        icon.standard_set('accessories-text-editor')

        # Using gksudo or sudo fails to load Image here
        #   unless options specify using preserving their existing environment.
        #   may also fail to load other icons but does not raise an exception
        #   in that situation.
        # Works fine using eSudo as a gksudo alternative,
        #   other alternatives not tested
        try:
            aboutImage = Image(self.aboutDialog, no_scale=1,
                               size_hint_weight=EXPAND_BOTH,
                               size_hint_align=FILL_BOTH,
                               file=icon.file_get())
            aboutImage.aspect_fixed_set(0)

            mainBox.pack_end(aboutImage)
            aboutImage.show()
        except RuntimeError, msg:
            print("Warning: to run as root please use:\n"
                  "\t gksudo -k or sudo -E \n"
                  "Continuing with minor errors ...")

        labelBox = Box(self.aboutDialog, size_hint_weight=EXPAND_NONE)
        mainBox.pack_end(labelBox)
        labelBox.show()
        #    Entry to hold text
        titleStr = '<br>ePad version <em>{0}</em><br>'.format(__version__)
        aboutStr = ('<br>A simple text editor written in <br>'
                    'python and elementary<br>')
        aboutLbTitle = Label(self.aboutDialog, style='marker')
        aboutLbTitle.text = titleStr
        aboutLbTitle.show()

        labelBox.pack_end(aboutLbTitle)

        sep = Separator(self.aboutDialog, horizontal=True)
        labelBox.pack_end(sep)
        sep.show()

        aboutText = Label(self.aboutDialog)
        aboutText.text = aboutStr

        aboutText.show()
        labelBox.pack_end(aboutText)

        aboutCopyright = Label(self.aboutDialog)
        aboutCopyright.text = '<b>Copyright</b> © <i>2014 Bodhi Linux</i><br>'

        aboutCopyright.show()
        labelBox.pack_end(aboutCopyright)

        # Dialog Buttons
        #    Horizontal Box for Dialog Buttons
        buttonBox = Box(self.aboutDialog, horizontal=True,
                        size_hint_weight=EXPAND_HORIZ,
                        size_hint_align=FILL_BOTH, padding=PADDING)
        buttonBox.size_hint_weight_set(EVAS_HINT_EXPAND, 0.0)
        buttonBox.show()
        labelBox.pack_end(buttonBox)
        #    Credits Button
        creditsBtn = Button(self.aboutDialog, text="Credits ",
                            size_hint_weight=EXPAND_NONE)
        creditsBtn.callback_clicked_add(self.creditsPress)
        creditsBtn.show()
        buttonBox.pack_end(creditsBtn)
        #    Close Button
        okBtn = Button(self.aboutDialog, text=" Close ",
                       size_hint_weight=EXPAND_NONE)
        okBtn.callback_clicked_add(self.closeabout)
        okBtn.show()
        buttonBox.pack_end(okBtn)

        # Ensure the min height
        self.aboutDialog.resize(300, 100)

    def creditsPress(self, obj):
        # About popup
        self.popupAbout = Popup(self.aboutDialog,
                                size_hint_weight=EXPAND_BOTH)

        self.popupAbout.text = (
            "Jeff Hoogland &lt;<i>Jef91</i>&gt;<br><br>"
            "Robert Wiley &lt;<i>ylee</i>&gt;<br><br>"
            "Kai Huuhko &lt;<i>kuuko</i>&gt;<br>"
            )

        self.popupAbout.callback_block_clicked_add(self.cb_bnt_close)
        self.popupAbout.show()

    def cb_bnt_close(self, btn):
        self.popupAbout.delete()

    def closeabout(self, obj=False, trash=False):
        self.aboutDialog.hide()

    def launch(self, startingFile=False):
        center = self._parent.mainWindow.center_get()
        self.aboutDialog.center_set(center[0], center[1])
        self.aboutDialog.show()


if __name__ == "__main__":
    import argparse as ag

    # Parse Arguments
    #   More arguments will be added with increased functionality
    parser = ag.ArgumentParser(prog='ePad',
                               description=__description__,
                               epilog=__source__)
    parser.add_argument('filepath', nargs='?', metavar='filename',
                        help='path to file to open')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s {0}'.format(__version__))
    results = parser.parse_args()
    ourFile = results.filepath

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
        GUI.launch(ourFile)
    else:
        GUI.launch()
    elementary.run()

    # Shutdown App
    elementary.shutdown()
