from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from stock.models import Stock, AccountCurrency, AccountStock
from stock.forms import BuySellForm

def stock_list(request):
    stocks = Stock.objects.all()
    context = {
        'stocks': stocks,
    }
    return render(request, 'stocks.html', context)

@login_required
def stock_detail(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    context = {
        'stock': stock,
        'form': BuySellForm(initial={'price': stock.get_random_price()})
    }
    return render(request, 'stock.html', context)

@login_required
def stock_trade(request, pk):
    stock = get_object_or_404(Stock, pk=pk)

    if request.method == "POST":
        form = BuySellForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data['action']
            amount = form.cleaned_data['amount']
            price = form.cleaned_data['price']
            total = price * amount

            acc_currency, _ = AccountCurrency.objects.get_or_create(
                account=request.user.account,
                currency=stock.currency,
                defaults={'amount': 0}
            )

            acc_stock, _ = AccountStock.objects.get_or_create(
                account=request.user.account,
                stock=stock,
                defaults={'amount': 0, 'average_buy_cost': 0}
            )

            if action == 'buy':
                if acc_currency.amount < total:
                    form.add_error(None, 'Недостаточно средств')
                else:
                    current_cost = acc_stock.average_buy_cost * acc_stock.amount
                    new_total_amount = acc_stock.amount + amount
                    new_total_cost = current_cost + total

                    acc_stock.amount = new_total_amount
                    acc_stock.average_buy_cost = new_total_cost / new_total_amount

                    acc_currency.amount -= total

                    acc_stock.save()
                    acc_currency.save()

            elif action == 'sell':
                if acc_stock.amount < amount:
                    form.add_error(None, 'Недостаточно акций')
                else:
                    acc_stock.amount -= amount
                    acc_currency.amount += total

                    if acc_stock.amount == 0:
                        acc_stock.delete()
                    else:
                        acc_stock.save()

                    acc_currency.save()
            cache.delete(f'stocks_{request.user.username}')
            cache.delete(f'currencies_{request.user.username}')

            return redirect('stock:account')

    else:
        form = BuySellForm(initial={
            'price': stock.get_random_price(),
            'action': 'buy'
        })

    return render(request, 'stock.html', {
        'stock': stock,
        'form': form
    })

@login_required
def account(request):
    currencies = cache.get(f'currencies_{request.user.username}')
    stocks = cache.get(f'stocks_{request.user.username}')

    if currencies is None:
        currencies = [
            {
                'amount': acc_currency.amount,
                'sign': acc_currency.currency.sign
            } for acc_currency in request.user.account.accountcurrency_set.select_related('currency')
        ]
        cache.set(f'currencies_{request.user.username}', currencies, 5)

    if stocks is None:
        stocks = [
            {
                'ticker': acc_stock.stock.ticker,
                'amount': acc_stock.amount,
                'avg': acc_stock.average_buy_cost
            } for acc_stock in request.user.account.accountstock_set.select_related('stock').all()
        ]
        cache.set(f'stocks_{request.user.username}', stocks, 5)

    context = {
        'currencies': currencies,
        'stocks': stocks
    }
    return render(request, 'account.html', context)