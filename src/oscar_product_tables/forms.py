from django import forms
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_model
from django.urls.base import reverse

Category = get_model('catalogue', 'Category')


class ProductFieldForm(forms.Form):
    def __init__(self, cell, request):
        self.url = request.path
        self.code = cell.code
        self.name = cell.name
        #pylint: disable=invalid-name
        auto_id = 'id_%s_' + str(cell.product.id)
        self.id = 'form_' + auto_id % (self.code,)
        if request.method == 'POST':
            super().__init__(request.POST, auto_id=auto_id)
        else:
            super().__init__(auto_id=auto_id)
        self.cell = cell
        self.initialize_fields()
        self.is_valid()

    def get_fields(self):
        return self.cell.fields

    def initialize_fields(self):
        self.fields['productid'] = forms.IntegerField(
            widget=forms.HiddenInput(),
            initial=self.cell.product.id,
        )
        self.fields['code'] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=self.cell.code,
        )
        self.fields.update(self.get_fields())

    def save(self):
        field_codes = self.cell.fields.keys()
        data = {k: v for k, v in self.cleaned_data.items() if k in field_codes}
        self.cell.save(**data)


class TableConfigForm(forms.Form):
    category = forms.ChoiceField(label=_('Kategorie'))

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices=self.get_category_choices()
        resolver = request.resolver_match
        namespace = resolver.namespace
        url_name = resolver.url_name
        url = reverse(f'{namespace}:{url_name}')
        self.fields['category'].widget.attrs['onchange'] = \
            f'var key = $(this).val(); window.location.replace("{url}" + key);'
        self.fields['category'].initial=resolver.kwargs.get('slug', None)

    def get_category_choices(self):
        yield (None, _('Kategorie wählen'))
        for category in Category.objects.filter(is_public=True):
            yield((category.slug, (category.depth - 1) * '-' + category.name))
