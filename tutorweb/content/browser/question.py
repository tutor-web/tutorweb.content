import json

from AccessControl.SecurityInfo import ClassSecurityInfo
from zope.publisher.interfaces import NotFound

from plone.memoize import ram
from Products.CMFCore.utils import getToolByName

from ..datauri import encodeDataUri

from .jsonbrowserview import JSONBrowserView


class BaseQuestionStruct(JSONBrowserView):
    security = ClassSecurityInfo()

    security.declarePrivate('asDict')
    def asDict(self, data=None):
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

    security.declarePrivate('convertTo')
    def convertTo(self, *args, **kwargs):
        if getattr(self, '_pt', None) is None:
            self._pt = getToolByName(self.context, 'portal_transforms')
        return self._pt.convertTo(*args, **kwargs)

    security.declarePrivate('render')
    def render(self, f, type = None):
        if f is None:
            return ''
        if type == 'TeX':
            return self.convertTo(
                'text/html',
                f.encode('utf-8'),
                mimetype='text/x-tex',
                encoding='utf-8',
            ).getData().decode('utf-8')
        if hasattr(f, 'output'):  # i.e. a RichTextField
            return f.output
        if hasattr(f, 'getImageSize'):  # i.e. a NamedBlobImage
            return '<img src="%s" width="%d" height="%d" />' % ((
                encodeDataUri(f.data, f.contentType),
            ) + f.getImageSize())
        raise ValueError("Cannot interpret %s" % f)


class LaTeXQuestionStruct(BaseQuestionStruct):
    security = ClassSecurityInfo()

    security.declarePrivate('allChoices')
    def allChoices(self):
        """List all the possible choices"""
        return (self.context.choices or []) + (self.context.finalchoices or [])

    security.declarePrivate('asDict')
    def asDict(self, data=None):
        """Pull fields out into struct"""
        all_choices = self.allChoices()
        out = dict(
            _type='multichoice',
            title=self.context.title,
            text=self.render(self.context.text) +
                 self.render(self.context.image),
            choices=[self.render(x['text'], 'TeX') for x in all_choices],
            shuffle=range(len(self.context.choices or [])),
            answer=dict(
                explanation=self.render(self.context.explanation),
                correct=[i for (i, x) in enumerate(all_choices) if x['correct']],
            ),
        )
        return out


class QuestionTemplateStruct(BaseQuestionStruct):
    security = ClassSecurityInfo()

    security.declarePrivate('asDict')
    def asDict(self, data=None):
        """Pull fields out into struct"""
        out = dict(
            _type='template',
            title=self.context.title,
            hints=self.render(self.context.hints),
            example_text=getattr(self.context.example_text, 'raw', ''),
            example_choices=[x['text'] for x in self.context.example_choices or []],
            example_explanation=getattr(self.context.example_explanation, 'raw', ''),
        )
        return out


def _allQuestionsDict_cachekey(method, self):
    """Cache key of path and last modified date"""
    return (
        '/'.join(self.context.getPhysicalPath()),
        self.context.modified(),
    )


class QuestionPackStruct(BaseQuestionStruct):
    security = ClassSecurityInfo()

    @ram.cache(_allQuestionsDict_cachekey)
    def allQuestionsDict(self):
        """Convert all questions to intermediate JSON"""
        from tutorweb.content.transmogrifier.latex import readQuestions
        out = dict()

        with self.context.questionfile.open() as fh:
            for qn in readQuestions(fh):
                out[qn['id']] = qn
        return out

    security.declarePrivate('asDict')
    def asDict(self, data={}):
        """Render Selected question"""
        if isinstance(data, dict) and 'question_id' in data:
            qnId = data['question_id']
            if isinstance(qnId, list):
                # Bodge for querystring data coming in
                qnId = qnId[0]
        elif 'question_id' in self.request:
            qnId = self.request.get('question_id', None)
        else:
            raise NotFound(self, "Missing question_id", self.request)

        qn = self.allQuestionsDict().get(qnId, None)
        if not qn:
            raise NotFound(self, qnId, self.request)

        all_choices = qn.get('choices', []) + qn.get('finalchoices', [])
        text = self.render(qn.get('text', dict(data=''))['data'], 'TeX')
        if qn.get('image', None):
            text += '<img src="%s" />' % encodeDataUri(
                qn['image']['data'],
                qn['image']['contenttype'],
            )
        out = dict(
            _type='multichoice',
            title=qn.get('title', ''),
            text=text,
            choices=[self.render(x['text'], 'TeX') for x in all_choices],
            shuffle=range(len(qn.get('choices', []))),
            answer=dict(
                explanation=self.render(qn.get('explanation', dict(data=''))['data'], 'TeX'),
                correct=[i for (i, x) in enumerate(all_choices) if x['correct']],
            ),
        )
        return out
