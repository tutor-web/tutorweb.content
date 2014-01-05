import json

from AccessControl.SecurityInfo import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView


class BaseQuestionStruct(BrowserView):
    def asDict(self):
        """
        Return struct representing question as dict. An example is:
        {
            "text": '<div>The symbol for the set of all irrational numbers is... (b)</div>',
            "choices": [
                '<div>$\\mathbb{R} \\backslash \\mathbb{Q}$ (me)</div>',
                '<div>$\\mathbb{Q} \\backslash \\mathbb{R}$</div>',
                '<div>$\\mathbb{N} \\cap \\mathbb{Q}$ (me)</div>' ],
            "shuffle": [0, 1],
            "answer": window.btoa(JSON.stringify({
                "explanation": "<div>\nThe symbol for the set of all irrational numbers (b)\n</div>",
                "correct": [3],
            }))
        }
        """
        raise NotImplementedError

    def __call__(self):
        try:
            out = self.asDict()
            self.request.response.setStatus(200)
            self.request.response.setHeader("Content-type", "application/json")
            return json.dumps(out)
        except Exception, ex:
            self.request.response.setStatus(500)
            self.request.response.setHeader("Content-type", "application/json")
            return json.dumps(dict(
                error=ex.__class__.__name__,
                message=str(ex),
            ))


class LaTeXQuestionStruct(BaseQuestionStruct):
    security = ClassSecurityInfo()
    def portalTransforms(self):
        if getattr(self, '_pt', None) is None:
            self._pt = getToolByName(self.context, 'portal_transforms')
        return self._pt

    security.declarePrivate('updateStats')
    def updateStats(self, timesanswered, timescorrect):
        """Update question with new stats"""
        self.context.timesanswered = timesanswered
        self.context.timescorrect = timescorrect

    security.declarePrivate('allChoices')
    def allChoices(self):
        """List all the possible choices"""
        return (self.context.choices or []) + (self.context.finalchoices or [])

    def asDict(self):
        """Pull fields out into struct"""
        def renderRichField(f):
            if f is None:
                return ''
            if hasattr(f, 'output'):  # i.e. a RichTextField
                return f.output
            if hasattr(f, 'getImageSize'):  # i.e. a NamedBlobImage
                return '<img src="data:%s;base64,%s" width="%d" height="%d" />' % ((
                    f.contentType,
                    f.data.encode("base64").replace("\n", ""),
                ) + f.getImageSize())
            'data:image/png;base64,{0}'.format(data_uri)

        def renderTeX(f):
            return self.portalTransforms().convertTo(
                'text/html', f,
                mimetype='text/x-tex',
            ).getData()

        all_choices = self.allChoices()
        out = dict(
            title=self.context.title,
            text=renderRichField(self.context.text) + renderRichField(self.context.image),
            choices=[renderTeX(x['text']) for x in all_choices],
            shuffle=range(len(self.context.choices or [])),
            answer=dict(
                explanation=renderRichField(self.context.explanation),
                correct=[i for (i, x) in enumerate(all_choices) if x['correct']],
            ),
        )
        return out
