"""
NBA Guess Contract
"""

from boa.interop.System.Storage import GetContext, Get, Put, Delete
from boa.interop.System.Runtime import CheckWitness, GetTime, Notify, Serialize, Deserialize
from boa.interop.System.Action import RegisterAction
from boa.builtins import concat, ToScriptHash, range,state, append
from boa.interop.System.App import RegisterAppCall
from boa.interop.Ontology.Native import Invoke
from boa.interop.System.ExecutionEngine import GetExecutingScriptHash

BetEvent = RegisterAction("placebet", "address", "gameid","horv", "amount")
# ApprovalEvent = RegisterAction("approval", "owner", "spender", "amount")

oracleContract = RegisterAppCall('a6ceb31d2f4694eb5dc049d518828c3c06e050ca', 'operation', 'args')
ctx = GetContext()
selfAddr = GetExecutingScriptHash()
adminAddress = ""
operaterAddress = ""

#keys
GameCountPrefix = 'GameCount'
GamePrefix = 'Game'
BetPrefix = 'Bet'
OraclePrefix = 'Oracle'
OracleResPrefix = 'OracleRes'

GameID = 'GameID'
HTeamID = 'HTeamID'
HTeamScore = 'HTeamScore'
VTeamID = 'VTeamID'
VTeamScore = 'VTeamScore'
Finished = 'Finished'
BetEnd = 'BetEnd'
HomeList = 'HomeList'
VistorList = 'VistorList'

def main(operation, args):
    if operation == 'GetMatchByDate':
        if len(args) != 1:
            return False
        return GetMatchByDate(args[0])
    if operation == 'PlaceBet':
        if len(args) != 4:
            return False
        return  PlaceBet(args[0],args[1],args[2],args[3])   
    if operation == 'EndBet':
        if len(args) != 1:
            return False
        return EndBet(args[0])    
    if operation == 'InputMatch':
        if len(args) != 4:
            return False
        return InputMatch(args[0],args[1],args[2],args[3])    
    if operation == 'CallOracle':
        if len(args) != 1:
            return False
        return CallOracle(args[0])  

    if operation == 'SetResult':
        if len(args) != 1:
            return False
        return SetResult(args[0])    
    return False    


def GetMatchByDate(date):
    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)

    gk1 = _concatKey(_concatKey(GamePrefix,date),1)    
    game1 = Get(ctx,gk1)
    gameMap1 = Deserialize(game1)
    gameid1 = gameMap1[GameID]
    hteamid1 = gameMap1[HTeamID]
    hteamScore1 = gameMap1[HTeamScore]
    vteamid1 = gameMap1[VTeamID]
    vteamScore1 = gameMap1[VTeamScore]
    res = _concatStrs([gameid1,hteamid1,hteamScore1,vteamid1,vteamScore1],',')

    for i in range(2 , gameCount):gameid
        gk = _concatKey(_concatKeygameid),i)    
        gamei = Get(ctx,gk)
        gameMap = Deserialize(gamegameid
        gameid = gameMap[GameID]
        hteamid = gameMap[HTeamID]
        hteamScore = gameMap[HTeamScore]
        vteamid = gameMap[VTeamID]
        vteamScore = gameMap[VTeamScore]
        tmp = _concatStrs([gameid,hteamid,hteamScore,vteamid,vteamScore],',')
        res = _concatKey(res,tmp)

    return res


def PlaceBet(address,gameID, HorV, amount):
    key = _concatKey(BetPrefix,gameID)
    game = Get(ctx,key)
    _require(game)
    gameMap = Deserialize(game)
    _require(gameMap[BetEnd] == False)
    _require(gameMap[Finished] == False)
    _require(_transferONG(address,selfAddr,amount))

    listkey = HomeList
    if HorV == 'V':
        listkey = VistorList


    betmap = gameMap[listkey]
    if not betmap:
        betinfo = {'address':address, 'amount':amount}
        gameMap[listkey] = betinfo
    else:
        betinfo = gameMap[listkey]
        if not betinfo[address]:
            betinfo[address] = amount
        else:
            betinfo[address] = betinfo[address] + amount   
        gameMap[listkey] = betinfo
    Put(ctx, key, Serialize(gameMap))

    BetEvent(address,gameID,HorV,amount)
    return True


def EndBet(date):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))
    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)
    for i in range(1 , gameCount):
        gk = _concatKey(_concatKey(GamePrefix,date),i)    
        gamei = Get(ctx,gk)
        gameMap = Deserialize(gamei)
        gameid = gameMap[GameID]

        betKey = _concatKey(BetPrefix,gameid)
        betgame = Get(ctx,betKey)
        betgameMap = Deserialize(betgame)
        betgameMap[BetEnd] = True

        Put(ctx,gk,Serialize(betgameMap))

    return True


