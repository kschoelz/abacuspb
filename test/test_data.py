from datetime import datetime
#####################
# Account Test Data #
#####################
account = {
    'name': 'Test Account Name',
    'type': 'Checking',
    'bank_name': 'Bank of Catonsville',
    'account_num': '1234567890'
}

account_put = {
    'name': 'Savings Account',
    'type': 'Savings'
}

db_account = {
    'id': 'acct_testaccountname',
    'name': 'Test Account Name',
    'type': 'Checking',
    'bank_name': 'Bank of Catonsville',
    'account_num': '1234567890',
    'bal_uncleared': 2635.63,
    'bal_cleared': -40.92,
    'bal_reconciled': 1021.61
}

#########################
# Transaction Test Data #
#########################
transaction = {
    'date': '2014-08-10',
    'type': 'EFT',
    'payee': 'Giant',
    # need: category/account, split -> consider fields.Nested
    'reconciled': '',
    'amount': -52.08,
    'memo': ''
}

transaction_put_amount = { # id = 53f69e77137a001e344259cb (Amazon.com) 
    'amount': -14.01,
    'memo': 'Birthday present'
}

transaction_put_reconciled = { # id = 53f69e77137a001e344259cb (Amazon.com)
    'reconciled': 'C'
}

transaction_put_amountreconciled = { # id = 53f69e77137a001e344259cb (Amazon.com)
    'amount': -14.01,
    'reconciled': 'C'
}

db_transactions= [
    {
        'id': '53f69e77137a001e344259c7',
        'date': datetime(2014,7,31),
        'type': 'DEP',
        'payee': 'Sandy Spring Bank',
        # need: category/account, split -> consider fields.Nested
        'reconciled': 'R',
        'amount': 1145.06,
        'memo': 'Sandy\'s Salary'
    },
    {
        'id': '53f69e77137a001e344259c8',
        'date': datetime(2014,8,1),
        'type': 'EFT',
        'payee': 'Costco',
        # need: category/account, split -> consider fields.Nested
        'reconciled': 'R',
        'amount': -123.45,
        'memo': 'Test transaction memo'
    },
    {
        'id': '53f69e77137a001e344259c9',
        'date': datetime(2014,8,6),
        'type': 'EFT',
        'payee': 'Exxon',
        # need: category/account, split -> consider fields.Nested
        'reconciled': 'C',
        'amount': -40.92,
        'memo': ''
    },
    {
        'id': '53f69e77137a001e344259ca',
        'date': datetime(2014,8,18),
        'type': 'DEP',
        'payee': 'U.S. Government',
        # need: category/account, split -> consider fields.Nested
        'reconciled': '',
        'amount': 2649.52,
        'memo': 'Kyle\'s Salary'
    },
    {
        'id': '53f69e77137a001e344259cb',
        'date': datetime(2014,8,12),
        'type': 'EFT',
        'payee': 'Amazon.com',
        # need: category/account, split -> consider fields.Nested
        'reconciled': '',
        'amount': -13.89,
        'memo': ''
    }
]

###################
# Payee Test Data #
###################
payee = { 'name': 'Costco' }

payee_put = { 'name': 'Newegg.com' }

db_payees = [
    {
        'id': '53f69e77137a001e344259f1',
        'name': 'Costco'
    },
    {
        'id': '53f69e77137a001e344259f2',
        'name': 'Amazon.com'
    },
    {
        'id': '53f69e77137a001e344259f3',
        'name': 'U.S. Government'
    },
    {
        'id': '53f69e77137a001e344259f4',
        'name': 'Exxon'
    },
    {
        'id': '53f69e77137a001e344259f5',
        'name': 'Sandy Spring Bank'
    }
]