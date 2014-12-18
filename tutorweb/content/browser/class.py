import logging
logger = logging.getLogger('tutorweb.content')

from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView


class BulkAddStudentView(BrowserView):
    def uploadLog(self, line=None):
        """Return upload log, optionally adding lines first"""
        if not hasattr(self, '_uploadLog'):
            self._uploadLog = ''
        if line:
            logging.info(line)
            self._uploadLog += line + '\n'
        return self._uploadLog

    def addUsersToClass(self, emails):
        """Given list of email addresses, add users."""
        mtool = getToolByName(self.context, 'portal_membership')
        rtool = getToolByName(self.context, 'portal_registration')

        self.uploadLog('Adding users to %s' % self.context.absolute_url())
        for email in (e.lower() for e in emails):
            if not rtool.isValidEmail(email):
                self.uploadLog(
                    '"%s" not a valid email address, skipping'
                    % email
                )
                continue

            # We always use email as the id now
            id = email

            if not(mtool.getMemberById(id)):
                # User doesn't exist, create them first.
                self.uploadLog('Creating new user %s' % id)
                rtool.addMember(id, rtool.generatePassword(), properties=dict(
                    email=email,
                    username=id,
                ))
                rtool.registeredNotify(id)

            # Ensure user is on the list
            if not getattr(self.context, 'students', None):
                self.uploadLog('Adding %s (%s) to course' % (id, email))
                self.context.students = [id]
            if id not in self.context.students:
                self.uploadLog('Adding %s (%s) to course' % (id, email))
                self.context.students.append(id)
            else:
                self.uploadLog('%s (%s) already on course' % (id, email))
        self.context.reindexObject()

    def __call__(self):
        if 'userlist' in self.request.form:
            self.addUsersToClass(
                l.strip()
                for l
                in self.request.form.get('userlist', '').split("\n")
            )

        # Render page
        return self.index()
