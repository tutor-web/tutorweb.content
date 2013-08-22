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
        # What we start off with when forming a new question
        initialitem = dict(
            processLatex=True,
            _defmime='text/x-tex',
            _deffield='text',
        )
        item = initialitem.copy()
        for line in (l.strip().decode('utf8') for l in file):
            if not line:
                pass

            elif line == '%===':
                # Separator, return this and move on to next item
                yield finalise(item)
                item = initialitem.copy()

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

            elif re.search(r'^\w\.(true|false)\)', line) or re.search(r'^\w\)', line):
                # a) or a.true) choices
                # Choose which field it should go in
                if line.startswith("d.") and "of the above" in line.lower():
                    # A "any of the above" or "none of the above" option goes at the bottom
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
                    correct=(re.search(r'^\w\.true\)', line) is not None),
                ))

            elif re.search(r'%n\s+', line):
                item['timesanswered'] = line.replace('%n', '', 1).strip()

            elif re.search(r'%r\s+', line):
                item['timescorrect'] = line.replace('%r', '', 1).strip()

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
                    item[item['_deffield']] = (item[item['_deffield']] + "\n" + line).strip()
        if item.keys():
            # Return final item too
            yield finalise(item)


class LatexSinkSection(object):
    """
    Write tutorweb questions out to a LaTeX file
    """
    classProvides(ISectionBlueprint)
    implements(ISection)
