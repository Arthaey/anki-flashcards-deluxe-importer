from datetime import datetime

class Statistics(object):
    def __init__(self, status, flagged, reviewCount, correctCount, streak,
            leitnerRounds, srsIntervalHours, lastReview, dueDate):
        self.status = int(status)
        self.flagged = (flagged == 1)
        self.reviewCount = int(reviewCount)
        self.correctCount = int(correctCount)
        self.streak = int(streak)
        self.leitnerRounds = int(leitnerRounds)
        self.srsIntervalHours = int(srsIntervalHours)
        self.lastReview = datetime.strptime(lastReview, "%Y-%m-%d %H:%M")
        self.dueDate = datetime.strptime(dueDate, "%Y-%m-%d %H:%M")

    @classmethod
    def parse(cls, unparsed_string):
        return cls(*unparsed_string.split(","))
