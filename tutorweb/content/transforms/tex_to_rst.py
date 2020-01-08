from zope.interface import implements

from Products.PortalTransforms.interfaces import ITransform
from Products.PortalTransforms.libtransforms.commandtransform import popentransform


class TexToRest(popentransform):
    """
    Translate TeX->ReST via. pandoc
    """
    implements(ITransform)
    __name__ = "tex_to_rst"
    inputs = ("text/x-tex",)
    output = "text/x-rst"
    output_encoding = 'utf-8'

    binaryName = "/usr/bin/pandoc"
    binaryArgs = "-r latex -w rst"
    useStdin = True


def register():
    return TexToRest()
