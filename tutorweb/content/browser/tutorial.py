import urlparse

from tutorweb.content.transmogrifier.collectivejsonifysource import catalog_query, fetch_item, fetch_children

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView


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
            title=oldLecture['title']
        )]

        # Fetch hist_sel from qsp sub-object
        qsp = [x for x in fetch_children(url, url.path) if 'questionselectionparameters' in x]
        if len(qsp) > 0:
            histSel = fetch_item(url, url.path + '/' + qsp[0]).get('historical_selection_probability', -1.0)
            if histSel >= 0:
                newLecture.settings = [
                  dict(key='hist_sel', value =histSel)
                ]

        # Publish the new lecture
        wftool = getToolByName(self.context, 'portal_workflow')
        wftool.doActionFor(newLecture, 'publish')
        newLecture.reindexObject()

        # Trigger slide import into our newly created lecture
        newLecture.unrestrictedTraverse('@@slide-copy')()
