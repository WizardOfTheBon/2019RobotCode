import wpilib, ctre, math, logging
from wpilib.drive import MecanumDrive
from networktables import NetworkTablesimport wpilib, ctre, math, logging
from wpilib.drive import MecanumDrive
from networktables import NetworkTables
from wpilib import CameraServer
import numpy
import math
from enum import Enum
import logging
import sys
import time
import threading


cond = threading.Condition()
notified = False


def connectionListener(connected, info):
	print(info, '; Connected=%s' % connected)
	with cond:
		notified = True 
		cond.notify()

# To see messages from networktables, you must setup logging 
NetworkTables.initialize() 
NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)
sd = NetworkTables.getTable('SmartDashboard') 

sd.getValue('adjust_x', 0)
sd.getValue('adjust_y', 0)
sd.getValue('adjust_z', 0)

logging.basicConfig(level=logging.DEBUG)

class Job:
	def __init__(self):
		self.function = ''
		self.parameters = '()'
		self.driveLock = False
		

class Queue:
	
	def __init__(self):
		self.queue = list()
		
	# add puts the item at the back of the list
	def add(self, item):
		self.queue.insert(0, item)
		
	# peek will return the value of the item at the beginning of the list, without removing it
	def peek(self):
		QueueLength = len(self.queue)
		if QueueLength > 0:
			return(self.queue[QueueLength - 1])
		else:
			return()
		
	# remove will return the value of the item at the beginning of the list, and remove it
	def remove(self):
		if len(self.queue) > 0:
			return(self.queue.pop())
		else:
			return()

