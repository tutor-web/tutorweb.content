from Products.Five.browser import BrowserView

class MockQuestionStatsView(BrowserView):
    def getStats(self):
        return []
