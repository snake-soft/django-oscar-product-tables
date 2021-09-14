from django import forms
from oscar.core.loading import get_model

ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
AttributeOption = get_model('catalogue', 'AttributeOption')
Partner = get_model('partner','Partner')
StockRecord = get_model('partner','StockRecord')


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

        self.field = self.get_field()
        self.initialize_fields()
        self.is_valid()

    def get_field(self):
        field = self.cell.field
        field.widget.attrs['class'] = 'form-control'
        return field

    def initialize_fields(self):
        self.fields['productid'] = forms.IntegerField(
            widget=forms.HiddenInput(),
            initial=self.cell.product.id,
        )
        self.fields['code'] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=self.cell.code,
        )
        self.fields[self.code] = self.field

    def save(self):
        product = self.cell.product
        code = self.cleaned_data['code']
        value = self.cleaned_data[code]
        updated = False

        if self.cell.type == 'attached':
            if getattr(product, code) != value:
                setattr(product, code, value)
                product.save()
                updated = True

        elif self.cell.type == 'attribute':
            attribute = product.product_class.attributes.get(code=self.code)
            if isinstance(value, AttributeOption):
                updated = ProductAttributeValue.objects.update_or_create(
                    attribute=attribute,
                    product=product,
                    defaults={
                        'value_option': value,
                    },
                )[0]
            else:
                updated = ProductAttributeValue.objects.filter(
                    attribute=attribute,product=product
                ).delete()[0]

        elif self.cell.type == 'partner':
            if value is not None:
                partner = Partner.objects.get(code=code)
                updated = StockRecord.objects.update_or_create(
                    partner=partner,
                    product=product,
                    defaults={
                        'price': value,
                    }
                )[0]
        return updated
