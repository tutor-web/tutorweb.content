from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import openFileReference
from collective.transmogrifier.utils import defaultMatcher

from tutorweb.content.schema import SlideSection


class TranslateOldTutorWeb(object):
    """
    Convert object from old Tutorweb into something new
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.key = defaultMatcher(options, 'key', name)

    def __iter__(self):
        def newSection(item, title=u'', text_field=None, image_field=None, image_filename=None):
            def rtv(text, mime):
                if mime == 'text/latex':
                    mime = 'text/x-tex'
                return dict(data=text, contenttype=mime)

            sect = {"_class" : "tutorweb.content.schema.SlideSection"}
            sect['title'] = title
            sect['text'] = rtv(
                item.get(text_field, ''),
                item.get('_content_type_' + text_field, u'text/latex'),
            )

            if image_field:
                image_type = item.get(image_field + u'Format', 'none')
                image_code = item.get(image_field + u'Text', '')
                if image_type == 'none':
                    sect['image_code'] = None
                elif image_type == 'image':
                    sect['image_code'] = rtv(image_filename, 'text/x-url')
                elif image_type == 'r':
                    # TODO: Rewrite read.table() calls to have HTTP
                    sect['image_code'] = rtv(image_code, 'text/R')
                elif image_type == 'gnuplot':
                    sect['image_code'] = rtv(image_code, 'text/x-gnuplot')
                elif image_type == 'fig':
                    sect['image_code'] = rtv(image_code, 'image/x-xfig')
                else:
                    raise ValueError("Unknown image type %s" % image_type)

                image_caption_field = image_field + u'Caption'
                sect['image_caption'] = item.get(image_caption_field, '')
            return sect

        for item in self.previous:
            newSlide = dict(
                _type='tw_slide',
                id=str(item[u'id']),
                title=item[u'title'],
                _images=dict(),
                sections=[],
            )

            # Extract useful image fields
            for imageField in ['SlideImage', 'ExplanationImage']:
                dataField = '_datafield_' + imageField
                if dataField not in item:
                    continue
                newSlide['_images'][imageField] = dict(
                    data=item[dataField]['data'],
                    content_type=item[dataField]['content_type'],
                    filename=(item[dataField]['filename'] or item['id'] + '_' + imageField),
                )
                # TODO: yield at this point, write them out as their own object

            newSlide['sections'].append(newSection(item,
                title=u'',
                text_field=u'SlideText',
                image_field='SlideImage',
                image_filename=newSlide['_images'].get('SlideImage', dict(filename=''))['filename'],
            ))
            newSlide['sections'].append(newSection(item,
                title=u'Explanation',
                text_field=u'Explanation',
                image_field='ExplanationImage',
                image_filename=newSlide['_images'].get('ExplanationImage', dict(filename=''))['filename'],
            ))
            for sectName in ['Details', 'Examples', 'Alternative', 'Handout', 'SlideReference']:
                if not item.get(sectName, None):
                    continue
                newSlide['sections'].append(newSection(item,
                    title='Slide Reference' if sectName == 'SlideReference' else sectName,
                    text_field=item[sectName],
                ))
            yield newSlide
