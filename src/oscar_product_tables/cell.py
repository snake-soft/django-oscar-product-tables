from typing import Dict
from django.utils.functional import cached_property
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from oscar.core.loading import get_model
from oscar.apps.dashboard.catalogue.forms import ProductForm

Product = get_model('catalogue', 'Product')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
StockRecord = get_model('partner','StockRecord')
Partner = get_model('partner','Partner')

__all__ = ['AttachedCell', 'AttributeCell', 'PartnerCell']


class CellBase:
    type = None
    enabled = True

    def __init__(self, row, col, obj=None, read_only=False):  # @UnusedVariable
        self.read_only = read_only
        self.row = row
        self.col = col
        self.name = col.name
        self.code = col.code
        self.product = row.product

    @property
    def data(self):
        raise NotImplementedError()

    @property
    def field(self):
        raise NotImplementedError()

    @property
    def fields(self) -> Dict:
        return {self.code: self.field}

    def save(self, **data):
        raise NotImplementedError()

    def __repr__(self):
        return 'Cell:{}:{}'.format(self.product.upc, str(self))

    def __str__(self):
        return self.code


class AttachedCell(CellBase):
    type = 'attached'

    @property
    def data(self):
        field = Product._meta.get_field(self.code)
        value = getattr(self.product, self.code)
        if field.choices:
            value = dict(field.choices).get(value, value)
        return value

    @property
    def field(self):
        field = Product._meta.get_field(self.code).formfield()
        field.initial = getattr(self.product, self.code)
        return field

    def save(self, **data):
        for code, value in data.items():
            if getattr(self.product, code) != value:
                setattr(self.product, code, value)
                self.product.save()


class AttributeCell(CellBase):
    type = 'attribute'

    def __init__(self, obj, *args, **kwargs):
        self.attribute = obj
        super().__init__(*args, **kwargs)

    @property
    def enabled(self):
        attribute_codes = [attribute.code for attribute in
                self.product.product_class.attributes.all()]
        return self.code in attribute_codes

    @property
    def data(self):
        value = self.attribute_values.get(self.code, None)
        if value:
            if self.attribute.type == 'option':
                value = value.option
            elif self.attribute.type == 'multi_option':
                value = ', '.join([x.option for x in value])
        return value

    @property
    def field(self):
        field = ProductForm.FIELD_FACTORIES[self.attribute.type](self.attribute)
        field.initial = self.attribute_values.get(self.code)
        return field

    @cached_property
    def attribute_values(self):
        product_attributes = {}
        for attribute_value in self.product.attribute_values.all():
            attribute_code = attribute_value.attribute.code
            value = attribute_value.value
            product_attributes[attribute_code] = value
        return product_attributes

    def save(self, **data):
        for code, value in data.items():
            attribute = self.product.product_class.attributes.get(code=code)
            if attribute.type == 'option':
                if value:
                    ProductAttributeValue.objects.update_or_create(
                        attribute=attribute,
                        product=self.product,
                        defaults={
                            'value_option': value,
                        },
                    )[0]
                else:
                    ProductAttributeValue.objects.filter(
                        attribute=attribute,
                        product=self.product,
                    ).delete()
            elif attribute.type == 'multi_option':
                if value:
                    val = ProductAttributeValue.objects.get_or_create(
                        attribute=attribute,
                        product=self.product,
                    )[0]
                    val.value_multi_option.set(value)
                else:
                    ProductAttributeValue.objects.filter(
                        attribute=attribute,
                        product=self.product,
                    ).delete()
            else:
                ProductAttributeValue.objects.filter(
                    attribute=attribute, product=self.product
                ).delete()


class PartnerCell(CellBase):
    type = 'price'

    def __init__(self, obj, *args, **kwargs):
        self.partner = obj
        assert obj
        super().__init__(*args, **kwargs)
        #self.type = self.code.split('__')[1]

    @property
    def show_sku(self):
        #return False
        site = Site.objects.get_current()
        if getattr(site, 'configuration', None):  # Domain specific
            return getattr(site.configuration, 'own_upc', False)
        if hasattr(settings, 'DATATABLES_SHOW_SKU'):
            return settings.DATATABLES_SHOW_SKU
        return False

    @property
    def data(self):
        if self.stockrecord:
            if self.show_sku:
                return f'{self.stockrecord.partner_sku} > {self.stockrecord.price}€'
            return f'{self.stockrecord.price}€'
        return '-'

    @property
    def fields(self)->Dict:
        fields = {}
        if self.show_sku:
            field = StockRecord._meta.get_field('partner_sku').formfield()
            field.widget.attrs['placeholder'] = _('Art.Nr.')
            field.required = False
            if self.stockrecord:
                field.initial = getattr(self.stockrecord, 'partner_sku')
            fields[f'partner_sku'] = field

        field = StockRecord._meta.get_field('price').formfield()
        field.widget.attrs['placeholder'] = _('Preis')
        field.required = False
        if self.stockrecord:
            field.initial = getattr(self.stockrecord, 'price')
        fields[f'price'] = field
        return fields

    @property
    def stockrecord(self):
        return self.stockrecords.get(self.partner.pk, None)

    @cached_property
    def stockrecords(self):
        return {stockrecord.partner.pk: stockrecord
                for stockrecord in self.product.stockrecords.all()}

    def save(self, **data):
        partner = self.partner #Partner.objects.get(code=code)
        if not data.get('partner_sku', None):
            data['partner_sku'] = self.product.upc

        if data['price'] is None:
            StockRecord.objects.filter(
                partner__pk=partner.pk, product=self.product).delete()
        else:
            StockRecord.objects.update_or_create(
                partner=partner,
                product=self.product,
                defaults=data
            )
