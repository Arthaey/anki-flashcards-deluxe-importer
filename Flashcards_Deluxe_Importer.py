# vim: set fileencoding=utf-8 :

# TODO:
# - dynamically check how many leading lines to ignore
# - allow HTML
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

import pprint # DELETE
pp = pprint.PrettyPrinter(indent = 2, stream=sys.stderr) # DELETE

# Required so that utf-8 characters can be used in the source code.
reload(sys)
sys.setdefaultencoding('utf8')

from anki.hooks import runHook, wrap
import anki.importing
from anki.importing.noteimp import NoteImporter, ForeignNote
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from anki.importing.csvfile import TextImporter
from anki.importing.apkg import AnkiPackageImporter
from anki.importing.anki2 import Anki2Importer
from anki.importing.anki1 import Anki1Importer
from anki.importing.supermemo_xml import SupermemoXmlImporter
from anki.importing.mnemo import MnemosyneImporter
from anki.importing.pauker import PaukerImporter
from anki.lang import _

from flashcards_deluxe_importer.statistics import Statistics

fcdFilename = os.path.expanduser("~") + "/FCD-Miscellaneous.txt" # FIXME

SECONDS_PER_DAY = 60*60*24

RENAME_TAGS = {
    "phrases": "español::frases",
    "sentences": "español::oraciones",
    "vocabulary": "español::vocabulario",
    "medical": "topics::medical",
}

class FlashcardsDeluxeImporter(TextImporter):

    needDelimiter = True
    patterns = ("\t")

    def __init__(self, *args):
        NoteImporter.__init__(self, *args)
        self.lines = None
        self.fileobj = None
        self.delimiter = "\t"
        self.tagsToAdd = ["FCD"]
        #self.allowHTML = True # TODO?
        self.numFields = 6 # Note ID, Front, Back, Citation # FIXME

        # specific to FlashcardsDeluxeImporter
        self.cardStats = {}
        self.startedAt = datetime.now()
        self.newNoteIds = []
        self.clozeNoteIds = []
        self.deckId = mw.col.decks.id("TEST")

    def importNotes(self, notes):
        NoteImporter.importNotes(self, notes)

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

        # skip first 10 lines (does this vary or is it constant?)
#       for _ in range(10):
#           self.file.next()

        reader = csv.DictReader(self.data, delimiter=self.delimiter, doublequote=True)
        try:
            for row in reader:
                lineNum += 1
                id = "Note #{0} imported at {1}".format(lineNum, now)

#               row = {k: unicode(v, "utf-8") for k,v in row.iteritems()}
                pp.pprint(row) # DELETE
                front = row["Text 1"]
                back = row["Text 2"]
                hint = row["Text 3"]

                if hint and hint.strip():
                    front += "\n<div class='extra'>{0}</div>".format(hint)

                tags = []
                self.addTag(tags, row["Category 1"])
                self.addTag(tags, row["Category 2"])

                statsString = row["Statistics 1"]
                stats = Statistics.parse(statsString)
                self.cardStats[id] = stats

                note = self.noteFromFields(id, front, back, tags)
                if stats.flagged:
                    note.tags.append("marked")

                notes.append(note)
        except (csv.Error), e:
            log.append(_("Aborted: %s") % str(e))

        self.log = log
        self.ignored = ignored
        self.fileobj.close()
        return notes

    def addTag(self, tags, tag):
        if tag and tag.strip():
            tag = RENAME_TAGS.get(tag.lower(), tag.lower())
            tags.append(tag)

    def fields(self):
        "Number of fields."
        self.open()
        return self.numFields

    def noteFromFields(self, id, front, back, tags):
        note = ForeignNote()
        note.fields.extend([id, front, back, ""])
        note.tags.extend(tags + self.tagsToAdd)
        return note

    def initMapping(self):
        pp.pprint("SELF.MODEL") # DELETE
        pp.pprint(self.model) # DELETE
        fields = [""]*len(self.model['flds']) # DELETE
        pp.pprint("FIELDS") # DELETE
        pp.pprint(fields) # DELETE
        pp.pprint("SELF.FIELDS()") # DELETE
        pp.pprint(self.fields()) # DELETE
        NoteImporter.initMapping(self)
        pp.pprint("SELF.MAPPING") # DELETE
        pp.pprint(self.mapping) # DELETE

    def newData(self, n):
        # [id, guid64(), self.model['id'],
        #  intTime(), self.col.usn(), self.col.tags.join(n.tags),
        #  n.fieldsStr, "", "", 0, ""]
        superData = NoteImporter.newData(self, n)

        id, guid, mid, time, usn, tags, fieldsStr, a, b, c, d = superData
        fields = fieldsStr.split("\x1f")
        noteId, front, back, citation = fields

        self.cardStats[id] = self.cardStats[noteId]
        del self.cardStats[noteId]

        self.newNoteIds.append(id)
        noteId = str(id) # change to the actual note ID, now that it's assigned
        fieldsStr = "\x1f".join([noteId, front, back, citation])

        return [id, guid, mid, time, usn, tags, fieldsStr, a, b, c, d]

    def updateCards(self):
        sched = mw.col.sched
        suspendIds = []

        for nid in self.newNoteIds:
            note = mw.col.getNote(nid)
            note.did = self.deckId
            stats = self.cardStats[nid]

            # horrible ugly hack but works "well enough" :(
            back = note["Back"]
            if "&lt;/u&gt;" in note["Back"]:
                self.clozeNoteIds.append(nid)
                note["Back"] = re.sub(r"&lt;u.*?&gt;(.+?)&lt;/u&gt;", r"{{c1::\1}}", back)
                note.flush()
            elif "&lt;/b&gt;" in note["Back"]:
                self.clozeNoteIds.append(nid)
                note["Back"] = re.sub(r"&lt;b.*?&gt;(.+?)&lt;/b&gt;", r"{{c1::\1}}", back)
                note.flush()

            # Use the same statistics for both directions.
            for card in note.cards():
                card.ivl = stats.intervalInDays
                card.due = stats.dueInDays(self.startedAt)
                card.factor = random.randint(1500,2500)
                card.reps = stats.reviewCount
                card.lapses = stats.lapses
                card.did = self.deckId

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

def importFlashcardsDeluxe():
    # import into the collection (with whichever is the current deck)
    fcdFile = open(fcdFilename, "r")
    importer = FlashcardsDeluxeImporter(mw.col, fcdFile)
    importer.initMapping()
    importer.run()
    showInfo("Finished importing {0} notes from {1}".format(
        len(importer.newNoteIds), fcdFilename))

action = QAction("Import from Flashcards Deluxe", mw)
mw.connect(action, SIGNAL("triggered()"), importFlashcardsDeluxe)
mw.form.menuTools.addAction(action)

anki.importing.Importers = (
    (_("Text separated by tabs or semicolons (*)"), TextImporter),
    (_("Packaged Anki Deck (*.apkg *.zip)"), AnkiPackageImporter),
    (_("Anki 1.2 Deck (*.anki)"), Anki1Importer),
    (_("Mnemosyne 2.0 Deck (*.db)"), MnemosyneImporter),
    (_("Supermemo XML export (*.xml)"), SupermemoXmlImporter),
    (_("Pauker 1.8 Lesson (*.pau.gz)"), PaukerImporter),
    (_("Flashcards Deluxe (*.txt)"), FlashcardsDeluxeImporter),
    )
