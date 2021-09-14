from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from oscar_product_tables.forms import ProductFieldForm
from oscar.core.loading import get_model
from ..table import Table

Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
Partner = get_model('partner','Partner')
StockRecord = get_model('partner','StockRecord')


class ProductTableView(TemplateView):
    template_name = 'product_tables/dashboard/product_table.html'
    template_name_table = 'product_tables/table.html'
    http_method_names = ['get']

    def get_context_data(self, **kwargs):
        context = {**kwargs}
        table = Table()
        context['table'] = table
        return context


class ProductTableAjaxView(FormView):
    http_method_names = ['get', 'post']
    form_class = ProductFieldForm

    def setup(self, request, product_id, code, *args, **kwargs):
        self.product = Product.objects.get(id=product_id)
        self.code = code
        self.previous_data = None
        self.table = Table()
        super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = FormView.get_context_data(self, **kwargs)
        context['value'] = context['form'].cell.data
        context['previous_value'] = self.previous_data
        return context

    def get_template_names(self):
        return {
            'GET': 'product_tables/form.html',
            'POST': 'product_tables/field.html',
        }[self.request.method]

    def get_form_kwargs(self):
        return {
            'cell': self.table.get_field(self.product, self.code),
            'request': self.request,
        }

    def form_valid(self, form):
        return super().get(self.request, self.product.id, self.code)

    def get(self, request, product_id, code, *args, **kwargs):
        if not product_id or not code:
            raise AttributeError('Need product_id and code to get the form!')
        return super().get(request, *args, **kwargs)

    def post(self, request, product_id, code,  action, *args, **kwargs):
        form = self.get_form()
        if action == 'save':
            if form.is_valid():
                self.previous_data = form.cell.data
                updated = form.save()
                if not updated:
                    self.previous_data = None
                return self.get(request, product_id, code, *args, **kwargs)
        return super().post(request, *args, **kwargs)
