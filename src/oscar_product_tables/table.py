from django.conf import settings
from oscar_product_tables.cell import AttachedCell, AttributeCell, PartnerCell
from oscar.core.loading import get_model
from .col import Col
from .row import Row

Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
Partner = get_model('partner','Partner')
StockRecord = get_model('partner','StockRecord')


class FieldsPluginBase:
    """
    Col need to be classmethods because they are needed before instantiating
    """
    cell_class = None

    def __init__(self, rows):
        self.code = self.cell_class.type
        self.objects = {obj.code: obj for obj in self.get_queryset()}
        self.cols = [*self.get_cols()]
        self.rows = self.add_cells_to_rows(rows)
        print(self.cell_class, 'executed')
    
    def add_cells_to_rows(self, rows):
        for row in rows:
            for col in self.cols:
                obj = self.get_obj(row, col)
                cell = self.cell_class(row=row, col=col, obj=obj)
                row.add_cell(cell)
        return rows

    def get_cols(self):
        raise NotImplementedError('Needs to be overwritten')

    def get_queryset(self):
        return []

    def get_obj(self, row, col):
        return self.objects.get(col.code, None)

    @classmethod
    def product_queryset(cls, qs):
        return qs


class AttachedFieldsPlugin(FieldsPluginBase):
    cell_class = AttachedCell

    def get_cols(self):
        cols = []
        for code in self.get_fieldnames():
            field = Product._meta.get_field(code)
            cols.append(
                Col(field.name, Product._meta.get_field(code).verbose_name))
        return cols

    @classmethod
    def get_fieldnames(cls):
        fieldnames = getattr(settings, 'OSCAR_ATTACHED_PRODUCT_FIELDS', [])
        return ['upc', 'title', *fieldnames]

    @classmethod
    def product_queryset(cls, qs):
        for field in cls.get_fieldnames():
            if Product._meta.get_field(field).is_relation:
                qs = qs.select_related(field)
        return qs


class AttributeFieldsPlugin(FieldsPluginBase):
    cell_class = AttributeCell

    def get_cols(self):
        for obj in self.objects.values():
            yield Col(obj.code, obj.name)

    def get_queryset(self):
        qs = ProductAttribute.objects.distinct('code')
        qs = qs.select_related('option_group')
        qs = qs.prefetch_related('option_group__options')
        return qs

    @classmethod
    def product_queryset(cls, qs):
        qs = qs.select_related('product_class')
        qs = qs.prefetch_related(
            'product_class__attributes',
            'attribute_values',
            'attribute_values__attribute',
            'attribute_values__value_option',
            'stockrecords',
            'stockrecords__partner',
        )
        return qs


class PartnerFieldsPlugin(FieldsPluginBase):
    cell_class = PartnerCell

    def get_cols(self):
        for obj in self.objects.values():
            yield Col(obj.code, obj.name)

    def get_queryset(self):
        return Partner.objects.all()


class Table:
    fixed_cell_count = 2
    all_plugin_classes = [
        AttachedFieldsPlugin,
        AttributeFieldsPlugin,
        PartnerFieldsPlugin,
    ]

    def __init__(self, plugin_classes=None, product=None):
        plugin_classes = plugin_classes or self.all_plugin_classes
        self.products = self.get_queryset(plugin_classes, product)
        self.rows = [Row(product) for product in self.products]
        self.plugins = [cls(self.rows) for cls in plugin_classes]
        self.cols = [*self.get_cols()]

    def get_cols(self):
        for plugin in self.plugins:
            for col in plugin.cols:
                yield col

    def get_queryset(self, plugin_classes, product=None):
        qs = Product.objects.browsable_dashboard()
        if product:
            qs = qs.filter(id=product.id)
        for cls in plugin_classes:
            qs = cls.product_queryset(qs)
        qs = qs.order_by('title')
        return qs

    def get_field(self, product, code):
        for row in self.rows:
            if row.product == product:
                break
        for cell in row.cells:
            if cell.code == code:
                return cell
