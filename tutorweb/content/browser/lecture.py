from Products.Five.browser import BrowserView
from plone.app.textfield.value import RichTextValue


def obj_children(obj, child_type):
    # TODO: Should filter by workflow state
    return (
        l.getObject()
        for l
        in obj.restrictedTraverse('@@folderListing')(
            Type=child_type,
            sort_on="id",
        )
    )


def rst_heading(s, heading_ch = "="):
    return str("%s\n%s\n\n" % (
        s,
        len(s) * heading_ch,
    ))


class LectureRstView(BrowserView):
    """Generate ReST for tutorial"""

    def __call__(self):
        writer = self.request.response
        lecture = self.context
        writer.setHeader("Content-type", "text/x-rst")
        writer.setHeader(
            'Content-disposition',
            "attachment; filename=%s.rst" % self.context.id,
        )

        writer.write(rst_heading(lecture.title, '*'))
        for slide in obj_children(lecture, 'Slide'):
            writer.write('\n\n\n..\n    Slide %s\n' % slide.absolute_url()),
            writer.write(rst_heading(slide.title, '='))

            for section in slide.sections:
                if not section.image_code and (not section.text or not section.text.raw.strip()):
                    # Neither image or text, ignore section
                    continue
                if type == 'explanation':
                    # Explanations are only useful as footnotes to slides
                    continue

                if section.title:
                     writer.write(rst_heading(section.title, '-'))

                if section.image_code and section.image_code.raw:
                    raise NotImplementedError()

                if section.text and section.text.raw:
                    l = section.text
                    writer.write(RichTextValue(
                        raw=l.raw,
                        mimeType=l.mimeType,
                        outputMimeType='text/x-rst',
                        encoding=l.encoding,
                    ).output.encode('utf8'))
