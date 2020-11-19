import logging
logger = logging.getLogger('tutorweb.content')

from AccessControl import Unauthorized
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

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
        for parts in (e.split() for e in emails):
            if len(parts) == 0:
                continue
            email = parts[0].lower()

            # Use e-mail for id if not provided
            id = parts[1] if len(parts) > 1 else email

            # If password is provided use it, otherwise assign a random password later
            pwd = parts[2] if len(parts) > 2 else None

            if not rtool.isValidEmail(email):
                self.uploadLog(
                    '"%s" not a valid email address, skipping'
                    % email
                )
                continue

            if not(mtool.getMemberById(id)):
                # User doesn't exist, create them first.
                self.uploadLog('Creating new user %s' % id)
                rtool.addMember(id, pwd or rtool.generatePassword(), properties=dict(
                    email=email,
                    username=id,
                ))
                if pwd is None:
                    self.uploadLog('Creating new user %s and e-mailing a link' % id)
                    rtool.registeredNotify(id)
                else:
                    self.uploadLog('Creating new user %s with password %s' % (id, pwd))

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
        notify(ObjectModifiedEvent(self.context))

    def __call__(self):
        if 'userlist' in self.request.form:
            self.addUsersToClass(
                l.strip()
                for l
                in self.request.form.get('userlist', '').split("\n")
            )

        # Render page
        return self.index()
