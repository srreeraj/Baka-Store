from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet,Transaction
from decimal import Decimal
from django.http import JsonResponse
from django.template.loader import render_to_string

# Create your views here.

def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user = request.user)
    transactions = wallet.transactions.order_by('-created_at')
    context = {
        'wallet' : wallet,
        'transactions' : transactions,
    } 
    return render(request, 'Users/wallet.html', context)

def add_funds(request):
    amount = Decimal(request.POST.get('amount', '0'))
    wallet = Wallet.objects.get(user = request.user)

    if amount > 0:
        wallet.balance += amount
        wallet.save()
        Transaction.objects.create(
            wallet = wallet,
            amount = amount,
            transaction_type = 'CREDIT',
            description = 'Added funds'
        )

        message = f"Successfullly added ₹{amount} to your wallet"
        success = True
    else:
        message = "Please enter a valid amount"
        success = False

    transactions = wallet.transactions.order_by('-created_at')
    transaction_list = render_to_string('Users/transaction-list.html', {'transactions' : transactions})

    return JsonResponse({
        'success' : success,
        'message' : message,
        'new_balance' : str(wallet.balance),
        'transaction_list' : transaction_list
    })

def withdraw_funds(request):
    amount = Decimal(request.POST.get('amount', '0'))
    wallet = Wallet.objects.get(user=request.user)
    
    if amount > 0 and amount <= wallet.balance:
        wallet.balance -= amount
        wallet.save()
        Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='DEBIT',
            description='Withdrawn funds'
        )
        message = f'Successfully withdrawn ₹{amount} from your wallet'
        success = True
    else:
        message = 'Invalid amount or insufficient funds.'
        success = False

    transactions = wallet.transactions.order_by('-created_at')
    transaction_list= render_to_string('Users/transaction-list.html', {'transactions': transactions})

    return JsonResponse({
        'success': success,
        'message': message,
        'new_balance': str(wallet.balance),
        'transaction_list': transaction_list
    })