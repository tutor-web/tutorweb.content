from zope import schema
from zope.component import adapts
from zope.interface import Interface, Invalid
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from z3c.form import field, validator

from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.browser.register import RegistrationForm, AddUserForm
from plone.app.users.browser.userdatapanel import UserDataPanel
from plone.supermodel import model
from plone.z3cform.fieldsets import extensible

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

from tutorweb.content import _


class IEnhancedUserDataSchema(model.Schema):
    """ Use all the fields from the default user data schema, and add various
    extra fields.
    """
    accept = schema.Bool(
        title=_(u'label_accept', default=u'Accept terms of use'),
        description=_(u'help_accept',
                      default=u"By logging on to the tutor-web I agree that my"
                      u" grades can be recorded into a database, these"
                      u" can be viewed by instructors in the"
                      u" appropriate courses and the grades can be"
                      u" used anonymously for research purposes."
                      u" Check this box if you agree to the"
                      u" conditions."),
        required=True,
        )


class EnhancedUserDataSchemaAdapter(AccountPanelSchemaAdapter):
    schema = IEnhancedUserDataSchema


class MustAccept(validator.SimpleFieldValidator):
    def validate(self, value):
        if value:
            return True
        raise Invalid(_("You must accept the terms to continue"))


class MustAcceptUserDataPanel(MustAccept):
    pass
validator.WidgetValidatorDiscriminators(
    MustAcceptUserDataPanel,
    field=IEnhancedUserDataSchema['accept'],
    view=UserDataPanel)


class MustAcceptRegistrationForm(MustAccept):
    pass
validator.WidgetValidatorDiscriminators(
    MustAcceptRegistrationForm,
    field=IEnhancedUserDataSchema['accept'],
    view=RegistrationForm)


class FormExtender(extensible.FormExtender):
    omitAccept = False

    def update(self):
        fields = field.Fields(IEnhancedUserDataSchema)
        if self.omitAccept:
            fields = fields.omit('accept')
        self.add(fields)

        self.form.fields['fullname'].field.required = True
        if 'username' in self.form.fields:
            self.form.fields['username'].field.title = u'Login name (official e-mail address)'
            self.form.fields['username'].field.description = u'''Please choose a login name.
Your login name should be an email
address. If you are using the system as a part of a course in a
school/university, use the official email address from your
institution (e.g. your @hi.is address). When you login the system
this email address is you login name'''
        self.form.fields['email'].field.title = u'Preferred email address'
        self.form.fields['email'].field.description = u'The email address we should use when sending you forgotten passwords, etc'
        self.form.buttons = self.form.buttons.omit('cancel')

        # If at beginning of editing process, and editing ourself, add nag.
        if not self.request.form.get('userid', None):
            mt = getToolByName(self.context, 'portal_membership')
            mb = mt.getAuthenticatedMember()
            if not mb.getProperty('accept', False):
                messages = IStatusMessage(self.request)
                messages.add(u"Make sure you accept the terms and conditions below", type=u"info")

class UserDataPanelExtender(FormExtender):
    adapts(Interface, IDefaultBrowserLayer, UserDataPanel)


class RegistrationPanelExtender(FormExtender):
    adapts(Interface, IDefaultBrowserLayer, RegistrationForm)


class AddUserFormExtender(FormExtender):
    adapts(Interface, IDefaultBrowserLayer, AddUserForm)
    omitAccept = True
