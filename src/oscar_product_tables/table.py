from django.conf import settings
from django.utils.functional import cached_property
from oscar_product_tables.cell import AttachedCell, AttributeCell, PartnerCell
from oscar.core.loading import get_model
from .col import Col
from .row import Row

Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
Partner = get_model('partner','Partner')
StockRecord = get_model('partner','StockRecord')


class Table:
    """ List of rows """
    fixed_cell_count = 2

    @cached_property
    def cols(self):
        cols = []
        for code in self.get_attached_field_codes():
            field = Product._meta.get_field(code)
            cols.append(
                Col(field.name, Product._meta.get_field(code).verbose_name)
            )

        for attribute in self.attributes:
            cols.append(Col(attribute.code, attribute.name))

        for partner in self.partners:
            cols.append(Col(partner.code, partner.name))

        return cols

    @cached_property
    def rows(self):
        return [self.get_row(product) for product in self.products]

    def get_attached_field_codes(self):
        config_fields = getattr(settings, 'OSCAR_ATTACHED_PRODUCT_FIELDS', [])
        return ['upc', 'title', *config_fields]

    def get_row(self, product):
        col_dict = {col.code: col for col in self.cols}
        row = Row(product)

        for code in self.get_attached_field_codes():
            row.add_cell(AttachedCell(row=row, col=col_dict[code]))

        for attribute in self.attributes:
            code = attribute.code
            row.add_cell(AttributeCell(attribute, row=row, col=col_dict[code]))

        for partner in self.partners:
            code = partner.code
            row.add_cell(PartnerCell(partner, row=row, col=col_dict[code]))

        return row

    @cached_property
    def attributes(self):
        qs = ProductAttribute.objects.distinct('code')
        qs = qs.select_related(
            'option_group',
        )
        qs = qs.prefetch_related(
            'option_group__options',
            #'productattributevalue_set',
            #'productattributevalue_set__value_option',
        )
        return qs

    @cached_property
    def products(self):
        qs = Product.objects.browsable_dashboard()
        qs = qs.select_related('product_class')
        qs = qs.prefetch_related(
            'product_class__attributes',
            #'product_class__attributes__option_group',
            #'product_class__attributes__option_group__options',
            'attribute_values',
            'attribute_values__attribute',
            'attribute_values__value_option',
            #'attributes__option_group',
            'stockrecords',
            'stockrecords__partner',
        )
        for field in self.get_attached_field_codes():
            if Product._meta.get_field(field).is_relation:
                qs = qs.select_related(field)

        #qs = qs[:100]
        #qs = qs.order_by('?')[:100]
        qs = qs.order_by('title')#[:100]
        return qs #[*qs]

    @cached_property
    def partners(self):
        return [*Partner.objects.all()]

    def validate(self):
        for row in self.rows:
            assert len(row.cells) == len(self.cols)
            #for cell in row.cells:

    def get_column_by_code(self, code):
        for col in self.cols:
            if col.code == code:
                return col

    def get_field(self, product, code):
        row = self.get_row(product)
        for cell in row.cells:
            if cell.code == code:
                return cell