class MyRobot(wpilib.TimedRobot):
	def __init__(self):
		
		self.ticksPerInchPulley = 30 # 30 ticks per inch is just a guess, the number is probably different
		self.ticksPerInchLifter = 30
		self.ticksPerInchWheels = 30
		self.ticksPerInchCrabbing = 31
		self.pulleyDeadbandInches = 0.5 #how many inches we are okay with the pulley being off (to avoid the jiggle)
		
		self.spinBarDeadBand = 400 # ticks, or about 1/10 of a rotation, which is about 36 degrees
		self.ticksPerRevolution = 4096
		
		self.queue = Queue()
		
		# switches
		self.leftLeadScrewDown = 1
		self.leftLeadScrewUp = 2
		self.rightLeadScrewDown = 3
		self.rightLeadScrewUp = 4
		self.spinBarIn = 5
		self.spinBarOut = 6
		self.manualPulleyUp = 7
		self.manualPulleyDown = 8
		self.selector1 = 9
		self.selector2 = 10
		self.selector3 = 11
		self.selector4 = 12
		
		# buttons
		self.EStop = 10
		self.manualHatchDeposit = 1
		self.autoHatchDeposit = 2
		self.autoCargoDeposit = 3
		self.hatchCollectHeight = 4
		self.autoCargoShipDeposit = 5
		self.pulleyReset = 6
		self.hab1to2 = 7
		self.hab1to3 = 8
		self.hab2to3 = 9
		
		self.buttonsChannel2 = 2
		self.buttonsChannel1 = 1
		self.driveJoystickChannel = 0
		
		self.ds = wpilib.DriverStation.getInstance()
		self.driveStick = wpilib.Joystick(self.driveJoystickChannel)
		
		self.extraHeight = 1 # this is the distance (in inches) that the robot will raise above each hab level before going back down
		
		self.lifter1to2 = 6 + self.extraHeight # these measurements are in inches
		self.lifter1to3 = 18 + self.extraHeight
		self.lifter2to3 = 12 + self.extraHeight
		self.lifterSpeed = 0.5
		
		self.selector0to1voltage = 0.5
		self.selector1to2voltage = 1.5
		self.selector2to3voltage = 2.5
		
		self.levelSelectorAnalogChannel = 0
		self.IRSensorAnalogChannel = 1
		
		self.IRSensor = wpilib.AnalogInput(self.IRSensorAnalogChannel)
		
		self.bottomPulleyHallEffectChannel = 0
		self.topPulleyHallEffectChannel = 1
		self.topLeftLeadScrewHallEffectChannel = 9
		self.topRightLeadScrewHallEffectChannel = 7
		self.bottomLeftLeadScrewHallEffectChannel = 8
		self.bottomRightLeadScrewHallEffectChannel = 6
		
		self.IRSensorThreshold = 2.5
		
		self.topLeftLeadScrewHallEffect = wpilib.DigitalInput(self.topLeftLeadScrewHallEffectChannel)
		self.topRightLeadScrewHallEffect = wpilib.DigitalInput(self.topRightLeadScrewHallEffectChannel)
		self.bottomLeftLeadScrewHallEffect = wpilib.DigitalInput(self.bottomLeftLeadScrewHallEffectChannel)
		self.bottomRightLeadScrewHallEffect = wpilib.DigitalInput(self.bottomRightLeadScrewHallEffectChannel)
		
		self.crab1 = -1 # these are the distances that the robot will crab onto the different hab levels, in inches
		self.crab2 = -2
		self.crab3 = -12
		self.crab4 = -2
		self.crab5 = -4
		self.crabSpeed = 0.5
		
		self.hatch1HeightInches = 20 # these are measurements off of the ground, and will change depending on how far the pulley is off the ground
		self.hatch2HeightInches = 48 # at the bottom (the measurements are in inches)
		self.hatch3HeightInches = 76
		self.hatchDepositSpeed = 0.1
		self.hatchDepositSpeedForWheels = 1
		
		self.cargo1HeightInches = 28
		self.cargo2HeightInches = 56
		self.cargo3HeightInches = 84
		self.cargoShipHeightInches = 36
		
		self.frontLeftChannel = 2
		self.frontRightChannel = 1
		self.rearLeftChannel = 3
		self.rearRightChannel = 4
		self.leftLeadScrewChannel = 6
		self.rightLeadScrewChannel = 5
		self.pulleyChannel = 7
		self.spinBarChannel = 8
		
		self.frontLeftMotor = ctre.WPI_TalonSRX(self.frontLeftChannel)
		self.frontRightMotor = ctre.WPI_TalonSRX(self.frontRightChannel)
		self.rearLeftMotor = ctre.WPI_TalonSRX(self.rearLeftChannel)
		self.rearRightMotor = ctre.WPI_TalonSRX(self.rearRightChannel)
		self.leftLeadScrewMotor = ctre.WPI_TalonSRX(self.leftLeadScrewChannel)
		self.rightLeadScrewMotor = ctre.WPI_TalonSRX(self.rightLeadScrewChannel)
		self.pulleyMotor = ctre.WPI_TalonSRX(self.pulleyChannel)
		self.spinBarMotor = ctre.WPI_TalonSRX(self.spinBarChannel)
		
		self.pulleyMotorModifier = 0.5 # slows down the Pulley motor speed just in case it goes way too fast
		
		self.drive = MecanumDrive(
			self.frontLeftMotor,
			self.rearLeftMotor,
			self.frontRightMotor,
			self.rearRightMotor,
		)
		
		self.frontLeftMotor.setSafetyEnabled(False)
		self.rearLeftMotor.setSafetyEnabled(False)
		self.frontRightMotor.setSafetyEnabled(False)
		self.rearRightMotor.setSafetyEnabled(False)
		
		#Last thing in the init function
		super().__init__()
		
		
		
	def hab(startLevel, goalLevel):
		'''This function will '''
		
		hab = Job()
		hab.function = 'raiseBase'
		hab.parameters = '(' + str(startLevel) + ', ' + str(goalLevel) + ')'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'crabLeft'
		hab.parameters = '(self.crab1, self.frontLeftMotor)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'raiseLeft'
		hab.parameters = '(' + str(startLevel) + ', ' + str(goalLevel) + ')'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'crabLeft'
		hab.parameters = '(self.crab2, self.rearRightMotor)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'lowerLeft'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'crabLeft'
		hab.parameters = '(self.crab3, self.frontLeftMotor)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'raiseRight'
		hab.parameters = '(' + str(startLevel) + ', ' + str(goalLevel) + ')'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'crabLeft'
		hab.parameters = '(self.crab4, self.frontLeftMotor)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'lowerRight'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'crabLeft'
		hab.parameters = '(self.crab5, self.frontLeftMotor)'
		hab.driveLock = True
		self.queue.add(hab)
					
		
	def raiseBase(startLevel, goalLevel):
		
		currentLeftLeadScrewPosition = self.leftLeadScrewMotor.getQuadraturePosition()
		currentRightLeadScrewPosition = self.rightLeadScrewMotor.getQuadraturePosition()
		
		if startLevel == 1:
			if goalLevel == 2:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to2
			elif goalLevel == 3:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to3
		elif startLevel == 2:
			goalPosition = self.ticksPerInchLifter * self.Lifter2to3
		
		if currentPosition < goalPosition and wpilib.DigitalInput(self.bottomLeftLeadScrewHallEffectChannel) < self.bottomLeftLeadScrewHallEffectThreshold and wpilib.DigitalInput(self.bottomRightLeadScrewHallEffectChannel) < self.bottomRightLeadScrewHallEffectThreshold:
			self.leftLeadScrewMotor.set(self.lifterSpeed)
			self.rightLeadScrewMotor.set(self.lifterSpeed)
		else:
			self.leftLeadScrewMotor.set(0)
			self.rightLeadScrewMotor.set(0)
			self.queue.remove()
		
		
	def lowerLeft():
		'''This moves the encoders down, or extends the lead screw.'''
		currentLeftLeadScrewPosition = self.leftLeadScrewMotor.getQuadraturePosition()
		
		goalPosition = self.ticksPerInchLifter * self.extraHeight
		
		if currentPosition < goalPosition and wpilib.DigitalInput(self.bottomLeftLeadScrewHallEffectChannel) < self.bottomLeftLeadScrewHallEffectThreshold:
			self.leftLeadScrewMotor.set(self.lifterSpeed)
		else:
			self.leftLeadScrewMotor.set(0)
			self.queue.remove()
		
		
	def lowerRight():
		
		currentRightLeadScrewPosition = self.rightLeadScrewMotor.getQuadraturePosition()
		
		
		goalPosition = self.ticksPerInchLifter * self.extraHeight
		
		if currentPosition < goalPosition and wpilib.DigitalInput(self.bottomRightLeadScrewHallEffectChannel) < self.bottomRightLeadScrewHallEffectThreshold:
			self.rightLeadScrewMotor.set(self.lifterSpeed)
		else:
			self.rightLeadScrewMotor.set(0)
			self.queue.remove()
		
		
	def raiseLeft(startLevel, goalLevel):
		'''This raises the lead screws into the body, and is considered a negative direction.'''
		currentLeftLeadScrewPosition = self.leftLeadScrewMotor.getQuadraturePosition()
		
		if startLevel == 1:
			if goalLevel == 2:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to2 * -1
			elif goalLevel == 3:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to3 * -1
		elif startLevel == 2:
			goalPosition = self.ticksPerInchLifter * self.Lifter2to3 * -1
		
		if currentPosition > goalPosition and wpilib.DigitalInput(self.topLeftLeadScrewHallEffectChannel) < self.topLeftLeadScrewHallEffectThreshold:
			self.leftLeadScrewMotor.set(-1 * self.lifterSpeed)
		else:
			self.leftLeadScrewMotor.set(0)
			self.queue.remove()
		
		
	def raiseRight(startLevel, goalLevel):
		
		currentRightLeadScrewPosition = self.rightLeadScrewMotor.getQuadraturePosition()
		
		if startLevel == 1:
			if goalLevel == 2:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to2 * -1
			elif goalLevel == 3:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to3 * -1
		elif startLevel == 2:
			goalPosition = self.ticksPerInchLifter * self.Lifter2to3 * -1
		
		if currentPosition > goalPosition and wpilib.DigitalInput(self.topRightLeadScrewHallEffectChannel) < self.topRightLeadScrewHallEffectThreshold:
			self.rightLeadScrewMotor.set(-1 * self.lifterSpeed)
		else:
			self.rightLeadScrewMotor.set(0)
			self.queue.remove()
		
		
	def driveQuadratureReset():
		
		self.frontLeftMotor.setQuadraturePosition(0, 0)
		self.frontRightMotor.setQuadraturePosition(0, 0)
		self.rearLeftMotor.setQuadraturePosition(0, 0)
		self.rearRightMotor.setQuadraturePosition(0, 0)
		
		
	def crabLeft(distance, encoder):
		
		currentPosition = encoder.getQuadraturePosition()
		
		goalPosition = ticksPerInchCrabbing * distance
		
		if currentPosition > goalPosition:
			self.frontLeftMotor.set(-1 * self.crabSpeed)
			self.frontRightMotor.set(self.crabSpeed)
			self.rearLeftMotor.set(self.crabSpeed)
			self.rearRightMotor.set(-1 * self.crabSpeed)
		else:
			self.frontLeftMotor.set(0)
			self.frontRightMotor.set(0)
			self.rearLeftMotor.set(0)
			self.rearRightMotor.set(0)
			self.queue.remove()
		
		
	def depositPayload(level, payload):
		
		depositPayload = Job()
		depositPayload.function = 'pulleyHeight'
		depositPayload.parameters = '(' + str(level) + ', ' + str(payload) + ')'
		depositPayload.driveLock = True
		self.queue.add(depositPayload)
		
		depositPayload = Job()
		depositPayload.function = 'dispense'
		depositPayload.parameters = '(' + str(payload) + ')'
		depositPayload.driveLock = True
		self.queue.add(depositPayload)
		
		
		
	def levelSelector():
		'''This function returns the level as an integer by checking the rotary switch controlling rocket level.'''
		
		if self.ds.getStickButton(2, self.selector1):
			return(0)
		elif self.ds.getStickButton(2, self.selector2):
			return(1)
		elif self.ds.getStickButton(2, self.selector3):
			return(2)
		else:
			return(3)
			
			
	def Pulley_encoder():
		currentPosition= self.pulleyMotor.getQuadraturePosition()
		
		
	def pulleyHeight(level, payload): # level 0 is the floor, payload 1 is hatch, payload 2 is cargo, payload 3 is cargo ship cargo(not done yet)
		'''Moves the Pulley to certain levels, with a certain offset based on hatch or cargo. The cargo ship has a unique offset (supposedly), and the hatch has no offset.'''
		
		currentPosition = self.pulleyMotor.getQuadraturePosition()
		
		if level == 0:
			self.resetPulley()
		elif payload == 1: # hatch
			if level == 1:
				goalPosition = self.ticksPerInchPulley * self.hatch1Height
			elif level == 2:
				goalPosition = self.ticksPerInchPulley * self.hatch2Height
			else: # level 3 is the only other option the Pulley has, so the else is for level 3
				goalPosition = self.ticksPerInchPulley * self.hatch3Height
		elif payload == 2: # cargo
			if level == 1:
				goalPosition = self.ticksPerInchPulley * self.cargo1Height
			elif level == 2:
				goalPosition = self.ticksPerInchPulley * self.cargo2Height
			else:
				goalPosition = self.ticksPerInchPulley * self.cargo3Height
		else:
			goalPosition = self.ticksPerInchPulley * self.cargoShipHeightInches
			
		if level > 0:
			if currentPosition < (goalPosition - (self.ticksPerInchPulley * self.pulleyDeadbandInches)) and wpilib.DigitalInput(topPulleyHallEffectChannel) < self.topPulleyHallEffectThreshold: # this sets a deadband for the encoders on the pulley so that the pulley doesnt go up and down forever
				self.pulleyMotor.set(self.pulleyMotorModifier)
				
			elif currentPosition > (goalPosition + (self.ticksPerInchPulley * self.pulleyDeadbandInches)) and wpilib.DigitalInput(topPulleyHallEffectChannel) < self.topPulleyHallEffectThreshold:
				self.pulleyMotor.set(-1 * self.pulleyMotorModifier)
				
			else:
				self.pulleyMotor.set(0)
				self.queue.remove()
		
		
	def dispense(payload):
		
		currentPosition = self.spinBarMotor.getQuadraturePosition()
		goalPositionCargo = self.ticksPerRevolution * 8
		goalPositionHatch = self.ticksPerRevolution
		
		
		if payload == 2 or payload == 3: # a cargo or a cargoship
		
			if currentPosition < (goalPositionCargo - self.spinBarDeadBand):
				self.spinBarMotor.set(0.5)
				
			elif currentPosition > (goalPositionCargo + self.spinBarDeadBand):
				self.spinBarMotor.set(-0.5)
				
			else:
				self.spinBarMotor.set(0)
				self.queue.remove()
			
		# This logic requires a job before this one to set the spinBar position to 0 when it is all the way back, without needing the spinBar to
		# go backwards multiple rotations to get to quadrature position 0. This is accomplished using the resetSpinBar function.
		elif payload == 1: # a hatch
		
			if currentPosition < (goalPositionHatch - self.spinBarDeadBand):
				self.spinBarMotor.set(self.hatchDepositSpeed)
				self.frontLeftMotor.set(-1 * self.hatchDepositSpeedForWheels)
				self.frontRightMotor.set(self.hatchDepositSpeedForWheels)
				self.rearLeftMotor.set(self.hatchDepositSpeedForWheels)
				self.rearRightMotor.set(-1 * self.hatchDepositSpeedForWheels)
				
			elif currentPosition > (goalPositionHatch + self.spinBarDeadBand):
				self.spinBarMotor.set(-1 * self.hatchDepositSpeed)
				self.frontLeftMotor.set(-1 * self.hatchDepositSpeedForWheels)
				self.frontRightMotor.set(self.hatchDepositSpeedForWheels)
				self.rearLeftMotor.set(self.hatchDepositSpeedForWheels)
				self.rearRightMotor.set(-1 * self.hatchDepositSpeedForWheels)
				
			else:
				self.spinBarMotor.set(0)
				self.frontLeftMotor.set(0)
				self.frontRightMotor.set(0)
				self.rearLeftMotor.set(0)
				self.rearRightMotor.set(0)
				self.queue.remove()
		
		
	def resetSpinBar():
		
		currentPosition = self.spinBarMotor.getQuadraturePosition()
		offset = currentPosition % self.ticksPerRevolution
		
		if (offset) > self.spinBarDeadBand:
			self.spinBarMotor.set(-1 * self.spinBarResetSpeed)
		else:
			self.spinBarMotor.set(0)
			self.spinBarMotor.setQuadraturePosition(offset, 0)
			self.queue.remove()
		
		
	def spinBar(velocity):
		
		self.spinBarMotor.set(velocity)
		
		
	def resetPulley(): # to bring the pulley back to its starting height
		# go down until the hall effect sensor reads the magnet, then stop and set encoder value to 0
		
		if self.DigitalInput(self.bottomPulleyHallEffectChannel) < self.bottomPulleyHallEffectThreshold:
			self.pulleyMotor.set(-1 * self.pulleyMotorModifier)
		else:
			self.pulleyMotor.set(0)
			self.pulleyMotor.setQuadraturePosition(0, 0)
			self.queue.remove()
		
		
	def robotInit(self):
		"""Robot initialization function"""
		
		pass
		
		
	def autonomousInit(self):
		
		pass
		
		
	def autonomousPeriodic(self):
		
		pass
		
		
	def teleopInit(self):
		
		pass
		
		
	def checkSwitches(self):
		
		if self.ds.getStickButton(1, self.EStop) ==1: #E-Stop button pressed, stop all motors and remove all jobs from job queue.
			
			self.frontLeftMotor.set(0)
			self.frontRightMotor.set(0)
			self.rearLeftMotor.set(0)
			self.rearRightMotor.set(0)
			self.leftLeadScrewMotor.set(0)
			self.rightLeadScrewMotor.set(0)
			self.pulleyMotor.set(0)
			self.spinBarMotor.set(0)
			
			#Remove all queued jobs by setting the queue to the blank class
			
			self.queue = Queue()
			
			
		else: #Check every other switch
			
			
			# leadscrew buttons aaaaaaaaaaaaaaannnnnnnnd limit switch stuff \/ \/ \/ 
			
			if self.ds.getStickButton(2, self.leftLeadScrewDown) and self.bottomLeftLeadScrewHallEffect == 1: # left lead screw out manual
				self.leftLeadScrewMotor.set(self.lifterSpeed)
				
			elif self.ds.getStickButton(2, self.leftLeadScrewUp) and self.topLeftLeadScrewHallEffect == 1: # left lead screw in manual
				self.leftLeadScrewMotor.set(-1 * self.lifterSpeed)
				
			else:
				self.leftLeadScrewMotor.set(0)
				
				
			if self.ds.getStickButton(2, self.rightLeadScrewDown) and self.bottomRightLeadScrewHallEffect == 1: # right lead screw out manual
				self.rightLeadScrewMotor.set(self.lifterSpeed)
				
			elif self.ds.getStickButton(2, self.rightLeadScrewUp) and self.topRightLeadScrewHallEffect == 1: # right lead screw in manual
				self.rightLeadScrewMotor.set(-1 * self.lifterSpeed)
				
			else:
				self.rightLeadScrewMotor.set(0)
				
				
			# spinbar buttons
				
			if self.ds.getStickButton(2, self.spinBarIn) ==1: # cargo collecting
				if self.IRSensor.getVoltage() < self.IRSensorThreshold: # IR distance sensor stops the spinBar from spinning in when the ball is already in
					self.spinBarMotor.set(-1)
				else:
					self.spinBarMotor.set(0)
				
			elif self.ds.getStickButton(2, self.spinBarOut) ==1: # manual cargo depositing
				self.spinBarMotor.set(1)
				
			elif self.ds.getStickButton(1, self.manualHatchDeposit) ==1: # manual hatch depositing
				self.spinBarMotor.set(self.hatchDepositSpeed)
				
			else:
				self.spinBarMotor.set(0)
				
				
			# pulley up down buttons
				
			if self.ds.getStickButton(2, self.manualPulleyUp) ==1: # manual pulley up
				self.pulleyMotor.set(self.pulleyMotorModifier)
				
			elif self.ds.getStickButton(2, self.manualPulleyDown)==1: # manual pulley down
				self.pulleyMotor.set(-1 * self.pulleyMotorModifier)
				
				
			# hatch buttons
				
			if self.ds.getStickButton(1, self.autoHatchDeposit)==1: # hatch movement and depositing (auto)
				Deposit_pl = Job()
				Deposit_pl.function = 'depositPayload'
				Deposit_pl.parameters = '(self.levelSelector, 1)'
				Deposit_pl.driveLock = True
				self.queue.add(Deposit_pl)
				
			elif self.ds.getStickButton(1, self.hatchCollectHeight) == 1: # hatch collecting (from player station)
				hatchCollectManual = Job()
				hatchCollectManual.function = 'pulleyHeight'
				hatchCollectManual.parameters = '(1, 1)'
				hatchCollectManual.driveLock = True
				self.queue.add(hatchCollectManual)
				
				hatchCollectManual = Job()
				hatchCollectManual.function = 'resetSpinBar'
				hatchCollectManual.parameters = '()'
				hatchCollectManual.driveLock = False
				self.queue.add(hatchCollectManual)
				
				
			# cargo buttons
				
			elif self.ds.getStickButton(1, self.autoCargoDeposit) == 1: # cargo movement and depositing
				
				self.depositPayload(self.levelSelector, 2)
				
				
			elif self.ds.getStickButton(1, self.autoCargoShipDeposit) == 1: # cargo ship depositing
				
				self.depositPayload(self.levelSelector, 3)
				
				
			# Pulley reset button
				
			elif self.ds.getStickButton(1, self.pulleyReset) == 1: # pulley reset
				resetPulley = Job()
				resetPulley.function = 'resetPulley'
				resetPulley.parameters = '()'
				resetPulley.driveLock = False
				self.queue.add(resetPulley)
				
				
			# buttons controlling baseLifter (3 buttons)
				
			if self.ds.getStickButton(1, self.hab1to2) == 1: # hab level 1 to level 2
				self.hab(1, 2)
				
			elif self.ds.getStickButton(1, self.hab1to3) ==1: # hab level 1 to level 3
				self.hab(1, 3)
				
			elif self.ds.getStickButton(1, self.hab2to3) ==1: # hab level 2 to level 3
				self.hab(2, 3)
				
				
			
			
			
			
	def teleopPeriodic(self):
		# checks switches and sensors, which feed the queue with jobs
		self.checkSwitches()
		
		# we are checking if a job is in the queue, and then calling the function that the first job makes using eval
		if len(self.queue.queue) > 0:
			
			currentJob = self.queue.peek()
			
			eval(currentJob.function + currentJob.parameters)
			
			# allows the driver to drive the robot when the currentJob allows them to, using the driveLock parameter in the job
			if currentJob.drivelock == False:
				self.drive.driveCartesian(self.driveStick.getX(), self.driveStick.getY(), self.driveStick.getZ(), 0)
			
		else:
			self.drive.driveCartesian(self.driveStick.getX(), self.driveStick.getY(), self.driveStick.getZ(), 0)
		
		if self.ds.getStickButton(0,2) ==1:
			try:
				test = sd.getValue('adjust_x', 0)
				testy = sd.getValue('adjust_y', 0)
				testz = sd.getValue('adjust_z', 0)
				print('x ' + str(test))
				print('y ' + str(testy))
				print('z ' + str(testz))
			except Exception as e:
				print(str(e.args))
			
			if len(self.queue.queue) == 0 and self.ds.getStickButton(0,2) == 1:
				self.drive.driveCartesian(self.driveStick.getX(test), self.driveStick.getY(testy), self.driveStick.getZ(testz), 0)
			
			
if __name__ == "__main__":
	wpilib.run(MyRobot)
