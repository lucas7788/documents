"""
NBA Guess Contract
"""

from boa.interop.System.Storage import GetContext, Get, Put, Delete
from boa.interop.System.Runtime import CheckWitness, GetTime, Notify, Serialize, Deserialize, Log
from boa.interop.System.Action import RegisterAction
from boa.builtins import concat, ToScriptHash, range,state
from boa.interop.System.App import RegisterAppCall
from boa.interop.Ontology.Native import Invoke
from boa.interop.System.ExecutionEngine import GetExecutingScriptHash

BetEvent = RegisterAction("placebet", "address", "gameid","horv", "amount")

oracleContract = RegisterAppCall('a6ceb31d2f4694eb5dc049d518828c3c06e050ca', 'operation', 'args')
ctx = GetContext()
selfAddr = GetExecutingScriptHash()
adminAddress = ToScriptHash("Ad4pjz2bqep4RhQrUAzMuZJkBC3qJ1tZuT")
operaterAddress = ToScriptHash("AS3SCXw8GKTEeXpdwVw7EcC4rqSebFYpfb")

# 5% fee cost
FeeRate = 5
Name = "NBA Guess"
#keys
GameCountPrefix = 'GameCount'
GamePrefix = 'Game'
BetPrefix = 'Bet'
OraclePrefix = 'Oracle'
OracleResPrefix = 'OracleRes'
AccountPrefix = 'Account'
EndPrefix = 'EndBet'
FeePoolPrefix = 'FeePool'

GameID = 'GameID'
HTeamID = 'HTeamID'
HTeamScore = 'HTeamScore'
VTeamID = 'VTeamID'
VTeamScore = 'VTeamScore'
Finished = 'Finished'
BetEnd = 'BetEnd'
HomeList = 'HomeList'
VistorList = 'VistorList'

def Main(operation, args):
    if operation == 'getMatchByDate':
        if len(args) != 1:
            return False
        return getMatchByDate(args[0])
    if operation == 'placeBet':
        if len(args) != 4:
            return False
        return  placeBet(args[0],args[1],args[2],args[3])   
    if operation == 'endBet':
        if len(args) != 1:
            return False
        return endBet(args[0])    
    if operation == 'inputMatch':
        if len(args) != 4:
            return False
        return inputMatch(args[0],args[1],args[2],args[3])    
    if operation == 'callOracle':
        if len(args) != 1:
            return False
        return callOracle(args[0])  
    if operation == 'name':
        return name();    
    if operation == 'setResult':
        if len(args) != 1:
            return False
        return setResult(args[0])    
    if operation == 'manualSetResult':
        if len(args) != 5:
            return False 
        return manualSetResult(args[0],args[1],args[2],args[3],args[4])   
    if operation == 'queryAccountBalance':
        if len(args)!= 1:
            return False
        return queryAccountBalance(args[0])
    if operation == 'withdraw':
        if len(args)!= 2:
            return False
        return withdraw(args[0],args[1])    
    return False    


def name():
    return Name

def getMatchByDate(date):
    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)

    res = ''
    if (gameCount > 0):
        for i in range(1 , gameCount+1):
            gk = _concatKey(_concatKey(GamePrefix,date),i)    
            gamei = Get(ctx,gk)
            gameMap = Deserialize(gamei)
            gameid = gameMap[GameID]
            hteamid = gameMap[HTeamID]
            hteamScore = gameMap[HTeamScore]
            vteamid = gameMap[VTeamID]
            vteamScore = gameMap[VTeamScore]
            tmp = _concatStrs([gameid,hteamid,hteamScore,vteamid,vteamScore],',')
            if i == 1:
                res = tmp
            else:
                res = _concatKey(res,tmp)

    return res


