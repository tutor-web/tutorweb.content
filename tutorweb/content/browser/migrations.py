import base64
import urlparse

from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from z3c.relationfield import RelationValue

from collective.transmogrifier.interfaces import ITransmogrifier
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from plone.namedfile.file import NamedBlobFile

from tutorweb.content.transmogrifier.collectivejsonifysource import catalog_query, fetch_item, fetch_children


class LectureImportView(BrowserView):
    """Copy a lecture from old tutor-web to new"""
    def __call__(self):
        if 'src' not in self.request.form:
            raise ValueError("Must provide a URL to a lecture in src")
        url = urlparse.urlparse(self.request.form['src'])

        # Find out id, Title & create new lecture
        oldLecture = fetch_item(url, url.path)
        newLecture = self.context[self.context.invokeFactory(
            type_name="tw_lecture",
            id=oldLecture['id'],
            title=oldLecture['title'],
            pdf_reference=oldLecture['LectureReference'],
        )]

        # Fetch hist_sel from qsp sub-object
        qsp = [x for x in fetch_children(url, url.path) if 'questionselectionparameters' in x]
        if len(qsp) > 0:
            histSel = fetch_item(url, url.path + '/' + qsp[0]).get('historical_selection_probability', -1.0)
            if histSel >= 0:
                newLecture.settings = [
                  dict(key='hist_sel', value =histSel)
                ]

        # Copy PDF
        if oldLecture.get("_datafield_Pdf", None):
            file = oldLecture["_datafield_Pdf"]
            newLecture.pdf = NamedBlobFile(
                filename=file['filename'],
                contentType=file['content_type'],
                data=base64.b64decode(file['data']),
            )

        # Publish the new lecture
        wftool = getToolByName(self.context, 'portal_workflow')
        wftool.doActionFor(newLecture, 'publish')
        newLecture.reindexObject()

        # Trigger slide import into our newly created lecture
        newLecture.unrestrictedTraverse('@@slide-copy')()


class SlideImportView(BrowserView):
    def __call__(self):
        if 'src' not in self.request.form:
            raise ValueError("Must provide a URL to a lecture in src")
        transmogrifier = ITransmogrifier(self.context)
        transmogrifier(
            'tutorweb.content.transmogrifier.oldtutorwebslideimport',
            definitions=dict(
                url=self.request.form['src'],
                folder='',
                desturl=self.context.absolute_url(),
            ),
        )
        return "success"


class TutorialImportView(BrowserView):
    """Copy a tutorial from old tutor-web to new"""
    def __call__(self):
        if 'src' not in self.request.form:
            raise ValueError("Must provide a URL to a tutorial in src")
        url = urlparse.urlparse(self.request.form['src'])

        # Find out id, Title & create new tutorial
        oldTutorial = fetch_item(url, url.path)
        newTutorial = self.context[self.context.invokeFactory(
            type_name="tw_tutorial",
            id=oldTutorial['id'],
            title=oldTutorial['title'],
            language=oldTutorial.get('TutorialLanguage', ''),
            author=oldTutorial.get('Author', ''),
            credits=oldTutorial.get('Credits', 0),
            pdf_preamble=oldTutorial.get('PdfPreamble', None),
            pdf_postamble=oldTutorial.get('PdfPostamble', None),
            pdf_reference=oldTutorial.get('PdfReference', None),
        )]

        # Fetch hist_sel from qsp sub-object
        histSel = oldTutorial.get('historical_selection_probability', None)
        if histSel >= 0:
            newTutorial.settings = [
              dict(key='hist_sel', value =histSel)
            ]

        # Copy PDF
        if oldTutorial.get("_datafield_Pdf", None):
            file = oldTutorial["_datafield_Pdf"]
            newTutorial.pdf = NamedBlobFile(
                filename=file['filename'],
                contentType=file['content_type'],
                data=base64.b64decode(file['data']),
            )

        # Set primary course
        if "inDepartmentCourse" in oldTutorial['_atrefs']:
            coursePath = oldTutorial['_atrefs']["inDepartmentCourse"][0]
            try:
                courseObj = self.context.restrictedTraverse(str(coursePath))
            except KeyError:
                raise ValueError("Cannot find course %s" % coursePath)

            intids = getUtility(IIntIds)
            newTutorial.primarycourse = RelationValue(intids.getId(courseObj))

        # Publish the new tutorial
        wftool = getToolByName(self.context, 'portal_workflow')
        wftool.doActionFor(newTutorial, 'publish')
        newTutorial.reindexObject()
