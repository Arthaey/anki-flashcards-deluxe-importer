from datetime import datetime

class Statistics(object):
    def __init__(self, status, flagged, reviewCount, correctCount, streak,
            leitnerRounds, srsIntervalHours, lastReview, dueDate):
        self.status = int(status)
        self.flagged = (flagged == "1")
        self.reviewCount = int(reviewCount)
        self.correctCount = int(correctCount)
        self.streak = int(streak)
        self.leitnerRounds = int(leitnerRounds)
        self.srsIntervalHours = int(srsIntervalHours)
        self.lastReview = datetime.strptime(lastReview, "%Y-%m-%d %H:%M")
        self.dueDate = datetime.strptime(dueDate, "%Y-%m-%d %H:%M")

    def intervalInDays(self):
        return self.srsIntervalHours / 24

    def dueInDays(self, startedAt):
        return (self.dueDate - startedAt).days

    def lapses(self):
        return self.reviewCount - self.correctCount

    @classmethod
    def parse(cls, unparsedString):
        return cls(*unparsedString.split(","))
