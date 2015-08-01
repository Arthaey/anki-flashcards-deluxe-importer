# vim: set fileencoding=utf-8 :

# TODO:
# - prompt user for exported FCD file
# - prompt user for which deck to use
# - prompt user for tag mapping
# - dynamically determine the number of fields for the model
# - check whether the Note Id addon is actually in use

import csv
from datetime import datetime
import random
import re
import sys

# Must happen before reload(sys).
import pprint # DELETE
pp = pprint.PrettyPrinter(indent = 2, stream=sys.stderr) # DELETE

# Required so that utf-8 characters can be used in the source code.
reload(sys)
sys.setdefaultencoding('utf8')

from anki.hooks import runHook, wrap
import anki.importing
from anki.importing import TextImporter
from anki.importing.anki1 import Anki1Importer
from anki.importing.anki2 import Anki2Importer
from anki.importing.apkg import AnkiPackageImporter
from anki.importing.mnemo import MnemosyneImporter
from anki.importing.noteimp import NoteImporter, ForeignNote
from anki.importing.pauker import PaukerImporter
from anki.importing.supermemo_xml import SupermemoXmlImporter
from anki.lang import _

from aqt import mw
from aqt.importing import ImportDialog
from aqt.qt import *
from aqt.utils import showInfo

from flashcards_deluxe_importer.statistics import Statistics

SECONDS_PER_DAY = 60*60*24

RENAME_TAGS = {
    "phrases": "español::frases",
    "sentences": "español::oraciones",
    "vocabulary": "español::vocabulario",
    "medical": "topics::medical",
}