def placeBet(address,gameID, HorV, amount):
    _require(amount > 0)
    key = _concatKey(BetPrefix,gameID)
    game = Get(ctx,key)
    _require(game)
    gameMap = Deserialize(game)

    if gameMap[BetEnd] == True:
        return False
    if gameMap[Finished] == True:
        return False

    _require(_transferONG(address,selfAddr,amount))

    listkey = HomeList
    if HorV == 'V':
        listkey = VistorList
        gameMap['VisitorTotal'] = gameMap['VisitorTotal'] + amount
    else:
        gameMap['HomeTotal'] = gameMap['HomeTotal'] + amount    

    betmap = gameMap[listkey]
    betinfo = {'address':address, 'amount':amount}
    if len(betmap) == 0:
        gameMap[listkey] = [betinfo]
    else:  
        gameMap[listkey].append(betinfo)
    
    Put(ctx, key, Serialize(gameMap))

    BetEvent(address,gameID,HorV,amount)
    return True


def endBet(date):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))
    ekey = _concatKey(EndPrefix,date)
    end = Get(ctx,ekey)
    if end == True:
        return False

    gameCount = Get(ctx, _concatKey(GameCountPrefix, date))
    for i in range(1 , gameCount+1):
        gk = _concatKey(_concatKey(GamePrefix,date),i)    
        gamei = Get(ctx,gk)
        gameMap = Deserialize(gamei)
        gameid = gameMap[GameID]

        betKey = _concatKey(BetPrefix,gameid)
        betgame = Get(ctx,betKey)
        betgameMap = Deserialize(betgame)
        betgameMap[BetEnd] = True

        Put(ctx,betKey,Serialize(betgameMap))

    Put(ctx, ekey, True)
    return True


def inputMatch( date, gameID, hTeamID, vTeamID):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))
    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)
    if not gameCount:
        gameCount = 0


    if gameCount > 0:
        for i in range(1 , gameCount+1):
            tmpgk = _concatKey(_concatKey(GamePrefix,date),i)    
            tmpGame = Deserialize(Get(ctx, tmpgk))
            if tmpGame['GameID'] == gameID:
                return False

    Put(ctx, gck, gameCount+1)    
    gk = _concatKey(_concatKey(GamePrefix,date),gameCount+1)    

    game = {'GameID':gameID,'HTeamID':hTeamID,'HTeamScore':'0','VTeamID':vTeamID,'VTeamScore':'0'}
    Put(ctx,gk,Serialize(game))

    betKey = _concatKey(BetPrefix,gameID)
    bet = {'BetEnd':False,'Finished':False,'HomeList':[],'VistorList':[],'HomeTotal':0,'VisitorTotal':0}

    Put(ctx,betKey,Serialize(bet))
    return True


def callOracle(date):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))

    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)

    url = concat(concat('"http://data.nba.net/prod/v2/"',date),'/scoreboard.json"')

    reqtmp =  """{
		"scheduler":{
			"type": "runAfter",
			"params": "2018-06-15 08:37:18"
		},
		"tasks":[
			{
			  "type": "httpGet",
			  "params": {
				"url":"""

    reqhead = concat(concat(reqtmp,url),"""}},""")
    bodyhead = """{"type":"jsonParse","params":{"data":[ """

    tmpbody = []
    for i in range(0,gameCount):
        s1 = concat(concat("""{"type":"String","path":["games",""", concat(concat('"',i),'"')),""","gameId"]}""")
        s2 = concat(concat("""{"type":"String","path":["games",""", concat(concat('"',i),'"')),""","hTeam","teamId]}""")
        s3 = concat(concat("""{"type":"String","path":["games",""", concat(concat('"',i),'"')),""","hTeam","score]}""")
        s4 = concat(concat("""{"type":"String","path":["games",""", concat(concat('"',i),'"')),""","vTeam","teamId]}""")
        s5 = concat(concat("""{"type":"String","path":["games",""", concat(concat('"',i),'"')),""","vTeam","score]}""")
        tmpbody.append(_concatStrs([s1,s2,s3,s4,s5],','))
    body = _concatStrs(tmpbody,',')

    bodytail = """]}}]}"""
    req = concat(concat(concat(reqhead,bodyhead),body),bodytail)

    key = _concatKey(OraclePrefix,date)
    txhash = GetExecutingScriptHash()
    Put(ctx, key, txhash)
    oracleContract('CreateOracleRequest',[req,txhash])
    return True

