from datetime import datetime

class Statistics(object):
    def __init__(self, status, flagged, reviewCount, correctCount, streak,
            leitnerRounds, srsIntervalHours, lastReview, dueDate):
        self.status           = int(status)
        self.flagged          = (1 == int(flagged))
        self.reviewCount      = int(reviewCount)
        self.correctCount     = int(correctCount)
        self.streak           = int(streak)
        self.leitnerRounds    = int(leitnerRounds)
        self.srsIntervalHours = int(srsIntervalHours)
        self.lastReview = datetime.strptime(lastReview, "%Y-%m-%d %H:%M")
        self.dueDate    = datetime.strptime(dueDate, "%Y-%m-%d %H:%M")

        # derived info
        # FCD Status: PENDING=0, NEW=1, ACTIVE=2, EXCLUDE=3
        self.pending  = (0 == self.status)
        self.new      = (1 == self.status)
        self.active   = (2 == self.status)
        self.excluded = (3 == self.status)

        self.intervalInDays = self.srsIntervalHours / 24
        self.lapses = self.reviewCount - self.correctCount

    def dueInDays(self, startedAt):
        return (self.dueDate - startedAt).days

    @classmethod
    def parse(cls, unparsedString):
        return cls(*unparsedString.split(","))
