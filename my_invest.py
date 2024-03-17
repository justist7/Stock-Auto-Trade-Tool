import glob
import os
from os import access
import requests
import json
import time
import math
import numpy as np
from datetime import datetime, timedelta
import pandas as pd


jongTarget = [
    { 'num':	1	,'iscd':'004410', 'name':'서울식품' },
    { 'num':	2	,'iscd':'003560', 'name':'IHQ'}]
   

def writeFile(fileName, data):
    f = open(fileName, 'w')
    f.write(json.dumps(data))
    f.close()

dtNow = datetime.now()
print('dtNow:', dtNow)
dtNowStr = str(dtNow.date()).replace('-','')
print('dtNowStr:', dtNowStr)
dtEnd = str(dtNow.date()).replace('-','')
dtStart = dtNow + timedelta(days=-90)
dtStart = str(dtStart.date()).replace('-','')

#mode = ''
mode = 'real_'

jong = []
order = []
url = 'https://openapi.koreainvestment.com:9443'

def readAccounts():
    txt_files = glob.glob('accounts/*.txt')
    accounts = dict()

    for txt_file in txt_files:
        acntName = os.path.basename(os.path.abspath(txt_file))[:-4]
        file = open(txt_file, 'r')
        lines = file.read().split('\n')
        file.close()
        accounts[acntName] = lines

    for acntName in accounts.keys():
        if os.path.isfile(acntName+'.json'):
            with open(acntName+'.json', 'r') as file:
                res = json.load(file)
                expire_time = datetime.strptime(res['access_token_token_expired'], '%Y-%m-%d %H:%M:%S')
                if (expire_time - dtNow).total_seconds() > 18*60*60:
                    accounts[acntName].append(res['access_token'])
                    continue

        appKey = accounts[acntName][1]
        appSecret = accounts[acntName][2]

        headers = { "content-type":"application/json",
        'appKey': appKey,
        'appSecret': appSecret}

        body = {"grant_type":"client_credentials",
                "appkey":appKey, 
                "appsecret":appSecret}

        sendUrl = url + '/oauth2/tokenP'
        res = requests.post(sendUrl, headers=headers, data=json.dumps(body))
        print(acntName)
        print('access_token msg')
        print(res.json())
        accessToken = res.json()['access_token']
        accounts[acntName].append(accessToken)
        with open(acntName+'.json', 'w') as file:
            json.dump(res.json(), file)

    return accounts

print(dtStart + '~' + dtEnd)

accounts = readAccounts()

def sendAccounts():
    return accounts

# HashKey
def getHashKey(acntName, datas):
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    sendUrl = url + '/uapi/hashkey'
    headers = { 
        "content-type":"application/json",
        'appKey': appKey,
        'appSecret': appSecret,
        }
    res = requests.post(sendUrl, headers=headers, data=json.dumps(datas))
    hashKey = res.json()['HASH']
    return hashKey

def getAcntList(acntName, CTX_AREA_FK100='', CTX_AREA_NK100=''):
    print("잔고조회##############")
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    headersDaily = { 
        "content-type":"application/json",
        'appKey': appKey,
        'appSecret': appSecret,
        'authorization': 'Bearer ' + accessToken,
        'tr_id':'TTTC8434R',
        'tr_cont':'',
        'custtype':'P',
        'hashkey': hashKey
        #'mac_address':macAddress

        }
    params = {
        'CANO':acntNo,
        'ACNT_PRDT_CD':'01',
        'AFHR_FLPR_YN':'N',
        'OFL_YN':'',
        'INQR_DVSN':'02',
        'UNPR_DVSN':'01',
        'FUND_STTL_ICLD_YN':'N',
        'FNCG_AMT_AUTO_RDPT_YN':'N',
        'PRCS_DVSN':'00',
        'CTX_AREA_FK100':CTX_AREA_FK100,
        'CTX_AREA_NK100':CTX_AREA_NK100
    }
    sendUrl = url +'/uapi/domestic-stock/v1/trading/inquire-balance'
    res = requests.get(sendUrl, headers=headersDaily, params=params)
    return res

