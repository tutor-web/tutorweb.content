from Products.Five.browser import BrowserView

class MockQuestionStatsView(BrowserView):
    def getStats(self):
        return [
            dict(id='qtd1', timesAnswered=99, timesCorrect=3),
            dict(id='qn2', timesAnswered=44, timesCorrect=4),
            dict(id='camel', timesAnswered=22, timesCorrect=1),
        ]
