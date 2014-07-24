import base64

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import defaultMatcher


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
        self.destUrl = options.get('desturl', '')

    def __iter__(self):
        def newSection(item, title=u'', text_field=None, image_field=None, image_url=None):
            def rtv(text, mime):
                if mime == 'text/latex':
                    mime = 'text/x-tex'
                return dict(data=text, contenttype=mime)

            sect = {"_class": "tutorweb.content.schema.SlideSection"}
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
                    sect['image_code'] = rtv(image_url, 'text/x-url')
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
                    _type='Image',
                    id=(item[dataField]['filename'] or item['id'] + '_' + imageField),
                    title=(item[dataField]['filename'] or item['id'] + '_' + imageField),
                    image=dict(
                        contenttype=item[dataField]['content_type'],
                        data=base64.b64decode(item[dataField]['data']),
                    ),
                    _url=(self.destUrl + '/' + (item[dataField]['filename'] or item['id'] + '_' + imageField)),
                )
                # Create the image as a file in it's own right
                yield newSlide['_images'][imageField]

            newSlide['sections'].append(newSection(
                item,
                title=u'',
                text_field=u'SlideText',
                image_field='SlideImage',
                image_url=newSlide['_images'].get('SlideImage', dict(_url=''))['_url'],
            ))
            if item.get(u'Explanation', "") or item.get(u'ExplanationText', ""):
                newSlide['sections'].append(newSection(
                    item,
                    title=u'Explanation',
                    text_field=u'Explanation',
                    image_field='ExplanationImage',
                    image_url=newSlide['_images'].get('ExplanationImage', dict(_url=''))['_url'],
                ))
            for sectName in ['Details', 'Examples', 'Alternative', 'Handout', 'SlideReference']:
                if item.get(sectName, "").strip():
                    newSlide['sections'].append(newSection(
                        item,
                        title='Slide Reference' if sectName == 'SlideReference' else sectName,
                        text_field=sectName,
                    ))
            yield newSlide