# 일자별시세 --------------------------------------
def getDays30(acntName, iscd):
    print("일자별시세###################")
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    headersDaily = { 
        "content-type":"application/json",
        'appKey': appKey,
        'appSecret': appSecret,
        'authorization': 'Bearer ' + accessToken,
        'tr_id':'FHKST01010400',
        'tr_cont':'',
        'custtype':'P',
        }
    params = {
        'FID_COND_MRKT_DIV_CODE':'J',
        'FID_INPUT_ISCD': iscd,
        'FID_ORG_ADJ_PRC':'0',
        'FID_PERIOD_DIV_CODE':'D'
    }
    sendUrl = url +'/uapi/domestic-stock/v1/quotations/inquire-daily-price'
    res = requests.get(sendUrl, headers=headersDaily, params=params)
    return res

def getCancelableOrder(acntName, INQR_STRT_DT=dtNowStr, INQR_END_DT=dtNowStr, PDNO='', CCLD_DVSN='00'):
    print("주문체결조회###################")
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    headers = {
        "content-type":"application/json",
        'authorization': 'Bearer ' + accessToken,
        'appKey': appKey,
        'appSecret': appSecret,
        'tr_id':'TTTC8036R',
        }
    params = {
        'CANO': acntNo,
        'ACNT_PRDT_CD': '01',
        'CTX_AREA_FK100': '',
        'CTX_AREA_NK100': '',
        'INQR_DVSN_1': '0', #조회구분1 - 0: 조회순서, 1: 주문순, 2: 종목순
        'INQR_DVSN_2': '0', #조회구분2 - 0: 전체, 1: 매도, 2: 매수
        }
    sendUrl = url + '/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl'
    res = requests.get(sendUrl, headers=headers, params=params)
    return res

def getExecutedOrder(acntName, tr_cont = '', CTX_AREA_FK100 = '', CTX_AREA_NK100 = '', INQR_STRT_DT=dtNowStr, INQR_END_DT=dtNowStr, PDNO='', CCLD_DVSN='00'):
    print("주문체결조회###################")
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    headers = {
        "content-type":"application/json",
        'authorization': 'Bearer ' + accessToken,
        'appKey': appKey,
        'appSecret': appSecret,
        'tr_id':'TTTC8001R',
        'tr_cont': tr_cont,
        }
    params = {
        'CANO': acntNo,
        'ACNT_PRDT_CD': '01',
        'INQR_STRT_DT': INQR_STRT_DT, #조회시작일자 YYYYMMDD
        'INQR_END_DT': INQR_END_DT, #조회종료일자 YYYYMMDD
        'SLL_BUY_DVSN_CD': '00', #00: 전체, 01:매도, 02:매수
        'INQR_DVSN': '00', #00:역순, 01:정순
        'PDNO': PDNO, #종목번호 6자리, 공란: 전체 조회
        'CCLD_DVSN': CCLD_DVSN, #00: 전체, 01: 체결, 02: 미체결
        'ORD_GNO_BRNO': '',
        'ODNO': '',
        'INQR_DVSN_3': '00', #00: 전체, 01: 현금, 02: 융자, 03:대출, 04:대주
        'INQR_DVSN_1': '',
        'CTX_AREA_FK100': CTX_AREA_FK100,
        'CTX_AREA_NK100': CTX_AREA_NK100,
        }
    sendUrl = url + '/uapi/domestic-stock/v1/trading/inquire-daily-ccld'
    res = requests.get(sendUrl, headers=headers, params=params)
    return res

def postPreorder(acntName, SLL_BUY_DVSN_CD, PDNO, ORD_QTY, ORD_UNPR, ORD_DVSN_CD='01', ORD_OBJT_CBLC_DVSN_CD='10', LOAN_DT='', RSVN_ORD_END_DT='', LDNG_DT=''):
    print("주식예약주문###################")
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    params={
        'CANO': acntNo,
        'ACNT_PRDT_CD': '01',
        'PDNO': PDNO, #종목번호 6자리
        'ORD_QTY': ORD_QTY, #주문 수량
        'ORD_UNPR': ORD_UNPR, #주문 단가 (시장가의 경우 '0' 으로 입력)
        'SLL_BUY_DVSN_CD': SLL_BUY_DVSN_CD, #01: 매도, 02: 매수
        'ORD_DVSN_CD': ORD_DVSN_CD, #01: 지정가, 02: 시장가, 02: 조건부지정가, 05: 장전 시간외
        'ORD_OBJT_CBLC_DVSN_CD': ORD_OBJT_CBLC_DVSN_CD, #10:현금
        'LOAN_DT': LOAN_DT, #대출일자 YYYYMMDD
        'RSVN_ORD_END_DT': RSVN_ORD_END_DT, #예약주문종료일자 YYYYMMDD 현재 일자 이후로 설정. 미입력시 다음날 주문처리후 종료. 입력 시 최대 30일 이후까지 가능
        'LDNG_DT': LDNG_DT, #대여일자
        }
    headers={
        "content-type":"application/json",
        'authorization': 'Bearer ' + accessToken,
        'appKey': appKey,
        'appSecret': appSecret,
        #'hashKey': getHashKey(acntName, params),
        'tr_id':'CTSC0008U',
        }
    
    sendUrl = url + '/uapi/domestic-stock/v1/trading/order-resv'
    res = requests.post(sendUrl, headers=headers, data=json.dumps(params))
    return res

