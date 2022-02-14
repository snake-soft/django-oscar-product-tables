from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.core.paginator import Paginator
from oscar_product_tables.forms import ProductFieldForm
from oscar.core.loading import get_model
from oscar_product_tables.plugins import *
from ..forms import TableConfigForm
from ..table import Table

Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
Partner = get_model('partner','Partner')
StockRecord = get_model('partner','StockRecord')


class GetTableMixin:
    template_name = 'product_tables/dashboard/product_table.html'
    template_name_table = 'product_tables/table.html'
    template_name_table_page = 'product_tables/table_page.html'
    paginate_by = 1000
    categories = []

    def get_plugin_classes(self):
        return [
            AttachedFieldsPlugin,
            AttributeFieldsPlugin,
            PartnerFieldsPlugin,
        ]

    def get_disabled_plugins(self):
        return []

    def get_read_only_plugins(self):
        return []

    def get_table(self, **additional_kwargs):
        """ Overwrite when using another plugin set """
        return Table(**self.get_table_kwargs(**additional_kwargs))

    def get_table_kwargs(self, **additional_kwargs):
        """ Overwrite when using another plugin_classes set """
        kwargs = {'plugin_classes': []}
        if hasattr(self, 'product'):
            kwargs.update({'product': self.product})
        kwargs.update(additional_kwargs)
        kwargs['read_only'] = self.get_read_only_plugins()
        kwargs['disabled'] = self.get_disabled_plugins()
        return kwargs

    def get_context_data(self, **kwargs):
        if self.categories:
            qs = self.get_queryset().filter(categories__in=self.categories).distinct()
        else:
            qs = self.get_queryset().none()
        paginator = Paginator(qs, self.paginate_by)
        site_nr = self.request.GET.get('page', 1)
        page = paginator.page(site_nr)
        context = super().get_context_data(**kwargs)
        context['table'] = self.get_table(queryset=page.object_list)
        context['page'] = page
        context['progress'] = int(page.number / page.paginator.num_pages * 100)
        if not 'page' in self.request.GET:
            context['form'] = TableConfigForm(self.request)
        return context

    def get_queryset(self):
        return Product.objects.browsable_dashboard().order_by('title')

    def get_template_names(self):
        if 'page' in self.request.GET:
            return self.template_name_table_page
        return self.template_name

    def user_is_allowed(self, user):
        return user.is_superuser

    def dispatch(self, request, *args, slug=None, **kwargs):
        if not self.user_is_allowed(request.user):
            raise AttributeError('Not allowed for user ' + request.user)
        if slug:
            category = Category.objects.get(slug=slug)
            self.categories = category.get_descendants_and_self()
        return super().dispatch(request, *args, **kwargs)


class ProductTableView(GetTableMixin, TemplateView):
    http_method_names = ['get']


class ProductTableAjaxView(GetTableMixin, FormView):
    http_method_names = ['get', 'post']
    form_class = ProductFieldForm

    def setup(self, request, product_id, code, *args, **kwargs):
        self.product = Product.objects.get(id=product_id)
        self.code = code
        self.previous_data = None
        self.table = self.get_table()
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
                form.save()
                # Reinitialize table to get new field data
                self.table = self.get_table()
                return self.get(request, product_id, code, *args, **kwargs)
        return super().post(request, *args, **kwargs)
