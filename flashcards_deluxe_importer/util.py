from anki.importing.noteimp import ForeignNote
from statistics import Statistics

def appendIfNotEmpty(arr, text):
    if text and text.strip():
        arr.append(text.lower())

def variablesToStr(self):
    x = ["{}:{}".format(k,v) for k,v in sorted(self.__dict__.iteritems())]
    return "<{0} {1}>".format(type(self).__name__, " ".join(x))

# monkey patch to print out a more useful debugging string
Statistics.__repr__ = variablesToStr
ForeignNote.__repr__ = variablesToStr