def postOrder(acntName, SLL_BUY_DVSN_CD, PDNO, ORD_QTY, ORD_UNPR, ORD_DVSN='00'):
    print("주식주문####################")
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    params={
        'CANO': acntNo,
        'ACNT_PRDT_CD': '01',
        'PDNO': PDNO, #종목번호 6자리
        'ORD_DVSN': ORD_DVSN, #00:지정가 01:시장가
        'ORD_QTY': ORD_QTY, #주문수량
        'ORD_UNPR': ORD_UNPR, #주문단가
        }
    headers={
        "content-type":"application/json",
        'authorization': 'Bearer ' + accessToken,
        'appKey': appKey,
        'appSecret': appSecret,
        #'hashKey': getHashKey(acntName, params),
        'tr_id':'TTTC08'+SLL_BUY_DVSN_CD+'U', #01: 매도, 02:매수
        }
    
    sendUrl = url + '/uapi/domestic-stock/v1/trading/order-cash'
    res = requests.post(sendUrl, headers=headers, data=json.dumps(params))
    print('res')
    return res

def getAllOrders(CCLD_DVSN='00'):
    data = dict()
    for acntName in accounts.keys():
        tr_cont = ''
        CTX_AREA_FK100 = ''
        CTX_AREA_NK100 = ''

        while True:
            res = getExecutedOrder(acntName=acntName, tr_cont=tr_cont, CTX_AREA_FK100=CTX_AREA_FK100, CTX_AREA_NK100= CTX_AREA_NK100, CCLD_DVSN=CCLD_DVSN)
            tr_cont = res.headers['tr_cont']
            output = res.json()

            if tr_cont =='M' or tr_cont == 'F':
                CTX_AREA_FK100 = output['ctx_area_fk100']
                CTX_AREA_NK100 = output['ctx_area_nk100']

            for order in output['output1']:
                #ord_dt: 주문일자, ord_gno_brno:주문채번지점번호, odno: 주문번호
                comp_odno = order['ord_dt']+order['ord_gno_brno']+order['odno']
                order_ccld = True if order['rmn_qty'] == '0' else False
                order['comp_odno'] = comp_odno
                order['acntName'] = acntName
                order['order_ccld'] = order_ccld
                #['계좌',  '주문번호',  '종목명', '종목번호',          '매도/매수',   '호가', '주문 수량',  '체결 수량', '체결 완료여부', '취소 여부']
                #[acntName, comp_odno, prdt_name,  pdno,      sll_buy_dvsn_cd_name, ord_unpr,     ord_qty, tot_ccld_qty,      order_ccld,    cncl_yn']
                comp_key = comp_odno
                data[comp_key] = order

            if tr_cont =='D' or tr_cont == 'E':
                break

    return data

