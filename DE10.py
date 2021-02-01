#coding:utf-8

import math
from BrakeReader import BrakeStatues

'''
# 方針
目標ブレーキシリンダ圧力を設定すると、ゆっくりとそこに向けて動いていく感じ
'''

class DE10:
    def __init__(self):
        # 車速(m/s)
        self.speed = 0
        # マスコンノッチ(0-14)
        self.mascon_level = 0
        # 非常ブレーキシリンダ圧力
        self.BC_MAX_EB = 4.0
        # 常用最大ブレーキシリンダ圧力 本物は5.7kg/cm2
        self.BC_MAX = 3.0
        # ブレーキシリンダ圧力(減速度)
        self.bc = self.BC_MAX
        # ブレーキ装置状態
        self.brake_status = BrakeStatues.FIX
        # 0(運転) ~ 1(全ブレーキ) のブレーキレベル
        self.brake_level = 0
        # 非常ブレーキ状態
        self.eb = False
        # 貨車牽引時の加速度減少(単機: 1)
        self.freight = 0.9
        # 目標ブレーキシリンダ圧力
        self.goal_bc = self.BC_MAX
        
    def getSmoothLevel(self):
        # y = log2(x+1) 最大が1
        return (math.log2(self.mascon_level+1))/4.0

    # 0.1秒進める
    def advanceTime(self):
        # 加速度を求める(m/s2)
        if self.speed < 3.33:
            accel = self.getSmoothLevel() * 0.803
        elif self.speed < 6.94:
            accel = self.getSmoothLevel() * 0.5
        elif self.speed < 9.72:
            accel = self.getSmoothLevel() * 0.333
        elif self.speed < 12.5:
            accel = self.getSmoothLevel() * 0.222
        elif self.speed < 23.5:
            accel = self.getSmoothLevel() * 0.194
        # 最高速度では加速は0になる
        else:
            accel = 0

        # 切位置時は空吹かしになって加速はしない
        if self.getWay() == 0:
            print('空吹かし')
            accel = 0
                        
        # ブレーキ装置状態から目標ブレーキシリンダ圧を求める
        if self.brake_status in (BrakeStatues.ERROR_SENSOR, BrakeStatues.ERROR, BrakeStatues.EMER):
            self.eb = True
        elif self.brake_status in (BrakeStatues.FIX, BrakeStatues.MAX_BRAKE):
            self.goal_bc = self.BC_MAX
        elif self.brake_status == BrakeStatues.BRAKE:
            self.goal_bc = round(self.BC_MAX * self.brake_level, 2)
        elif self.brake_status == BrakeStatues.RUN:
            self.goal_bc = 0.0
        elif self.brake_status == BrakeStatues.LOWER_BRAKE:
            self.goal_bc = 0.0

        # 0.1秒あたりのブレーキ作用・寛解 ここは実物に則さない
        # bc: 減速度(m/s2)とする。ここも実物に則さない
        if abs(self.bc - self.goal_bc) < 0.1:
            self.bc = self.goal_bc
        elif self.bc > self.goal_bc:
            self.bc -= (self.bc - self.goal_bc) / 20.0
        elif self.bc < self.goal_bc:
            self.bc += (self.goal_bc - self.bc) / 20.0
        
        # 丸める
        self.bc = round(self.bc, 2)
        
        if self.bc < 0:
            self.bc = 0

        # 走行抵抗
        if self.bc < 0.06:
            self.bc = 0.055
        elif self.bc > self.BC_MAX:
            self.bc = self.BC_MAX
            
        # 加減速計算
        self.speed = self.speed + (accel - self.bc) * 0.1 * self.freight
        if self.speed < 0:
            self.speed = 0

        # 非常ブレーキ
        if self.eb:
            self.bc = self.BC_MAX_EB
            self.setMascon(0)
            # 停車で復位
            if self.speed == 0:
                self.eb = False
                self.setBrake(0)

    def getSpeed(self):
        return self.speed
    
    # 暫定で方向固定
    def getWay(self):
        return 1
    
    # 0 ~ 14のマスコンノッチを入力 EB時は力行不可
    def setMascon(self, mascon_level):
        if not self.eb:
            self.mascon_level = mascon_level
        else:
            self.mascon_level = 0
    
    # 0(運転) ~ 1(全ブレーキ) のブレーキレベルを入力
    def setBrake(self, brake_level):
        self.brake_level = brake_level
    
    # ブレーキ装置の状態(非常、ブレーキ、ユルメ…)を入力
    def setBrakeStatus(self, brake_status):
        self.brake_status = brake_status
    
    # 実際のブレーキ管圧力を便宜上のブレーキシリンダ圧力値から求める
    # ブレーキ管圧力は通常490kPa 140kPa減圧して350kPaになると最大がかかる
    def getBp(self):
        return 490 - (self.bc / self.BC_MAX) * 140
    

