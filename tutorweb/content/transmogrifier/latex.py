import re

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import openFileReference
from collective.transmogrifier.utils import defaultMatcher


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

        def finalise(item):
            # Convert rich text fields into dicts
            for field in ['text', 'explanation']:
                if field in item:
                    item[field] = dict(
                        contenttype='text/x-tex',
                        data="\n".join(item[field]),
                        encoding='utf-8',
                    )

            # Unless otherwise marked, last item is correct
            if 'choices' in item:
                for i, c in enumerate(item['choices']):
                    if 'correct' not in c:
                        c['correct'] = (i + 1 == len(item['choices']))

            # Set portal type for content
            if '_type' not in item:
                item['_type'] = 'tw_latexquestion'
                item['processLatex'] = True

            return item
        item = {}
        defaultfield = 'text'
        for line in (l.strip().decode('utf8') for l in file):
            if not line:
                pass
            elif line == '%===':
                # Separator, return this and move on to next item
                yield finalise(item)
                item = {}
                defaultfield = 'text'
            elif line.startswith('%ID '):
                item['id'] = line.replace('%ID', '', 1).strip()
            elif line.startswith('%title '):
                item['title'] = line.replace('%title', '', 1).strip()
            elif line.startswith('%image '):
                #TODO: Fetch file
                raise NotImplementedError('Should fetch file at this point')
                item['image'] = line.replace('%image', '', 1).strip()
            elif line.startswith('%Explanation'):
                # Any un %'ed lines are now part of the explanation
                initExplanation = line.replace('%Explanation', '', 1).strip()
                defaultfield = 'explanation'
                if initExplanation:
                    item[defaultfield] = [initExplanation]
            elif line.startswith('%format '):
                # Format tag: Don't understand anything other than LaTeX
                if line != '%format latex':
                    raise ValueError('Unknown format %s' % line)
            elif re.search(r'^\w\) ', line):
                # a) -- z) choices. Use file ordering.
                if 'choices' not in item:
                    item['choices'] = []
                item['choices'].append(dict(
                    text=re.sub(r'^\w\) ', '', line),
                    randomize=True,
                ))
            elif re.search(r'^\w\.(true|false)\) ', line):
                # a.true) choices
                #TODO:
                raise NotImplementedError
            else:
                # Line that needs appending to
                if defaultfield not in item:
                    #TODO: Guessed
                    item[defaultfield] = []
                item[defaultfield].append(line)
        if item.keys():
            # Return final item too
            yield finalise(item)


class LatexSinkSection(object):
    """
    Write tutorweb questions out to a LaTeX file
    """
    classProvides(ISectionBlueprint)
    implements(ISection)
