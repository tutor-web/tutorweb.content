import json

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
    def portalTransforms(self):
        if getattr(self, '_pt', None) is None:
            self._pt = getToolByName(self.context, 'portal_transforms')
        return self._pt

    def asDict(self):
        """Pull fields out into struct"""
        def renderRichField(f):
            if f is None:
                return ''
            return f.output

        def renderTeX(f):
            return self.portalTransforms().convertTo(
                'text/html', f,
                mimetype='text/x-tex',
            ).getData()

        choices = self.context.choices or []
        out = dict(
            title=self.context.title,
            text=renderRichField(self.context.text),
            choices=[renderTeX(x['text']) for x in choices],
            fixed_order=[i for (i, x) in enumerate(choices) if not x['randomize']],
            random_order=[i for (i, x) in enumerate(choices) if x['randomize']],
            answer=dict(
                explanation=renderRichField(self.context.explanation),
                correct=[i for (i, x) in enumerate(choices) if x['correct']],
            ),
        )
        return out


class LaTeXQuestionTeXView(BrowserView):
    """Render question in TeX form"""
    def __call__(self):
        context = self.context
        self.request.response.setHeader('Content-Type', 'application/x-tex')
        self.request.response.setHeader('Content-disposition', "attachment; filename=%s.tex" % context.id)
        out = "%%ID %s\n" % context.id
        out += "%%title %s\n" % context.title
        out += "%format latex\n"
        #TODO: %image imagesource
        if context.text:
            out += context.text.raw + "\n\n"
        for (i, x) in enumerate(context.choices):
            out += "%s.%s) %s\n" % (chr(97 + i), 'true' if x['correct'] else 'false', x['text'].replace("\n", ""))
        if context.explanation:
            out += "\n%Explanation\n"
            out += context.explanation.raw + "\n"
        return out
