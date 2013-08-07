import cgi
import json

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
            "fixed_order": [0],
            "random_order": [1, 2],
            "answer": window.btoa(JSON.stringify({
                "explanation": "<div>\nThe symbol for the set of all irrational numbers (b)\n</div>",
                "correct": [0, 2]
            }))
        }        
        """
        raise NotImplementedError

    def __call__(self):
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(self.asDict())

class StaticQuestionStruct(BaseQuestionStruct):
    def asDict(self):
        """Pull fields out into struct"""
        def renderRichField(f):
            if f is None:
                return ''
            return f.output

        choices = self.context.choices
        out = dict(
            text=renderRichField(self.context.text),
            choices=['<div>%s</div>' % cgi.escape(x['text']) for x in choices],
            fixed_order=[i for (i, x) in enumerate(choices) if not x['randomize']],
            random_order=[i for (i, x) in enumerate(choices) if x['randomize']],
            answer=dict(
                explanation=renderRichField(self.context.explanation),
                correct=[i for (i, x) in enumerate(choices) if x['correct']],
            ),
        )
        return out