class FlashcardsDeluxeImporter(TextImporter):

    needDelimiter = True
    allowHTML = True

    def __init__(self, *args):
        NoteImporter.__init__(self, *args)
        self.lines = None
        self.fileobj = None
        self.delimiter = "\t"
        self.tagsToAdd = ["FCD"]

        # specific to FlashcardsDeluxeImporter
        self.cardStats = {}
        self.startedAt = datetime.now()
        self.newNoteIds = []
        self.clozeNoteIds = []

    def importNotes(self, notes):
        NoteImporter.importNotes(self, notes)

        # Update any cloze cards.
        mm = mw.col.models
        basicReversedModel = mm.byName("Basic (and reversed card)")
        clozeModel = mm.byName("Cloze")
        fmap = {0: 0, 1: 2, 2: 1, 3: 3}
        cmap = {0: None, 1: 0}
        mm.change(basicReversedModel, self.clozeNoteIds, clozeModel, fmap, cmap)

    def foreignNotes(self):
        self.open()
        now = self.startedAt.strftime('%Y-%m-%d %H:%M:%S')

        # process all lines
        notes = []
        log = []
        ignored = 0
        lineNum = 0

        # skip leading lines that define the FCD deck
        i = 0
        while (self.data[i].startswith("*")):
            self.data.pop(0)

        reader = csv.DictReader(self.data, delimiter="\t", doublequote=True)
        try:
            for row in reader:
                lineNum += 1
                id = "Note #{0} imported at {1}".format(lineNum, now)

                row = {k: unicode(v, "utf-8") for k,v in row.iteritems()}
                front = row["Text 1"]
                back, isCloze = self._replaceClozes(row["Text 2"])
                hint = row["Text 3"]

                front = front.replace("\n", "<br>")
                back = back.replace("\n", "<br>")
                hint = hint.replace("\n", "<br>")

                if hint and hint.strip():
                    front += "\n<div class='extra'>{0}</div>".format(hint)

                tags = []
                self._addTag(tags, row["Category 1"])
                self._addTag(tags, row["Category 2"])

                statsString = row["Statistics 1"]
                stats = Statistics.parse(statsString)
                self.cardStats[id] = stats

                note = self.noteFromFields(id, front, back, tags)
                if stats.flagged:
                    note.tags.append("marked")
                if isCloze:
                    self.clozeNoteIds.append(id)

                notes.append(note)
        except (csv.Error), e:
            log.append(_("Aborted: %s") % str(e))

        self.log = log
        self.ignored = ignored
        self.fileobj.close()
        return notes

    def _addTag(self, tags, tag):
        if tag and tag.strip():
            tag = RENAME_TAGS.get(tag.lower(), tag.lower())
            tags.append(tag)

    # Returns the replaced text (if neeeded) and whether text was changed.
    def _replaceClozes(self, text):
        # horrible ugly hack but works "well enough" :(
        if "</u>" in text:
            return re.sub(r"<u.*?>(.+?)</u>", r"{{c1::\1}}", text), True
        elif "</b>" in text:
            return re.sub(r"<b.*?>(.+?)</b>", r"{{c1::\1}}", text), True
        else:
            return text, False

    def fields(self):
        "Number of fields."
        self.open()
        return 4 # Note ID, Front, Back, Citation # FIXME

    def noteFromFields(self, id, front, back, tags):
        note = ForeignNote()
        note.fields.extend([id, front, back, ""])
        note.tags.extend(tags + self.tagsToAdd)
        return note

    def newData(self, n):
        # [id, guid64(), self.model['id'],
        #  intTime(), self.col.usn(), self.col.tags.join(n.tags),
        #  n.fieldsStr, "", "", 0, ""]
        superData = NoteImporter.newData(self, n)

        id, guid, mid, time, usn, tags, fieldsStr, a, b, c, d = superData
        fields = fieldsStr.split("\x1f")
        noteId, front, back, citation = fields

        self.newNoteIds.append(id)

        # change to the actual note ID, now that it's assigned
        self.cardStats[id] = self.cardStats[noteId]
        del self.cardStats[noteId]
        if noteId in self.clozeNoteIds:
            ndx = self.clozeNoteIds.index(noteId)
            self.clozeNoteIds[ndx] = id
        fieldsStr = "\x1f".join([str(id), front, back, citation])

        return [id, guid, mid, time, usn, tags, fieldsStr, a, b, c, d]

    def updateCards(self):
        sched = mw.col.sched
        suspendIds = []

        for nid in self.newNoteIds:
            note = mw.col.getNote(nid)
            stats = self.cardStats[nid]

            # Use the same statistics for both directions.
            for card in note.cards():
                card.ivl = stats.intervalInDays
                card.due = stats.dueInDays(self.startedAt)
                card.factor = random.randint(1500,2500)
                card.reps = stats.reviewCount
                card.lapses = stats.lapses

                suspendIds += self._checkLeech(card, sched._lapseConf(card))

                # queue types: 0=new/cram, 1=lrn, 2=rev, 3=day lrn, -1=suspended, -2=buried
                # revlog types: 0=lrn, 1=rev, 2=relrn, 3=cram
                # FIXME: Cards aren't going to the new or learning queues. Why?
                if stats.pending: # new
                    card.type = 0
                    card.queue = 0
                    card.due = card.id
                elif stats.new: # learning
                    card.type = 1
                    card.queue = 1
                elif stats.active: # graduated
                    card.type = 2
                    card.queue = 2
                elif stats.excluded: # suspended
                    suspendIds += [card.id]

                card.flush()
                self._cards.append((nid, card.ord, card))

        NoteImporter.updateCards(self)
        sched.suspendCards(suspendIds)

    def _checkLeech(self, card, lapseConf):
        suspendIds = []
        lf = lapseConf["leechFails"]
        if card.lapses >= lf:
            note = card.note()
            note.addTag("leech")
            note.flush()
            if lapseConf["leechAction"] == 0:
                suspendIds.append(card.id)
            runHook("leech", card)
        return suspendIds

# TODO: append
anki.importing.Importers = (
    (_("Text separated by tabs or semicolons (*)"), TextImporter),
    (_("Packaged Anki Deck (*.apkg *.zip)"), AnkiPackageImporter),
    (_("Anki 1.2 Deck (*.anki)"), Anki1Importer),
    (_("Mnemosyne 2.0 Deck (*.db)"), MnemosyneImporter),
    (_("Supermemo XML export (*.xml)"), SupermemoXmlImporter),
    (_("Pauker 1.8 Lesson (*.pau.gz)"), PaukerImporter),
    (_("Flashcards Deluxe (*.txt)"), FlashcardsDeluxeImporter),
)

def setupOptionsForFlashcardsDeluxe(self):
    layout = self.findChild(QVBoxLayout, "toplayout")
    self.frm.tagsToAdd = QLineEdit()
    self.frm.tagsToAdd.setText(" ".join(self.importer.tagsToAdd))
    layout.addWidget(self.frm.tagsToAdd)

def acceptForFlashcardsDeluxe(self):
    self.importer.tagsToAdd = self.frm.tagsToAdd.text().split(" ")

ImportDialog.setupOptions = wrap(
    ImportDialog.setupOptions, setupOptionsForFlashcardsDeluxe, "after"
)
ImportDialog.accept = wrap(
    ImportDialog.accept, acceptForFlashcardsDeluxe, "before"
)
