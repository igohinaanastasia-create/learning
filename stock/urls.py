from django.urls import path
from stock.views import stock_list, stock_detail, stock_trade, account

urlpatterns = [
    path('list/', stock_list, name='list'),
    path('detail/<int:pk>/', stock_detail, name='detail'),
    path('trade/<int:pk>/', stock_trade, name='trade'),
    path('account/', account, name='account'),
]

