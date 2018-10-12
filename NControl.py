#encoding: utf-8

import DE10
import MasconReader
import BrakeReader
import Controller
import Sounder
from multiprocessing import Process, Value
import time

## マスコン読み込みプロセス起動
def ReadMasconWorker(mascon_shared, device):    
    mascon = MasconReader.ReadMascon(device)
    while True:
        mascon_level = mascon.waitAndGetMascon()
        mascon_shared.value = mascon_level

mascon_shared = Value('i', 0)
mascon_process = Process(target=ReadMasconWorker, args=(mascon_shared, '/dev/ttyUSB1'))
mascon_process.start()

# ブレーキ読み込みプロセス起動
def ReadBrakeWorker(brake_shared, buttons_shared, speed_shared, device):    
    brake = BrakeReader.ReadBrake(device)
    while True:
        brake_level, buttons = brake.waitAndGetData()
        brake_shared.value = brake_level
        buttons_shared.value = buttons
        brake.setSpeed(speed_shared.value)

brake_shared = Value('f', 0.0)
buttons_shared = Value('i', 0)
speed_shared = Value('i', 0)
brake_process = Process(target=ReadBrakeWorker, args=(brake_shared, buttons_shared, speed_shared, '/dev/ttyUSB0'))
brake_process.start()

DE101 = DE10.DE10()
#controller = Controller.Controller('/dev/ttyUSB2')

Sound = Sounder.Sounder()
Sound.idle.play(0)

# メインループを0.1秒おきに回す
last_counter = time.time()

# ホーンが最後に押されたUNIX time
last_hone = 0

# 最後の方向, 速度
last_way = 0
last_kph = 0
last_mascon_level = 0
last_brake = False

while True:
    try:
        mascon_level = mascon_shared.value
        brake_level = brake_shared.value
        buttons = buttons_shared.value
        
        DE101.setMascon(mascon_level)
        DE101.setBrake(brake_level)
        DE101.setButtons(buttons)
        
        DE101.advanceTime()
        speed = DE101.getSpeed()
        
        if (last_hone < time.time() - 3) and DE101.isHoneEnabled():
            last_hone = time.time()
            Sound.Hone()
            
        if (brake_level < 0 and not last_brake) or (DE101.eb and not last_brake):
            last_brake = True
            Sound.brake.play(0)
        elif brake_level >= 0 and not DE101.eb:
            last_brake = False
            Sound.brake.stop(0)
            
        if last_way != DE101.getWay():
            last_way = DE101.getWay()
            Sound.Switch()
            
        kph = speed * 3600 / 1000
        
        if not DE101.isKeyEnabled():
            DE101.eb = True
            
        if kph == 0:
            Sound.run.stopAll()
        if 0 < kph < 15  and not(0 < last_kph < 15):
            Sound.run.stopAll()
            Sound.run.play(0)
        if 15 <= kph < 25  and not (15 <= last_kph < 25):
            Sound.run.stopAll()
            Sound.run.play(1)
        if 25 <= kph < 35  and not (25 <= last_kph < 35):
            Sound.run.stopAll()
            Sound.run.play(2)
        if 35 <= kph < 45  and not (35 <= last_kph < 45):
            Sound.run.stopAll()
            Sound.run.play(3)
        if 45 <= kph < 65  and not (45 <= last_kph < 65):
            Sound.run.stopAll()
            Sound.run.play(4)
        if 65 <= kph  and not(65 <= last_kph):
            Sound.run.stopAll()
            Sound.run.play(5)

        last_kph = kph
        
        if mascon_level == 0:
            Sound.power.stopAll()
        if 1 <= mascon_level < 5 and (last_mascon_level == 0 or 5 <= last_mascon_level):
            Sound.power.stopAll()
            Sound.power.play(0)
        elif 5 <= mascon_level < 10 and (last_mascon_level < 5 or 10 <= last_mascon_level):
            Sound.power.stopAll()
            Sound.power.play(1)
        elif 10 <= mascon_level < 14 and (last_mascon_level < 10 or 14 <= last_mascon_level):
            Sound.power.stopAll()
            Sound.power.play(2)
        last_mascon_level = mascon_level

        speed_shared.value = int(kph)
        print(kph)
        controller.move(speed, DE101.getWay(), DE101.isHonsenEnabled())
        
        # 0.1秒経過するまでwaitする
        while (time.time() < last_counter + 0.1):
            time.sleep(0.001)
        last_counter = time.time()
        
    except KeyboardInterrupt:
        controller.move(0, 0, False)
        raise
        

