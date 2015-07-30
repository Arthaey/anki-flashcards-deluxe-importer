import csv
from datetime import datetime
import random
import sys

from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from anki.importing import TextImporter
from anki.importing.noteimp import NoteImporter, ForeignNote

from flashcards_deluxe_importer.statistics import Statistics

import pprint # DELETE
pp = pprint.PrettyPrinter(indent = 2, stream=sys.stderr) # DELETE
fcdFilename = os.path.expanduser("~") + "/FCD-Miscellaneous.txt" # FIXME

SECONDS_PER_DAY = 60*60*24

class FlashcardsDeluxeImporter(NoteImporter):

    needDelimiter = True

    def __init__(self, *args):
        NoteImporter.__init__(self, *args)
        self.lines = None
        self.delimiter = "\t"
        self.tagsToAdd = ["FCD"]
        self.numFields = 4 # Note ID, Front, Back, Citation # FIXME
        self.cardStats = {}
        self.newNoteIds = []
        self.startedAt = datetime.now()

    def foreignNotes(self):
        self.open()
        now = self.startedAt.strftime('%Y-%m-%d %H:%M:%S')

        # process all lines
        notes = []
        log = []
        ignored = 0
        lineNum = 0

        # skip first 10 lines (does this vary or is it constant?)
        for _ in range(10):
            self.file.next()

        reader = csv.DictReader(self.file, delimiter="\t", doublequote=True)
        try:
            for row in reader:
                lineNum += 1
                id = "Note #{0} imported at {1}".format(lineNum, now)

                #row = {k: unicode(v, "utf-8") for k,v in row.iteritems()}
                front = row["Text 1"]
                back = row["Text 2"]
                hint = row["Text 3"]

                if hint and hint.strip():
                    front += "\n<div class='extra'>{0}</div>".format(hint)

                _appendIfNotEmpty(self.tagsToAdd, row["Category 1"])
                _appendIfNotEmpty(self.tagsToAdd, row["Category 2"])

                statsString = row["Statistics 1"]
                stats = Statistics.parse(statsString)
                self.cardStats[id] = stats

                note = self.noteFromFields(id, front, back)
                notes.append(note)
        except (csv.Error), e:
            log.append(_("Aborted: %s") % str(e))

        self.log = log
        self.ignored = ignored
        self.file.close()
        return notes

    def fields(self):
        "Number of fields."
        self.open()
        return self.numFields

    def noteFromFields(self, id, front, back):
        note = ForeignNote()
        note.fields.extend([id, front, back, ""])
        note.tags.extend(self.tagsToAdd)
        return note

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
        # TODO: handle FCD card status
        # FIXME: Use ForeignCard instead?
        # Use the same statistics for both directions.
        for nid in self.newNoteIds:
            stats = self.cardStats[nid]
            for card in mw.col.getNote(nid).cards():
                card.ivl = stats.intervalInDays()
                card.due = stats.dueInDays(self.startedAt)
                card.factor = random.randint(1500,2500)
                card.reps = stats.reviewCount
                card.lapses = stats.lapses()
                self._cards.append((nid, card.ord, card))
        NoteImporter.updateCards(self)

def _appendIfNotEmpty(arr, text):
    if text and text.strip():
        arr.append(text.lower())

def _variables(self):
    x = ["{}:{}".format(k,v) for k,v in sorted(self.__dict__.iteritems())]
    return "<{0} {1}>".format(type(self).__name__, " ".join(x))

# monkey patch to print out a more useful debugging string
Statistics.__repr__ = _variables
ForeignNote.__repr__ = _variables

def importFlashcardsDeluxe():
    # set current deck ("did" = deck ID)
    # FIXME: it's still using the default deck, why?
    #did = mw.col.decks.id("TEST")
    #mw.col.decks.select(did)

    # set note type for deck ("mid" = model aka note ID)
    #m = mw.col.models.byName("Basic (and reversed card)")
    #deck = mw.col.decks.get(did)
    #deck["mid"] = m["id"]
    #mw.col.decks.save(deck)

    # import into the collection (with whichever is the current deck)
    fcdFile = open(fcdFilename, "r") # FIXME
    importer = FlashcardsDeluxeImporter(mw.col, fcdFile) # FIXME
    importer.initMapping()
    importer.run()
    showInfo("Finished importing {0} notes from {1}".format(
        len(importer.newNoteIds), fcdFilename))

action = QAction("Import from Flashcards Deluxe", mw)
mw.connect(action, SIGNAL("triggered()"), importFlashcardsDeluxe)
mw.form.menuTools.addAction(action)
