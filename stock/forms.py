from django import forms

class BuySellForm(forms.Form):
    amount = forms.IntegerField(min_value=1)
    price = forms.DecimalField(min_value=0.01)
    action = forms.ChoiceField(
        choices=[('buy', 'Buy'), ('sell', 'Sell')],
        widget=forms.HiddenInput()
    )