from zope.interface import implements

from Products.PortalTransforms.interfaces import ITransform
from Products.PortalTransforms.libtransforms.commandtransform import popentransform


class RestToTex(popentransform):
    """
    Translate ReST via. pandoc
    """
    implements(ITransform)
    __name__ = "rst_to_tex"
    inputs = ("text/x-rst", "text/restructured",)
    output = "text/x-tex"
    output_encoding = 'utf-8'

    binaryName = "/usr/bin/pandoc"
    binaryArgs = "-r rst -w latex"
    useStdin = True


def register():
    return RestToTex()
