from oscar_product_tables.plugins import *
from oscar.core.loading import get_model
from .row import Row

Product = get_model('catalogue', 'Product')


class Table:
    fixed_cell_count = 2
    all_plugin_classes = [
        AttachedFieldsPlugin,
        AttributeFieldsPlugin,
        PartnerFieldsPlugin,
    ]

    def __init__(self, queryset=None, plugin_classes=None, product=None,
                 read_only=None, disabled=None):
        assert queryset is not None or product
        self.read_only = read_only or []
        self.disabled = disabled or []
        plugin_classes = plugin_classes or self.all_plugin_classes
        self.products = self.get_queryset(plugin_classes, queryset, product)
        self.rows = [Row(product) for product in self.products]
        self.plugins = self.get_plugins(plugin_classes)
        self.cols = self.get_cols()

    def get_plugins(self, plugin_classes):
        plugins = []
        for cls in plugin_classes:
            if cls not in self.disabled:
                plugins.append(cls(self.rows, read_only=cls in self.read_only))
        return plugins

    def get_cols(self):
        cols = []
        for plugin in self.plugins:
            for col in plugin.cols:
                cols.append(col)
        return cols

    def get_queryset(self, plugin_classes, queryset, product):
        qs = queryset
        if product:
            if not queryset:
                qs = Product.objects.all()
            qs = qs.filter(id=product.id)
        for cls in plugin_classes:
            if cls not in self.disabled:
                qs = cls.product_queryset(qs)
        return qs

    def get_row(self, product):
        for row in self.rows:
            if row.product == product:
                return row

    def get_field(self, product, code):
        row = self.get_row(product)
        for cell in row.cells:
            if cell.code == code:
                return cell
