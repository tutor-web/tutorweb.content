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
                        contenttype=item['_defmime'],
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

            # Tidy up and return
            del item['_defmime']
            return item
        item = dict(
            processLatex=True,
            _defmime='text/x-tex',
        )
        defaultfield = 'text'
        for line in (l.strip().decode('utf8') for l in file):
            if not line:
                pass
            elif line == '%===':
                # Separator, return this and move on to next item
                yield finalise(item)
                item = dict(
                    processLatex=True,
                    _defmime='text/x-tex',
                )
                defaultfield = 'text'
            elif re.search(r'%ID\s+', line):
                item['id'] = line.replace('%ID', '', 1).strip()
            elif re.search(r'%title\s+', line):
                item['title'] = line.replace('%title', '', 1).strip()
            elif re.search(r'%image\s+', line):
                #TODO: Fetch file
                raise NotImplementedError('Should fetch file at this point')
                item['image'] = line.replace('%image', '', 1).strip()
            elif line.startswith('%Explanation'):
                # Any un %'ed lines are now part of the explanation
                initExplanation = line.replace('%Explanation', '', 1).strip()
                defaultfield = 'explanation'
                if initExplanation:
                    item[defaultfield] = [initExplanation]
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
            elif re.search(r'^\w\)', line):
                # a) -- z) choices. Use file ordering.
                if 'choices' not in item:
                    item['choices'] = []
                item['choices'].append(dict(
                    text=re.sub(r'^\w\)\s*', '', line),
                    randomize=True,
                ))
                defaultfield='choices'
            elif re.search(r'^\w\.(true|false)\)', line):
                # a.true) choices
                if 'choices' not in item:
                    item['choices'] = []
                item['choices'].append(dict(
                    text=re.sub(r'^\w\.(true|false)\)\s*', '', line),
                    randomize=True,
                    correct=(re.search(r'^\w\.true\)', line) is not None),
                ))
            elif re.search(r'%n\s+', line):
                item['timesanswered'] = line.replace('%n', '', 1).strip()
            elif re.search(r'%r\s+', line):
                item['timescorrect'] = line.replace('%r', '', 1).strip()
            else:
                if defaultfield == 'choices':
                    # Append to last choice
                    item['choices'][-1]['text'] = (item['choices'][-1]['text']
                                                  + "\n" + line).strip()
                else:
                    # Line that needs appending to
                    if defaultfield not in item:
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
