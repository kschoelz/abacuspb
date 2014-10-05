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
    'bal_reconciled': 1021.61,
    'budget_monitored': True
}

db_account_2 = {
    'id': 'acct_toaccountname',
    'name': 'To Account Name',
    'type': 'Savings',
    'bank_name': 'Bank of Catonsville',
    'account_num': '0987654321',
    'bal_uncleared': 100.00,
    'bal_cleared': 100.00,
    'bal_reconciled': 200.00,
    'budget_monitored': False
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

transaction_transfer = {
    'date': '2014-08-10',
    'type': 'XFER',
    'payee': 'Move to Savings',
    'reconciled': '',
    'amount': -100.00,
    'memo': '',
    'cat_or_acct_id': 'acct_toaccountname'
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
        'reconciled': 'R',
        'amount': 1145.06,
        'memo': 'Sandy\'s Salary',
        'cat_or_acct_id': '1'
    },
    {
        'id': '53f69e77137a001e344259c8',
        'date': datetime(2014,8,1),
        'type': 'EFT',
        'payee': 'Costco',
        'reconciled': 'R',
        'amount': -123.45,
        'memo': 'Test transaction memo',
        'cat_or_acct_id': '2'
    },
    {
        'id': '53f69e77137a001e344259c9',
        'date': datetime(2014,8,6),
        'type': 'EFT',
        'payee': 'Exxon',
        'reconciled': 'C',
        'amount': -40.92,
        'memo': '',
        'cat_or_acct_id': '2'
    },
    {
        'id': '53f69e77137a001e344259ca',
        'date': datetime(2014,8,18),
        'type': 'DEP',
        'payee': 'U.S. Government',
        'reconciled': '',
        'amount': 2649.52,
        'memo': 'Kyle\'s Salary',
        'cat_or_acct_id': '1'
    },
    {
        'id': '53f69e77137a001e344259cb',
        'date': datetime(2014,8,12),
        'type': 'EFT',
        'payee': 'Amazon.com',
        'reconciled': '',
        'amount': -13.89,
        'memo': '',
        'cat_or_acct_id': '2'
    }
]

db_transfer_transactions_fromAcct= [
    {
        'id': '53f69e77137a001e344259c7',
        'date': datetime(2014,7,31),
        'type': 'XFER',
        'payee': 'To Savings',
        'reconciled': 'C',
        'amount': -100.00,
        'memo': '',
        'cat_or_acct_id': 'acct_toaccountname'
    }
]

db_transfer_transactions_toAcct= [
    {
        'id': '53f69e77137a001e344259c7',
        'date': datetime(2014,7,31),
        'type': 'XFER',
        'payee': 'To Savings',
        'reconciled': 'R',
        'amount': 100.00,
        'memo': '',
        'cat_or_acct_id': 'acct_testaccountname'
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

######################
# Category Test Data #
######################
category_1 = {
    'name': 'Tithe',
    'parent_id': None
}

category_2 = {
    'name': 'Gas & Electric',
    'parent_id': '1234567890'
}

category_put = { 'parent_id': '1234567890' }

db_categories = [
    {
        'id': '53f69e77137a001e344259f1',
        'name': 'Auto',
        'budget_tracked': False,
        'parent_id': None
    },
    {
        'id': '53f69e77137a001e344259fa',
        'name': 'Gas',
        'budget_tracked': True,
        'parent_id': '53f69e77137a001e344259f1' # Parent = Auto
    },
    {
        'id': '53f69e77137a001e344259fb',
        'name': 'Service',
        'budget_tracked': True,
        'parent_id': '53f69e77137a001e344259f1' # Parent = Auto
    },
    {
        'id': '53f69e77137a001e344259f2',
        'name': 'Dining & Entertainment',
        'budget_tracked': True,
        'parent_id': None
    },
    {
        'id': '53f69e77137a001e344259f3',
        'name': 'Tithe',
        'budget_tracked': True,
        'parent_id': None
    }
]