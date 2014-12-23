from Products.Five.browser import BrowserView

from ..tex_generator import TexGenerator

class TutorialTeXView(BrowserView):
    """Convert tutorials into TeX"""

    def __call__(self):
        tg = TexGenerator(self.context)
        self.request.response.write(str(tg.outputFiles()))
