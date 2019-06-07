# -*- coding: utf-8 -*-
import binascii
import nfc
import time
import struct
import numpy as np
import smbus
from acm1602 import acm1602
from threading import Thread, Timer

# 初期設定部
i2c_channel = 1
i2c = smbus.SMBus(i2c_channel)
acm1602_addr = 0x50
acm1602 = acm1602( i2c, acm1602_addr )	# ACM1602のインスタンスを作成する

num_block = 20
service_code = 0x010f

# NFC待ち受けの1サイクル秒
TIME_cycle = 1.0
# NFC待ち受けの反応インターバル秒
TIME_interval = 0.2
# タッチされてから次の待ち受けを開始するまで無効化する秒
TIME_wait = 3

# NFC接続リクエストのための準備
# 212F(FeliCa)で設定
target_req_suica = nfc.clf.RemoteTarget("212F")
# 8DB6(DoCard)
target_req_suica.sensf_req = bytearray.fromhex("008db60000")

class StationRecord(object):
  db = None
 
  def __init__(self, row):
    self.area_key = int(row[0], 10)
    self.line_key = int(row[1], 10)
    self.station_key = int(row[2], 10)
    self.company_value = row[3]
    self.line_value = row[4]

 
 
class HistoryRecord(object):
  def __init__(self, data):
    # ビッグエンディアンでバイト列を解釈する
    row_be = struct.unpack('>2B2H4BH4B', data)

    self.month = row_be[0]
    self.day = row_be[1]
    self.balance = row_be[12]


 
def connected(tag):
  #print tag
 
  if isinstance(tag, nfc.tag.tt3.Type3Tag):
    try:
      sc = nfc.tag.tt3.ServiceCode(service_code >> 6 ,service_code & 0x3f)

      bc = nfc.tag.tt3.BlockCode(0,service=0)
      data = tag.read_without_encryption([sc],[bc])
      history = HistoryRecord(bytes(data))

      t_data = data[14]<<8
      balance = t_data+data[15]


      # LCD Program
      ba = str(balance)

      acm1602.move_home( i2c )				# カーソルを左上に移動する
      acm1602.set_cursol( i2c, 0 )			# カーソルを非表示にする
      acm1602.set_blink( i2c, 0 )				# 点滅カーソルを非表示にする
      acm1602.clear( i2c )
      acm1602.write( i2c, "DoCARD Balance" )
      acm1602.move( i2c, 0x00, 0x01 )	
      acm1602.write( i2c,ba)	# print balance(str)
      acm1602.write( i2c," Yen")

      print "============"

      print "最終利用日: %02d月%02d日" % (history.month, history.day)

      print "残高: %d Yen" % balance

      print ('Please waiting...')	#SystemOutput
      time.sleep(TIME_wait)
      acm1602.clear( i2c )

    except Exception as e:
      print "error: %s" % e
  else:
    print "error: tag isn't Type3Tag"


print ('Lets touch DoCard!')
while True:
    # USBに接続されたNFCリーダに接続してインスタンス化
    clf = nfc.ContactlessFrontend('usb')
    # Suica待ち受け開始

    acm1602.move_home( i2c )				# カーソルを左上に移動する
    acm1602.set_cursol( i2c, 0 )			# カーソルを非表示にする
    acm1602.set_blink( i2c, 0 )				# 点滅カーソルを非表示にする
    acm1602.write( i2c, "DoCARD Balance" )	# 1行目に「Now Time is」と表示する
    acm1602.move( i2c, 0x00, 0x01 )		# 2行目の行頭に移動する
    acm1602.write( i2c,"Let's touch!!")	# 現在の時刻を表示する
	
    # clf.sense( [リモートターゲット], [検索回数], [検索の間隔] )
    target_res = clf.sense(target_req_suica, iterations=int(TIME_cycle//TIME_interval)+1 , interval=TIME_interval)

	
    if target_res != None:

        #tag = nfc.tag.tt3.Type3Tag(clf, target_res)
        #なんか仕様変わったっぽい？↓なら動いた
        tag = nfc.tag.activate_tt3(clf, target_res)
        tag.sys = 3

	
        #IDmを取り出す
        idm = binascii.hexlify(tag.idm)
        print 'Felica detected. idm = ' + idm

        connected(tag)

        #clf.connect(rdwr={'on-connect': connected})

	#print ('Please waiting...')
        #print 'sleep ' + TIME_wait + ' seconds'
        #time.sleep(TIME_wait)
	print ('Lets touch Felica!')
    #end if

    clf.close()

#end while