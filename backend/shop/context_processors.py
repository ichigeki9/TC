from .cart import SESSION_KEY


def cart(request):
    return {'cart_count': sum(request.session.get(SESSION_KEY, {}).values())}
