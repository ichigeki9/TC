from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).select_related('category')

    current = None
    slug = request.GET.get('kategoria')
    if slug:
        current = get_object_or_404(Category, slug=slug)
        products = products.filter(category=current)

    return render(request, 'shop/list.html', {
        'categories': categories,
        'current': current,
        'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    related = Product.objects.filter(is_active=True, category=product.category).exclude(pk=product.pk)[:4]
    return render(request, 'shop/detail.html', {'product': product, 'related': related})
