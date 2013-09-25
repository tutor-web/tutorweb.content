import logging
logger = logging.getLogger('tutorweb.content')

from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView


class EnrolView(BrowserView):
    def __call__(self):
        mt = getToolByName(self.context, 'portal_membership')
        if mt.isAnonymousUser():
            raise Unauthorized
        mb = mt.getAuthenticatedMember()

        if not getattr(self.context, 'students', None):
            self.context.students = []
        self.context.students.append(mb.getUserName())

        self.request.response.redirect(self.context.absolute_url())


class BulkAddStudentView(BrowserView):
    def uploadLog(self, line=None):
        """Return upload log, optionally adding lines first"""
        if not hasattr(self, '_uploadLog'):
            self._uploadLog = ''
        if line:
            logging.info(line)
            self._uploadLog += line + '\n'
        return self._uploadLog

    def getAllMemberEmails(self):
        """Make lookup of member email addresses to ids"""
        mtool = getToolByName(self.context, 'portal_membership')
        out = {}
        for m in mtool.listMembers():
            email = m.getProperty('email').lower()
            if email in out:
                self.uploadLog("WARNING: %s used by both %s and %s, assuming latter" % (
                    email,
                    out[email],
                    m.id,
                ))
            out[email] = m.id
        return out

    def addUsersToClass(self, emails):
        """Given list of email addresses, add users."""
        mtool = getToolByName(self.context, 'portal_membership')
        rtool = getToolByName(self.context, 'portal_registration')
        membersEmails = self.getAllMemberEmails()

        self.uploadLog('Adding users to %s' % self.context.absolute_url())
        for email in (e.lower() for e in emails):
            if not rtool.isValidEmail(email):
                self.uploadLog(
                    '"%s" not a valid email address, skipping'
                    % email
                )
                continue

            if email in membersEmails:
                # User with email already exists
                id = membersEmails[email]
            elif mtool.getMemberById(email):
                # User with this id already exists (but has a different email
                # address for some reason?), assume they're the same
                id = email
            else:
                # User doesn't exist, create them first.
                id = email
                self.uploadLog('Creating new user %s' % id)
                rtool.addMember(id, rtool.generatePassword(), properties=dict(
                    email=email,
                    username=id,
                    fullname=id,
                ))
                rtool.registeredNotify(id)

            # Ensure user is on the list
            if id not in self.context.students:
                self.uploadLog('Adding %s (%s) to course' % (id, email))
                self.context.students.append(id)
            else:
                self.uploadLog('%s (%s) already on course' % (id, email))

    def __call__(self):
        if 'userlist' in self.request.form:
            self.addUsersToClass(
                l.strip()
                for l
                in self.request.form.get('userlist', '').split("\n")
            )

        # Render page
        return self.index()
