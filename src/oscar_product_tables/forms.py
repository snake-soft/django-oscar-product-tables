from django import forms


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
