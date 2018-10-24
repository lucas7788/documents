"""
An Example of OEP-4
"""
from boa.interop.System.Storage import GetContext, Get, Put, Delete
from boa.interop.System.Runtime import Notify, CheckWitness
from boa.builtins import concat, ToScriptHash
ctx = GetContext()

NAME = 'X-Token'
SYMBOL = 'XToken'
DECIMAL = 8
FACTOR = 100000000
OWNER = ToScriptHash("ASYkgyWm4GFiXqVKZs6XrjaN3HnFVGRhDs")
TOTAL_AMOUNT = 1000000000
TRANSFER_PREFIX = bytearray(b'\x01')
APPROVE_PREFIX = bytearray(b'\x02 ')

SUPPLY_KEY = 'totoalSupply'


def Main(operation, args):
    """
    :param operation:
    :param args:
    :return:
    """
    if operation == 'name':
        return name()
    if operation == 'totalSupply':
        return totalSupply()
    if operation == 'init':
        return init()
    if operation == 'symbol':
        return symbol()
    if operation == 'transfer':
        if len(args) != 3:
            return False
        else:
            from_acct = args[0]
            to_acct = args[1]
            amount = args[2]
            return transfer(from_acct,to_acct,amount)
    if operation == 'transferMulti':
        return transferMulti(args)
    if operation == 'approve':
        if len(args) != 3:
            return False
        owner  = args[0]
        spender = args[1]
        amount = args[2]
        return approve(owner,spender,amount)
    if operation == 'transferFrom':
        if len(args) != 4:
            return False
        spender = args[0]
        from_acct = args[1]
        to_acct = args[2]
        amount = args[3]
        return transferFrom(spender,from_acct,to_acct,amount)
    if operation == 'balanceOf':
        if len(args) != 1:
            return False
        acct = args[0]
        return balanceOf(acct)
    if operation == 'decimals':
        return decimals()
    if operation == 'allowance':
        if len(args) != 2:
            return False;
        owner = args[0]
        spender = args[1]
        return allowance(owner,spender)


def name():
    return NAME


def totalSupply():
    return TOTAL_AMOUNT * FACTOR


def init():
    if Get(ctx,SUPPLY_KEY):
        Notify('Already initialized!')
        return False
    else:
        total = TOTAL_AMOUNT * FACTOR
        Put(ctx,SUPPLY_KEY,total)
        Put(ctx,concat(TRANSFER_PREFIX,OWNER),total)
        Notify(['transfer', '', OWNER, total])
        return True


def symbol():
    return SYMBOL


def transfer(from_acct,to_acct,amount):
    if from_acct == to_acct:
        return True
    if amount == 0:
        return True
    if amount < 0 :
        return False
    if CheckWitness(from_acct) == False:
        return False
    if len(to_acct) != 20:
        return False
    fromKey = concat(TRANSFER_PREFIX,from_acct)
    fromBalance = Get(ctx,fromKey)
    if fromBalance < amount:
        return False
    if fromBalance == amount:
        Delete(ctx,fromKey)
    else:
        Put(ctx,fromKey,fromBalance - amount)

    tokey = concat(TRANSFER_PREFIX,to_acct)
    toBalance = Get(ctx,tokey)

    Put(ctx,tokey,toBalance + amount)
    Notify(['transfer',from_acct,to_acct,amount])
    return True


def transferMulti(args):
    for p in args:
        if len(p) != 3:
            return False
        if transfer(p[0],p[1],p[2]) == False:
            # return False # this is wrong since the previous transaction will be successful
            raise Exception("TransferMulti failed.")
    return True


def approve(owner,spender,amount):
    if amount < 0 :
        return False
    if CheckWitness(owner) == False:
        return False
    if len(spender) != 20:
        return False
    key = concat(concat(APPROVE_PREFIX,owner),spender)
    allowance = Get(ctx, key)
    Put(ctx, key,amount + allowance)
    Notify(['approve', owner, spender, amount])
    return True


def transferFrom(spender,from_acct,to_acct,amount):
    if amount < 0 :
        return False
    if CheckWitness(spender) == False:
        return False
    if len(to_acct) != 20:
        return False
    appoveKey = concat(concat(APPROVE_PREFIX,from_acct),spender)
    approvedAmount = Get(ctx,appoveKey)
    if approvedAmount < amount:
        return False
    if approvedAmount == amount:
        Delete(ctx,appoveKey)
    else:
        Put(ctx,appoveKey,approvedAmount - amount)
    fromKey = concat(TRANSFER_PREFIX,from_acct)
    fromBalance = Get(ctx,fromKey)
    if fromBalance < amount:
        return False
    if fromBalance == amount:
        Delete(ctx,fromKey)
    else:
        Put(ctx,fromKey,fromBalance - amount)

    tokey = concat(TRANSFER_PREFIX,to_acct)
    toBalance = Get(ctx,tokey)

    Put(ctx,tokey,toBalance + amount)
    Notify(['transferfrom',spender, from_acct,to_acct,amount])
    return True


def balanceOf(account):
    return Get(ctx,concat(TRANSFER_PREFIX,account))


def decimals():
    return DECIMAL


def allowance(owner,spender):
    allowanceKey = concat(concat(APPROVE_PREFIX,owner),spender)
    return Get(ctx,allowanceKey)