def InputMatch( date, gameID, hTeamID, vTeamID):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))
    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)
    if not gameCount:
        gameCount = 0
    Put(ctx, gck, gameCount+1)    
    gk = _concatKey(_concatKey(GamePrefix,date),gameCount+1)    

    game = {'GameID':gameID,'HTeamID':hTeamID,'HTeamScore':0,'VTeamID':vTeamID,'VTeamScore':0}
    Put(ctx,gk,Serialize(game))

    betKey = _concatKey(BetPrefix,gameID)
    bet = {'BetEnd':False,'Finished':False}

    Put(ctx,betKey,Serialize(bet))
    return True


def CallOracle(date):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))

    req = """ ???"""

    key = _concatKey(OraclePrefix,date)
    txhash = GetExecutingScriptHash()
    Put(ctx, key, txhash)
    oracleContract('CreateOracleRequest',[req,txhash])
    return True

def SetResult(date):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))

    reskey = _concatKey(OracleResPrefix,date)
    if Get(ctx, reskey):
        return False

    key = _concatKey(OraclePrefix,date)
    txhash = Get(ctx, key)

    res = oracleContract('GetOracleOutcome',[txhash])
    if not res:
        return False
    # a = Deserialize(res)
    # b = Deserialize(a[0])

    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)

    for i in range(1, gameCount):
        gk = _concatKey(_concatKey(GamePrefix,date),i)    
        gameMap = Deserialize(Get(ctx, gk))

        gameid = gameMap[GameID]

        #check the same gameid
        hscore = 100+i 
        vscore = 90 + i*2

        #analyz from oracle response
        gameMap[HTeamScore] = hscore   
        gameMap[VTeamScore] = vscore

        Put(ctx,gk,Serialize(gameMap))

        #update the bet
        betKey = _concatKey(BetPrefix,gameid)
        betmap = Deserialize(Get(ctx,betKey))

        winnerkey = HomeList
        if hscore < vscore:
            winnerkey = VistorList
        betmap[Finished] = True
        
        betinfo = betmap[winnerkey]




def _require(regx):
    if not regx:
        raise Exception('Error')


def _concatKey(str1, str2):
    return concat(concat(str1, '_'),str2)
    

def _concatStrs(strarr,spliter):
    res = strarr[0]
    for i in range (1, len(strarr)):
        res = concat(concat(res, spliter),strarr[i])
    return res



def _transferONG(fromacct, toacct, amount):
    """
    transfer ONT
    :param fromacct:
    :param toacct:
    :param amount:
    :return:
    """
    # ONT native contract address
    contractAddress = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02')

    if CheckWitness(fromacct):
        param = state(fromacct, toacct, amount)
        res = Invoke(0, contractAddress, 'transfer', [param])

        if res and res == b'\x01':
            return True
        else:
            return False

    else:
        return False


def _transferONGFromContract(toacct, amount):
    """
    transfer ONT from contract
    :param fromacct:
    :param toacct:
    :param amount:
    :return:
    """
    # ONT native contract address
    contractAddress = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02')

    param = state(selfAddr, toacct, amount)
    res = Invoke(0, contractAddress, 'transfer', [param])

    if res and res == b'\x01':
        return True
    else:
        return False
