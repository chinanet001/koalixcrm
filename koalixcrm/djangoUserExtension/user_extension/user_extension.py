# -*- coding: utf-8 -*-

from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext as _

from koalixcrm.crm.exceptions import *
from koalixcrm.crm.contact.postaladdress import PostalAddress
from koalixcrm.crm.contact.phoneaddress import PhoneAddress
from koalixcrm.crm.contact.emailaddress import EmailAddress
from koalixcrm.crm.documents.pdfexport import PDFExport
from koalixcrm.djangoUserExtension.const.purpose import *
from koalixcrm.djangoUserExtension.exceptions import TemplateSetMissingForUserExtension
from koalixcrm.globalSupportFunctions import xstr


class UserExtension(models.Model):
    user = models.ForeignKey("auth.User", blank=False, null=False)
    defaultTemplateSet = models.ForeignKey("TemplateSet")
    defaultCurrency = models.ForeignKey("crm.Currency")

    @staticmethod
    def objects_to_serialize(object_to_create_pdf, reference_user):
        from koalixcrm.crm.contact.phoneaddress import PhoneAddress
        from koalixcrm.crm.contact.emailaddress import EmailAddress
        from django.contrib import auth
        objects = list(auth.models.User.objects.filter(id=reference_user.id))
        user_extension = UserExtension.objects.filter(user=reference_user.id)
        if len(user_extension) == 0:
            raise UserExtensionMissing(_("During "+str(object_to_create_pdf)+" PDF Export"))
        phone_address = UserExtensionPhoneAddress.objects.filter(
            userExtension=user_extension[0].id)
        if len(phone_address) == 0:
            raise UserExtensionPhoneAddressMissing(_("During "+str(object_to_create_pdf)+" PDF Export"))
        email_address = UserExtensionEmailAddress.objects.filter(
            userExtension=user_extension[0].id)
        if len(email_address) == 0:
            raise UserExtensionEmailAddressMissing(_("During "+str(object_to_create_pdf)+" PDF Export"))
        objects += list(user_extension)
        objects += list(EmailAddress.objects.filter(id=email_address[0].id))
        objects += list(PhoneAddress.objects.filter(id=phone_address[0].id))
        return objects

    @staticmethod
    def get_user_extension(django_user):
        user_extensions = UserExtension.objects.filter(user=django_user)
        if len(user_extensions) > 1:
            raise TooManyUserExtensionsAvailable(_("More than one User Extension define for user ") + django_user.__str__())
        elif len(user_extensions) == 0:
            raise UserExtensionMissing(_("No User Extension define for user ") + django_user.__str__())
        return user_extensions[0]

    def create_pdf(self, template_set, printed_by):
        return PDFExport.create_pdf(self, template_set, printed_by)

    def get_template_set(self, template_set):
        if template_set == self.defaultTemplateSet.work_report_template:
            if self.defaultTemplateSet.work_report_template:
                return self.defaultTemplateSet.work_report_template
            else:
                raise TemplateSetMissingForUserExtension((_("Template Set for work report " +
                                                            "is missing for User Extension" + str(self))))

    def get_fop_config_file(self, template_set):
        template_set = self.get_template_set(template_set)
        return template_set.get_fop_config_file()

    def get_xsl_file(self, template_set):
        template_set = self.get_template_set(template_set)
        return template_set.get_xsl_file()

    def serialize_to_xml(self):
        objects = [self, ]
        main_xml = PDFExport.write_xml(objects)
        project_xml = self.project.serialize_to_xml(reporting_period=self)
        main_xml = PDFExport.merge_xml(main_xml, project_xml)
        return main_xml

    class Meta:
        app_label = "djangoUserExtension"
        verbose_name = _('User Extension')
        verbose_name_plural = _('User Extension')

    def __str__(self):
        return xstr(self.id) + ' ' + xstr(self.user.__str__())


class UserExtensionPostalAddress(PostalAddress):
    purpose = models.CharField(verbose_name=_("Purpose"), max_length=1, choices=PURPOSESADDRESSINUSEREXTENTION)
    userExtension = models.ForeignKey(UserExtension)

    def __str__(self):
        return xstr(self.name) + ' ' + xstr(self.prename)

    class Meta:
        app_label = "djangoUserExtension"
        verbose_name = _('Postal Address for User Extension')
        verbose_name_plural = _('Postal Address for User Extension')


class UserExtensionPhoneAddress(PhoneAddress):
    purpose = models.CharField(verbose_name=_("Purpose"), max_length=1, choices=PURPOSESADDRESSINUSEREXTENTION)
    userExtension = models.ForeignKey(UserExtension)

    def __str__(self):
        return xstr(self.phone)

    class Meta:
        app_label = "djangoUserExtension"
        verbose_name = _('Phone number for User Extension')
        verbose_name_plural = _('Phone number for User Extension')


class UserExtensionEmailAddress(EmailAddress):
    purpose = models.CharField(verbose_name=_("Purpose"), max_length=1, choices=PURPOSESADDRESSINUSEREXTENTION)
    userExtension = models.ForeignKey(UserExtension)

    def __str__(self):
        return xstr(self.email)

    class Meta:
        app_label = "djangoUserExtension"
        verbose_name = _('Email Address for User Extension')
        verbose_name_plural = _('Email Address for User Extension')


class InlineUserExtensionPostalAddress(admin.StackedInline):
    model = UserExtensionPostalAddress
    extra = 1
    classes = ('collapse-open',)
    fieldsets = (
        (_('Basics'), {
            'fields': (
                'prefix',
                'prename',
                'name',
                'addressline1',
                'addressline2',
                'addressline3',
                'addressline4',
                'zipcode',
                'town',
                'state',
                'country',
                'purpose')
        }),
    )
    allow_add = True


class InlineUserExtensionPhoneAddress(admin.StackedInline):
    model = UserExtensionPhoneAddress
    extra = 1
    classes = ('collapse-open',)
    fieldsets = (
        (_('Basics'), {
            'fields': ('phone',
                       'purpose',)
        }),
    )
    allow_add = True


class InlineUserExtensionEmailAddress(admin.StackedInline):
    model = UserExtensionEmailAddress
    extra = 1
    classes = ('collapse-open',)
    fieldsets = (
        (_('Basics'), {
            'fields': ('email',
                       'purpose',)
        }),
    )
    allow_add = True


class OptionUserExtension(admin.ModelAdmin):
    list_display = ('id',
                    'user',
                    'defaultTemplateSet',
                    'defaultCurrency')
    list_display_links = ('id',
                          'user')
    list_filter = ('user',
                   'defaultTemplateSet',)
    ordering = ('id',)
    search_fields = ('id',
                     'user')
    fieldsets = (
        (_('Basics'), {
            'fields': ('user',
                       'defaultTemplateSet',
                       'defaultCurrency')
        }),
    )

    def create_work_report_pdf(self, request, queryset):
        from koalixcrm.crm.views.pdfexport import PDFExportView
        for obj in queryset:
            response = PDFExportView.export_pdf(self,
                                                request,
                                                obj,
                                                ("/admin/djangoUserExtension/"+obj.__class__.__name__.lower()+"/"),
                                                obj.defaultTemplateSet.work_report_template)
        return response

    create_work_report_pdf.short_description = _("Work Report PDF")

    save_as = True
    actions = [create_work_report_pdf]
    inlines = [InlineUserExtensionPostalAddress,
               InlineUserExtensionPhoneAddress,
               InlineUserExtensionEmailAddress]