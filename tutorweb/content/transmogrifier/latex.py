import urllib
import urllib2
import re

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import openFileReference
from collective.transmogrifier.utils import defaultMatcher

from ..datauri import encodeDataUri, decodeDataUri


class LatexSourceSection(object):
    """
    Read a LaTeX file containing tutorweb questions
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier

        self.key = defaultMatcher(options, 'key', name)
        self.filename = options.get('filename')
        if self.filename:
            self.filename = options['filename'] = self.filename

    def __iter__(self):
        file = openFileReference(self.transmogrifier, self.filename)
        if file is None:
            raise ValueError("%s not found" % self.filename)

        for qn in readQuestions(file):
            yield qn


def readQuestions(file):
    def finalise(item):
        # Convert rich text fields into dicts
        for field in ['text', 'explanation']:
            if field in item:
                item[field] = dict(
                    contenttype=item['_defmime'],
                    data=item[field],
                    encoding='utf-8',
                )

        # Unless otherwise marked, last item is correct
        if 'choices' in item:
            # Has to be at least one correct answer, choose first if none marked
            if len([i for i in item['choices'] + item.get('finalchoices', []) if i['correct']]) == 0:
                item['choices'][0]['correct'] = True

        # Set portal type for content
        if '_type' not in item:
            item['_type'] = 'tw_latexquestion'

        # Tidy up and return
        del item['_defmime']
        del item['_deffield']
        return item

    initialitem = dict(
        processLatex=True,
        _defmime='text/x-tex',
        _deffield='text',
        _type='tw_latexquestion',
    )
    item = initialitem.copy()
    for line in (l.strip().decode('utf8') for l in file):
        if line == '%===':
            # Separator, return this and move on to next item
            if item.get('id', None):
                yield finalise(item)
            item = initialitem.copy()

        elif re.search(r'%ID\s+', line):
            item['id'] = line.replace('%ID', '', 1).strip()

        elif re.search(r'%title\s+', line):
            item['title'] = line.replace('%title', '', 1).strip()

        elif re.search(r'%image\s+data:', line):
            data = decodeDataUri(line.replace('%image', '', 1).strip())
            item['image'] = dict(
                filename=data.get('extra', {}).get('filename', "%s-image" % item.get('id', None)),
                data=data['data'],
                contenttype=data['mimeType'],
            )

        elif re.search(r'%image\s+', line):
            response = urllib2.urlopen(line.replace('%image', '', 1).strip())
            item['image'] = dict(
                filename=urllib.quote_plus(response.geturl()),
                data=response.read(),
                contenttype=response.headers['content-type'],
            )

        elif line.startswith('%Explanation'):
            # Any un %'ed lines are now part of the explanation
            initExplanation = line.replace('%Explanation', '', 1).strip()
            item['_deffield'] = 'explanation'
            if initExplanation:
                item[item['_deffield']] = initExplanation

        elif re.search(r'%format\s+', line):
            # Format tag: Don't understand anything other than LaTeX
            if re.search(r'%format\s+latex', line):
                # Already set up by default
                pass
            elif re.search(r'%format\s+(txt|text)', line):
                item['processLatex'] = False
                item['_defmime'] = 'text/x-web-intelligent'
            else:
                raise ValueError('Unknown format %s' % line)

        elif re.search(r'^[a-z]+(\.true|\.false)?\)', line):
            # a) or a.true) choices
            # Choose which field it should go in
            if re.search(r'^d.(true|false)\)', line):
                # "d.true|d.false" is a special case, apparently
                item['_deffield']='finalchoices'
            elif re.search(r'^x[a-z]', line):
                # xa) .. xz) goes at the end
                item['_deffield']='finalchoices'
            else:
                item['_deffield']='choices'

            # Add to field
            if item['_deffield'] not in item:
                item[item['_deffield']] = []
            item[item['_deffield']].append(dict(
                text=re.sub(r'^.*?\)\s*', '', line),
                #NB: if in the form a), then the following is still false.
                # Will mark the first answer as correct in finalise()
                correct=(re.search(r'^[a-z]+\.true\)', line) is not None),
            ))

        elif re.search(r'%n\s+', line):
            item['timesanswered'] = int(line.replace('%n', '', 1).strip())
        elif re.search(r'%r\s+', line):
            item['timescorrect'] = int(line.replace('%r', '', 1).strip())

        else:
            if item['_deffield'] == 'choices':
                # Append to last choice
                item['choices'][-1]['text'] = (item['choices'][-1]['text']
                                              + "\n" + line).strip()
            elif item['_deffield'] == 'finalchoices':
                # Append to last choice
                item['finalchoices'][-1]['text'] = (item['finalchoices'][-1]['text']
                                                 + "\n" + line).strip()
            else:
                # Line that needs appending to
                if item['_deffield'] not in item:
                    item[item['_deffield']] = ""
                item[item['_deffield']] = (item[item['_deffield']] + "\n" + line).lstrip()

    if item.get('id', None):
        # Return final item too
        yield finalise(item)


def objectsToTex(gen, stats=dict()):
    """Convert a generator of plone objects into a string of TeX"""
    out = ""
    for obj in gen:
        if out:
            out += "\n%===\n"

        out += dict(
            tw_latexquestion=latexQuestionToTex,
            tw_questiontemplate=questionTemplateToTex,
        )[obj.portal_type](obj, stats.get(obj.id, None))

    return out


def latexQuestionToTex(obj, statsObj):
    out = ""
    out += "%%ID %s\n" % obj.id
    out += "%%title %s\n" % obj.title
    out += "%format latex\n"
    if obj.image is not None:
        out += "%%image %s\n" % encodeDataUri(
            obj.image.data,
            mimeType=obj.image.contentType,
            extra=dict(filename=obj.image.filename.encode('utf-8')) if obj.image.filename else dict(),
        )
    if obj.text:
        out += obj.text.raw + "\n\n"
    for (i, x) in enumerate(obj.choices or []):
        out += "%s%s) %s\n" % (
            chr(97 + i),
            '.true' if x['correct'] else '',
            x['text'].replace("\n", "")
        )
    for (i, x) in enumerate(obj.finalchoices or []):
        out += "x%s%s) %s\n" % (
            chr(97 + i),
            '.true' if x['correct'] else '',
            x['text'].replace("\n", "")
        )
    if obj.explanation:
        out += "\n%Explanation\n"
        out += obj.explanation.raw + "\n"

    if statsObj:
        out += "%%r %d\n" % statsObj['timesCorrect']
        out += "%%n %d\n" % statsObj['timesAnswered']
    else:
        if obj.timescorrect:
            out += "%%r %d\n" % obj.timescorrect
        if obj.timesanswered:
            out += "%%n %d\n" % obj.timesanswered
    return out

def questionTemplateToTex(obj, statsObj):
    out = ""
    out += "%%ID %s\n" % obj.id
    out += "%%title %s\n" % obj.title
    out += "%%format %s\n" % obj.portal_type
    if obj.hints:
        out += "\n%hints\n"
        out += obj.hints.raw + "\n"
    if obj.example_text:
        out += "\n%example_text\n"
        out += obj.example_text.raw + "\n"
    for (i, x) in enumerate(obj.example_choices or []):
        out += "%s%s) %s\n" % (
            chr(97 + i),
            '.true' if x['correct'] else '',
            x['text'].replace("\n", "")
        )
    if obj.example_explanation:
        out += "\n%example_explanation\n"
        out += obj.example_explanation.raw + "\n"

    if statsObj:
        out += "%%r %d\n" % statsObj['timesCorrect']
        out += "%%n %d\n" % statsObj['timesAnswered']
    return out