def postCancelOrder(acntName, KRX_FWDG_ORD_ORGNO, ORGN_ODNO, ORD_DVSN='00', RVSE_CNCL_DVSN_CD='02', ORD_QTY='0', ORD_UNPR='0', QTY_ALL_ORD_YN='Y'):
    print("주식주문취소####################")
    acntNo, appKey, appSecret, accessToken = accounts[acntName]
    params={
        'CANO': acntNo,
        'ACNT_PRDT_CD': '01',
        'KRX_FWDG_ORD_ORGNO': KRX_FWDG_ORD_ORGNO, #한국거래소전송주문조직번호
        'ORGN_ODNO': ORGN_ODNO, #원주문번호/ 주식일별주문체결조회 API output1의 odno(주문번호) 값 입력
        'ORD_DVSN': ORD_DVSN, #주문구분/ 00: 지정가, 01:시장가, ...
        'RVSE_CNCL_DVSN_CD': RVSE_CNCL_DVSN_CD, #정정취소구분코드/ 정정:01, 취소: 02
        'ORD_QTY': ORD_QTY, #주문수량/ 잔량전부 취소/정정시 '0'설정, QTY_ALL_ORD_YN=Y 설정
        'ORD_UNPR': ORD_UNPR, #주문단가/ 취소시 '0'설정
        'QTY_ALL_ORD_YN': QTY_ALL_ORD_YN, #잔량전부주문여부/ 잔량전부: 'Y', 잔량일부: 'N'
        }
    headers={
        "content-type":"application/json",
        'authorization': 'Bearer ' + accessToken,
        'appKey': appKey,
        'appSecret': appSecret,
        #'hashKey': getHashKey(acntName, params),
        'tr_id':'TTTC0803U',
        }
    
    sendUrl = url + '/uapi/domestic-stock/v1/trading/order-rvsecncl'
    res = requests.post(sendUrl, headers=headers, data=json.dumps(params))
    return res

def initAutoTrade(auto_info): #std_price, deviation : string
    new_comp_odno_set = []
    for form in ['sell', 'buy']:
        acntName = auto_info[form+'_acntName']
        if acntName != '':
            SLL_BUY_DVSN_CD = '01' if form =='sell' else '02'
            PDNO = auto_info['product_number']
            ORD_QTY = auto_info[form+'_quantity']
            ORD_UNPR = str(int(float(auto_info['std_price']) + float(auto_info['deviation']))) if form == 'sell' else str(int(float(auto_info['std_price']) - float(auto_info['deviation'])))
            res = postOrder(acntName, SLL_BUY_DVSN_CD, PDNO, ORD_QTY, ORD_UNPR)
            try:
                output = res.json()['output']
            except: print(res.json())
            new_comp_odno = dtNowStr+output['KRX_FWDG_ORD_ORGNO']+output['ODNO']
            new_comp_odno_set.append(new_comp_odno)
        else:
            new_comp_odno_set.append('')


    return new_comp_odno_set

def autoTradeStates(comp_odno_sets, data):
    order_states = []
    for index, comp_odno_set in enumerate(comp_odno_sets):
        order_state = [None, None] #True: 체결, False: 미체결, None: 취소/미주문
        for sub_index, comp_odno in enumerate(comp_odno_set):
            comp_key = comp_odno
            if comp_key != '':
                order = data[comp_key]
                order_state[sub_index] = order['order_ccld']
                if order['cncl_yn'] == 'y' or order['cncl_yn'] == 'Y':
                    order_state[sub_index] = None
        order_states.append(order_state)
    return order_states


def autoTrade(comp_odno_sets, auto_infos):
    data = getAllOrders()
    order_states = autoTradeStates(comp_odno_sets, data)
    for index, comp_odno_set in enumerate(comp_odno_sets):
        order_state = order_states[index]
        if True in order_state:
            for sub_index, comp_odno in enumerate(comp_odno_set):
                comp_key = comp_odno
                if order_state[sub_index] == True:
                    order = data[comp_key]
                    std_price = order['ord_unpr']
                if order_state[sub_index] == False:
                    order = data[comp_key]
                    acntName = order['acntName']
                    KRX_FWDG_ORD_ORGNO = order['ord_gno_brno']
                    ORGN_ODNO = order['odno']
                    postCancelOrder(acntName, KRX_FWDG_ORD_ORGNO, ORGN_ODNO)
            
            auto_info = auto_infos[index]
            comp_odno_sets[index] = initAutoTrade(auto_info, std_price)

    return comp_odno_sets, auto_infos

#def circuitBreaker(acntName, )


def orders2excel():
    return

#print(postOrder('실전투자계좌', '02', '004410', '1', '178'))

time.sleep(1)


#print(getAcntList('실전투자계좌'))
print('----------------------')
'''
for jong in jongTarget:
    iscd = jong['iscd']
    print(getDays30(iscd))
    time.sleep(0.5)
'''
'''
res = getExecutedOrder('실전투자계좌')
print('res.headers')
print(type(res.headers))
print(res.headers)
print('res.text')
print(type(res.text))
print(res.text)
print('res.json()')
print(type(res.json()))
print(res.json())
'''