def setResult(date):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))

    reskey = _concatKey(OracleResPrefix,date)
    if Get(ctx, reskey):
        return False

    key = _concatKey(OraclePrefix,date)
    txhash = Get(ctx, key)

    res = oracleContract('GetOracleOutcome',[txhash])
    if not res:
        return False
    a = Deserialize(res)
    b = Deserialize(a[0])

    gck = _concatKey(GameCountPrefix, date)
    gameCount = Get(ctx, gck)

    for i in range(0, gameCount):
        gk = _concatKey(_concatKey(GamePrefix,date),i+1)    
        gameMap = Deserialize(Get(ctx, gk))

        gameid = gameMap[GameID]

        #check the same gameid
        resGid = b[i*5+0]
        if resGid != gameid:
            return False

        resHid = b[i*5+1]
        resHscore = b[i*5+2]
        resVid = b[i*5+3]
        resVscore = b[i*5+4]

        if (resHid != gameMap[HTeamID]) or (resVid != gameMap[VTeamID]):
            return False

        hscore = resHscore 
        vscore = resVscore

        #analyz from oracle response
        gameMap[HTeamScore] = hscore   
        gameMap[VTeamScore] = vscore

        Put(ctx,gk,Serialize(gameMap))

        #update the bet
        betKey = _concatKey(BetPrefix,gameid)
        betmap = Deserialize(Get(ctx,betKey))

        winnerkey = HomeList
        betinfos = betmap[winnerkey]
        winnerBets = betmap['HomeTotal']
        if hscore < vscore:
            winnerkey = VistorList
            winnerBets = betmap['VisitorTotal']
        betmap[Finished] = True
        
        totalBets = betmap['HomeTotal'] + betmap['VisitorTotal']
        _distributeRewards(totalBets, winnerBets,betinfos)

    return True


def manualSetResult(date,index,gameid,hscore,vscore):
    _require(CheckWitness(operaterAddress) or CheckWitness(adminAddress))
     #update the bet
    betKey = _concatKey(BetPrefix,gameid)
    betmap = Deserialize(Get(ctx,betKey))
    if betmap[Finished]==True:
        return False
    gk = _concatKey(_concatKey(GamePrefix,date),index)    
    gameMap = Deserialize(Get(ctx, gk))
    _require(gameid == gameMap[GameID])
    gameMap[HTeamScore] = hscore
    gameMap[VTeamScore] = vscore
    Put(ctx,gk,Serialize(gameMap))
    winnerkey = HomeList
    betinfos = betmap[winnerkey]
    winnerBets = betmap['HomeTotal']
    if hscore < vscore:
        winnerkey = VistorList
        winnerBets = betmap['VisitorTotal']
    betmap[Finished] = True
    
    totalBets = betmap['HomeTotal'] + betmap['VisitorTotal']
    _distributeRewards(totalBets, winnerBets,betinfos)
    Put(ctx,betKey,Serialize(betmap))
    return True

def queryAccountBalance(address):
    key = _concatKey(AccountPrefix,address)
    return Get(ctx,key)


def withdraw(address, amount):
    _require(CheckWitness(address))
    _require(amount > 0)
    key = _concatKey(AccountPrefix,address)
    balance = Get(ctx,key)
    _require(balance >= amount )
    if balance == amount:
        Delete(ctx,key)
    else:      
        Put(ctx,key,balance - amount)    
    _require(_transferONGFromContract(address,amount))
    return True

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
    _require(amount > 0)
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
    _require(amount > 0)
    param = state(selfAddr, toacct, amount)
    res = Invoke(0, contractAddress, 'transfer', [param])

    if res and res == b'\x01':
        return True
    else:
        return False

def _distributeRewards(totalBets,winnerBets,betinfos):
    count = 0
    for betinfo in betinfos:
        address = betinfo['address']
        amount = betinfo['amount']
        key = _concatKey(AccountPrefix, address)
        balance = Get(ctx, key)
        benefit = amount  * totalBets * (100 - FeeRate) / (100 * winnerBets) 
        Put(ctx, key ,balance + benefit)
        count = count + benefit
    if count > 0:
        balance = Get(ctx,FeePoolPrefix)
        Put(ctx,FeePoolPrefix,balance + totalBets - count)
    return True
