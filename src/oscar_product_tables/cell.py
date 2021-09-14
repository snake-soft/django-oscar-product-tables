from oscar.core.loading import get_model
from oscar.apps.dashboard.catalogue.forms import ProductForm

Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner','StockRecord')


class CellBase:
    type = None
    enabled = True

    def __init__(self, row, col):
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


class AttachedCell(CellBase):
    type = 'attached'

    @property
    def data(self):
        return getattr(self.product, self.code)

    @property
    def field(self):
        field = Product._meta.get_field(self.code).formfield()
        field.initial = getattr(self.product, self.code)
        return field

class AttributeCell(CellBase):
    type = 'attribute'

    def __init__(self, attribute, *args, **kwargs):
        self.attribute = attribute
        super().__init__(*args, **kwargs)

    @property
    def enabled(self):
        attribute_codes = [attribute.code for attribute in
                self.product.product_class.attributes.all()]
        return self.code in attribute_codes

    @property
    def data(self):
        value = self.attribute_values.get(self.code, None)
        if value and self.attribute.type in ('option', 'multi_option'):
            value = value.option
        return value

    @property
    def field(self):
        field = ProductForm.FIELD_FACTORIES[self.attribute.type](self.attribute)
        field.initial = self.attribute_values.get(self.code)
        return field

    @property
    def attribute_values(self):
        product_attributes = {}
        for attribute_value in self.product.attribute_values.all():
            attribute_code = attribute_value.attribute.code
            value = attribute_value.value
            product_attributes[attribute_code] = value
        return product_attributes


class PartnerCell(CellBase):
    type = 'partner'

    def __init__(self, partner, *args, **kwargs):
        self.partner = partner
        super().__init__(*args, **kwargs)

    @property
    def data(self):
        return self.stockrecords.get(self.code, None)

    @property
    def stockrecords(self):
        return {stockrecord.partner.code: stockrecord.price
                for stockrecord in self.product.stockrecords.all()}

    @property
    def field(self):
        field = StockRecord._meta.get_field('price').formfield()
        stockrecord = self.stockrecords.get(self.code, None)
        if stockrecord:
            field.initial = stockrecord
        return field
