import csv
from datetime import datetime
import sys

from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from anki.importing import TextImporter
from anki.importing.noteimp import NoteImporter, ForeignNote

from flashcards_deluxe_importer.statistics import Statistics

import pprint # DELETE
pp = pprint.PrettyPrinter(indent = 2, stream=sys.stderr) # DELETE
fcd_filename = os.path.expanduser("~") + "/FCD-Miscellaneous.txt" # FIXME

class FlashcardsDeluxeImporter(NoteImporter):

    needDelimiter = True

    def __init__(self, *args):
        NoteImporter.__init__(self, *args)
        self.lines = None
        self.delimiter = "\t"
        self.tagsToAdd = ["FCD"]
        self.numFields = 4 # Note ID, Front, Back, Citation # FIXME

    def foreignNotes(self):
        pp.pprint("START") # DELETE
        self.open()

        # process all lines
        log = []
        ignored = 0

        # skip first 10 lines (does this vary or is it constant?)
        for _ in range(10):
            self.file.next()

        notes = []
        reader = csv.DictReader(self.file, delimiter="\t", doublequote=True)
        try:
            for row in reader:
                #row = {k: unicode(v, "utf-8") for k,v in row.iteritems()}
                front = row["Text 1"]
                back = row["Text 2"]
                hint = row["Text 3"]

                if hint and hint.strip():
                    front += "\n<div class='extra'>{0}</div>".format(hint)

                _appendIfNotEmpty(self.tagsToAdd, row["Category 1"])
                _appendIfNotEmpty(self.tagsToAdd, row["Category 2"])

                stats_string = row["Statistics 1"]
                stats = Statistics.parse(stats_string)

                note = self.noteFromFields(front, back, stats)
                notes.append(note)
                pp.pprint("BOTTOM INSIDE OF TRY") # DELETE
        except (csv.Error), e:
            pp.pprint("ERROR") # DELETE
            log.append(_("Aborted: %s") % str(e))

        pp.pprint("OUTSIDE TRY") # DELETE
        self.log = log
        self.ignored = ignored
        self.file.close()
        pp.pprint(notes)
        pp.pprint("END") # DELETE
        return notes

    def fields(self):
        "Number of fields."
        self.open()
        return self.numFields

    def noteFromFields(self, front, back, stats):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # FIXME
        note = ForeignNote()
        note.fields.extend([timestamp, front, back, ""])
        note.tags.extend(self.tagsToAdd)
        return note

def _appendIfNotEmpty(arr, item):
    if item and item.strip():
        arr.append(item)

def _variables(self):
    x = ["{}:{}".format(k,v) for k,v in sorted(self.__dict__.iteritems())]
    return "<{0} {1}>".format(type(self).__name__, " ".join(x))

# monkey patch to print out a more useful debugging string
Statistics.__repr__ = _variables
ForeignNote.__repr__ = _variables

def importFlashcardsDeluxe():
    # set current deck ("did" = deck ID)
    # FIXME: it's still using the default deck, why?
    did = mw.col.decks.id("TEST")
    mw.col.decks.select(did)

    # set note type for deck ("mid" = model aka note ID)
    m = mw.col.models.byName("Basic (and reversed card)")
    deck = mw.col.decks.get(did)
    deck["mid"] = m["id"]
    mw.col.decks.save(deck)

    # import into the collection
    fcd_file = open(fcd_filename, "r") # FIXME
    importer = FlashcardsDeluxeImporter(mw.col, fcd_file) # FIXME
    pp.pprint(importer)
    importer.initMapping()
    importer.run()

action = QAction("Import from Flashcards Deluxe", mw)
mw.connect(action, SIGNAL("triggered()"), importFlashcardsDeluxe)
mw.form.menuTools.addAction(action)
