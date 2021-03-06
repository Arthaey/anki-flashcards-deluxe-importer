# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/Arthaey/anki-flashcards-deluxe-importer
#
# Also available for Anki at https://ankiweb.net/shared/info/1356674785

from anki.hooks import wrap
from anki.lang import _

from aqt.importing import ImportDialog
from aqt.qt import *

def setupUi():
    ImportDialog.setupOptions = wrap(
        ImportDialog.setupOptions, setupOptionsForFlashcardsDeluxe, "after")

    ImportDialog.accept = wrap(
        ImportDialog.accept, acceptForFlashcardsDeluxe, "before")

def setupOptionsForFlashcardsDeluxe(self):
    self.frm.tagsToAdd = QLineEdit()
    self.frm.tagsToAdd.setText(" ".join(self.importer.tagsToAdd))

    tagLayout = QHBoxLayout()
    tagLayout.addWidget(QLabel("Tags"))
    tagLayout.addWidget(self.frm.tagsToAdd)

    topLayout = self.findChild(QVBoxLayout, "toplayout")
    topLayout.addLayout(tagLayout)

def acceptForFlashcardsDeluxe(self):
    self.importer.tagsToAdd = self.frm.tagsToAdd.text().split(" ")
