from Products.CMFCore.utils import getToolByName
from Products.MimetypesRegistry.MimeTypeItem import MimeTypeItem

# TODO: Disabled whilst it comes from Products.TutorWeb
#class LaTeX(MimeTypeItem):
#    __name__   = "LaTeX"
#    mimetypes  = ('text/latex', 'text/x-tex',)
#    extensions = ('tex',)
#    binary     = 0


class R(MimeTypeItem):
    __name__   = "R"
    mimetypes  = ('text/r', 'text/R',)
    extensions = ('r',)
    binary     = 0


class GnuPlot(MimeTypeItem):
    __name__   = "GNU Plot"
    mimetypes  = ('text/x-gnuplot',)
    extensions = ('gpi', 'plt', 'gp',)
    binary     = 0


class XFig(MimeTypeItem):
    __name__   = "Xfig"
    mimetypes  = ('image/x-xfig',)
    extensions = ('fig',)
    binary     = 0


def registerMimeTypes(context, logger=None):
    mimetypes_registry = getToolByName(context, 'mimetypes_registry')

    for k, v in globals().items():
        if k == 'MimeTypeItem':
            continue
        if not(isinstance(v, type) and issubclass(v, MimeTypeItem)):
            continue
        mimetypes_registry.register(v())
        logger.info('Registered MIME-type %s' % k)
