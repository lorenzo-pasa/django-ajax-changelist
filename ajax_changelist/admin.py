from django import http
from django.conf.urls import patterns
from django.contrib import admin
from django.db import models
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404
from django.views.generic import View


def get_printable_field_value(instance, fieldname):
    """ Get the display value of a model field, showing a comma-delimited
        list for M2M fields.
    """
    field = instance._meta.get_field(fieldname)
    field_value = getattr(instance, fieldname)

    if isinstance(field, models.ManyToManyField):
        field_value = ', '.join([unicode(f) for f in
                    field_value.all()])
    return field_value


"""
NOTE: be cautious setting M2M fields in `ajax_fields`.

The only currently supported M2M use case is for relations
to tables with a small number (< ~50) records.  For example,
relations to a model representing categories for news items.

If you do use this for M2M, to reduce queries when the admin
you should prefetch - you can do so by adding the following
queryset() method to your subclass of AjaxModelFormView:

    def queryset(self, request):
        queryset = self.model.original_manager.get_query_set()
        queryset = queryset.prefetch_related('NAME_OF_M2M_FIELD')
        return queryset
"""


class AjaxModelFormView(View):
    """ Handle AJAX updates of a single field on an object

        Usage:

        my_model_form = AjaxModelFormView.as_view(model=MyModel)
    """

    model = None

    def __init__(self, model, **kwargs):
        self.model = model

    def post(self, request, object_id, *args, **kwargs):
        if not request.user or not request.user.is_staff:
            return http.HttpResponseForbidden()

        request = request.POST.copy()

        fieldname = request.pop('field', None)[0]
        form_prefix = request.pop('prefix', None)[0]

        ItemForm = modelform_factory(self.model, fields=(fieldname,))
        instance = get_object_or_404(self.model, pk=object_id)
        form = ItemForm(request, instance=instance, prefix=form_prefix)

        if not form or not form.is_valid():
            return http.HttpResponseBadRequest()

        form.save()

        new_value = get_printable_field_value(instance, fieldname)

        return http.HttpResponse(new_value)


class AjaxModelAdmin(admin.ModelAdmin):
    """ Admin class providing support for inline forms in
        listview that are submitted through AJAX.
    """

    def __init__(self, *args, **kwargs):

        HANDLER_NAME_TPL = "_%s_ajax_handler"

        if not hasattr(self, 'ajax_fields'):
            self.ajax_fields = []

        self.list_display = list(self.list_display)
        self.list_display = self.list_display + map(lambda name: HANDLER_NAME_TPL % name,
                self.ajax_fields)

        super(AjaxModelAdmin, self).__init__(*args, **kwargs)

        for name in self.ajax_fields:
            setattr(self, HANDLER_NAME_TPL % name,
                    self._get_field_handler(name))

    def get_urls(self):
        """ Add endpoint for saving a new field value. """

        urls = super(AjaxModelAdmin, self).get_urls()
        list_urls = patterns('',
                (r'^(?P<object_id>\d+)$',
                 AjaxModelFormView.as_view(model=self.model)))
        return list_urls + urls

    def _get_field_handler(self, fieldname):
        """ Handle rendering of AJAX-editable fields for the changelist, by
            dynamically building a callable for each field.
        """

        def handler_function(obj, *args, **kwargs):
            ItemForm = modelform_factory(self.model, fields=(fieldname,))
            form = ItemForm(instance=obj, prefix="c" + unicode(obj.id))

            field_value = get_printable_field_value(obj, fieldname)

            # Render elements including initial field value for display as
            # plain text, plus form for editing the field.
            form_html = """
                <div class="ajx-inline-edit">
                <div id="{object_id}_{field_name}_value" class="ajx-inline-form-value">{field_value}</div>
                <div id="inlineForm{object_id}_{field_name}"
                        data-form-id="{object_id}"
                        data-field="{field_name}" data-prefix="c{object_id}"
                        class="ajx-inline-form hidden">{form}</div>
                </div>
                """.format(object_id=obj.id, field_name=fieldname,
                           form=form.as_p(),
                           field_value=field_value)

            return form_html

        handler_function.allow_tags = True
        handler_function.short_description = fieldname
        return handler_function

    class Media:

        #FIXME: dripping jQueries is straight-up wack.
        js = ('//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
                'ajax_changelist/js/lib/jquery.django_csrf.js',
                'ajax_changelist/js/admin.js',)
        css = {
             'all': ('ajax_changelist/css/admin.css',)
        }
