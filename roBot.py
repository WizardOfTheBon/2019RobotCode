import wpilib, ctre, math, logging
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
		wpilib.CameraServer.launch()
		self.ticksPerInchPulley = 1735 #for wilsonville pulley, will be inaccurate at higher numbers
		self.ticksPerInchLifter = 30
		self.ticksPerInchWheels = 30
		self.ticksPerInchCrabbing = 31
		self.pulleyDeadbandInches = 1 #how many inches we are okay with the pulley being off (to avoid the jiggle)
		
		self.spinBarDeadBand = 400 # ticks, or about 1/10 of a rotation, which is about 36 degrees
		self.ticksPerRevolution = 4096
		
		self.queue = Queue()
		
		# switches
		self.leftLeadScrewDown = 5
		self.leftLeadScrewUp = 4
		self.rightLeadScrewDown = 3
		self.rightLeadScrewUp = 2
		self.spinBarIn = 14
		self.spinBarOut = 15
		self.manualPulleyUp = 7
		self.manualPulleyDown = 6
		self.selector1 = 8
		self.selector2 = 11
		self.selector3 = 12
		self.selector4 = 13
		
		
		# buttons
		self.eStop = 1
		self.manualHatchDeposit = 1
		self.autoHatchDeposit = 4
		self.autoCargoDeposit = 3
		self.hatchCollectHeight = 7
		self.autoCargoShipDeposit = 8
		self.pulleyReset = 6
		self.hab1to2 = 10
		self.hab1to3 = 9
		self.hab2to3 = 2
		
		self.buttonsChannel2 = 2
		self.buttonsChannel1 = 1
		self.driveJoystickChannel = 0
		
		self.ds = wpilib.DriverStation.getInstance()
		self.driveStick = wpilib.Joystick(self.driveJoystickChannel)
		self.auxiliary1 = wpilib.Joystick(self.buttonsChannel1)
		self.auxiliary2 = wpilib.Joystick(self.buttonsChannel2)
		
		self.extraHeight = 1 # this is the distance (in inches) that the robot will raise above each hab level before going back down
		
		self.Lifter1to2 = 6 + self.extraHeight # these measurements are in inches
		self.Lifter1to3 = 19 + self.extraHeight
		self.Lifter2to3 = 13 + self.extraHeight
		self.lifterSpeed = .7
		
		self.selector0to1voltage = 0.5
		self.selector1to2voltage = 1.5
		self.selector2to3voltage = 2.5
		
		self.levelSelectorAnalogChannel = 0
		self.IRSensorAnalogChannel = 1
		
		self.IRSensor = wpilib.AnalogInput(self.IRSensorAnalogChannel)
		
		self.bottomPulleyHallEffectChannel = 0
		self.topPulleyHallEffectChannel = 1
		self.topLeftLeadScrewHallEffectChannel = 7
		self.topRightLeadScrewHallEffectChannel = 3
		self.bottomLeftLeadScrewHallEffectChannel = 9
		self.bottomRightLeadScrewHallEffectChannel = 5
		
		
		self.bottomPulleyHallEffect = wpilib.DigitalInput(self.bottomPulleyHallEffectChannel)
		self.topPulleyHallEffect = wpilib.DigitalInput(self.topPulleyHallEffectChannel)
		self.topLeftLeadScrewHallEffect = wpilib.DigitalInput(self.topLeftLeadScrewHallEffectChannel)
		self.topRightLeadScrewHallEffect = wpilib.DigitalInput(self.topRightLeadScrewHallEffectChannel)
		self.bottomLeftLeadScrewHallEffect = wpilib.DigitalInput(self.bottomLeftLeadScrewHallEffectChannel)
		self.bottomRightLeadScrewHallEffect = wpilib.DigitalInput(self.bottomRightLeadScrewHallEffectChannel)
		
		self.IRSensorThreshold = 2.5
		
		self.bottomPulleyHallEffectThreshold = 1
		self.topPulleyHallEffectThreshold = 1
		self.topLeftLeadScrewHallEffectThreshold = 1
		self.topRightLeadScrewHallEffectThreshold = 1
		self.bottomLeftLeadScrewHallEffectThreshold = 1
		self.bottomRightLeadScrewHallEffectThreshold = 1
		
		self.crab1 = 1 # these are the distances that the robot will crab onto the different hab levels, in inches
		self.crab2 = 2
		self.crab3 = 24
		self.crab4 = 2
		self.crab5 = 4
		self.crabSpeed = 0.8
		self.crabTolerance = 200
		self.fLCrabSpeed = 0.6
		self.bLCrabSpeed = 0.6
		self.fRCrabSpeed = 0.6
		self.bRCrabSpeed = 0.6
		
		self.hatch1Height = 20 # these are measurements off of the ground, and will change depending on how far the pulley is off the ground
		self.hatch2Height = 48 # at the bottom (the measurements are in inches)
		self.hatch3Height = 76
		self.hatchDepositSpeed = 0.1
		self.hatchDepositSpeedForWheels = 1
		
		self.cargo1Height = 28
		self.cargo2Height = 56
		self.cargo3Height = 84
		self.cargoShipHeightInches = 36
		
		self.frontLeftChannel = 2
		self.frontRightChannel = 1
		self.rearLeftChannel = 3
		self.rearRightChannel = 4
		self.leftLeadScrewChannel = 6
		self.rightLeadScrewChannel = 5
		self.pulleyChannel = 7
		self.spinBarChannel = 8
		self.raisedPulley = False
		
		self.frontLeftMotor = ctre.WPI_TalonSRX(self.frontLeftChannel)
		self.frontRightMotor = ctre.WPI_TalonSRX(self.frontRightChannel)
		self.rearLeftMotor = ctre.WPI_TalonSRX(self.rearLeftChannel)
		self.rearRightMotor = ctre.WPI_TalonSRX(self.rearRightChannel)
		self.leftLeadScrewMotor = ctre.WPI_TalonSRX(self.leftLeadScrewChannel)
		self.rightLeadScrewMotor = ctre.WPI_TalonSRX(self.rightLeadScrewChannel)
		self.pulleyMotor = ctre.WPI_TalonSRX(self.pulleyChannel)
		self.spinBarMotor = ctre.WPI_TalonSRX(self.spinBarChannel)
		
		self.pulleyMotorModifier = 0.8 # slows down the Pulley motor speed just in case it goes way too fast
		self.frontLeftMotor.setInverted(True)
		self.frontRightMotor.setInverted(True)
		self.rearLeftMotor.setInverted(True)
		self.rearRightMotor.setInverted(True)
		
		self.drive = MecanumDrive(
			self.frontRightMotor,
			self.rearRightMotor,
			self.frontLeftMotor,
			self.rearLeftMotor,
		)
		
		self.frontLeftMotor.setSafetyEnabled(False)
		self.rearLeftMotor.setSafetyEnabled(False)
		self.frontRightMotor.setSafetyEnabled(False)
		self.rearRightMotor.setSafetyEnabled(False)
		
		#this is the IR dist for ball
		self.ball_dist = 2.5
		self.hatch_dist = 3
		self.alignB1 = 15
		self.alignH = 35
		self.alignCB = 12
		self.adjust_ready = False
		self.pulleyMotor.setQuadraturePosition(0,0)
		#Last thing in the init function
		super().__init__()
		
	def hab(self, startLevel, goalLevel):
		'''This function will '''
		
		hab = Job()
		hab.function = 'self.raiseBase'
		hab.parameters = '(' + str(startLevel) + ', ' + str(goalLevel) + ')'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.crabRight'
		hab.parameters = '(self.crab1)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.raiseLeft'
		hab.parameters = '(' + str(startLevel) + ', ' + str(goalLevel) + ')'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.crabRight'
		hab.parameters = '(self.crab2)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.lowerLeft'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.crabRight'
		hab.parameters = '(self.crab3)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.raiseRight'
		hab.parameters = '(' + str(startLevel) + ', ' + str(goalLevel) + ')'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.crabRight'
		hab.parameters = '(self.crab4)'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.lowerRight'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.driveQuadratureReset'
		hab.parameters = '()'
		hab.driveLock = True
		self.queue.add(hab)
		
		hab = Job()
		hab.function = 'self.crabRight'
		hab.parameters = '(self.crab5)'
		hab.driveLock = True
		self.queue.add(hab)
		
	def raiseBase(self, startLevel, goalLevel):
	
		Left_off = 0
		Right_off = 0
		currentLeftLeadScrewPosition = self.leftLeadScrewMotor.getQuadraturePosition()
		currentRightLeadScrewPosition = self.rightLeadScrewMotor.getQuadraturePosition()
		
		if startLevel == 1:
			if goalLevel == 2:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to2
			elif goalLevel == 3:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to3
		elif startLevel == 2:
			goalPosition = self.ticksPerInchLifter * self.Lifter2to3
		
		if currentLeftLeadScrewPosition < goalPosition and (self.bottomLeftLeadScrewHallEffect).get() < self.bottomLeftLeadScrewHallEffectThreshold:
			self.leftLeadScrewMotor.set(self.lifterSpeed)
		else:
			self.leftLeadScrewMotor.set(0)
			Left_off = 1
			
	
		if currentRightLeadScrewPosition < goalPosition and (self.bottomRightLeadScrewHallEffect).get() < self.bottomRightLeadScrewHallEffectThreshold:
			self.rightLeadScrewMotor.set(self.lifterSpeed)
		else:
			self.rightLeadScrewMotor.set(0)
			Right_off = 1
			self.queue.remove()
			
		if Left_off ==1 and Right_off ==1:
			self.queue.remove()
			
	def lowerLeft(self):
		'''This moves the encoders down, or extends the lead screw.'''
		currentLeftLeadScrewPosition = self.leftLeadScrewMotor.getQuadraturePosition()
		
		goalPosition = self.ticksPerInchLifter * self.extraHeight
		
		if currentLeftLeadScrewPosition < goalPosition and (self.bottomLeftLeadScrewHallEffect.get()) < self.bottomLeftLeadScrewHallEffectThreshold:
			self.leftLeadScrewMotor.set(self.lifterSpeed)
		else:
			self.leftLeadScrewMotor.set(0)
			self.queue.remove()
			
			
	def lowerRight(self):
		
		currentRightLeadScrewPosition = self.rightLeadScrewMotor.getQuadraturePosition()
		
		
		goalPosition = self.ticksPerInchLifter * self.extraHeight
		
		if currentPosition < goalPosition and (self.bottomRightLeadScrewHallEffect.get()) < self.bottomRightLeadScrewHallEffectThreshold:
			self.rightLeadScrewMotor.set(self.lifterSpeed)
		else:
			self.rightLeadScrewMotor.set(0)
			self.queue.remove()
			
			
	def raiseLeft(self, startLevel, goalLevel):
		'''This raises the lead screws into the body, and is considered a negative direction.'''
		currentLeftLeadScrewPosition = self.leftLeadScrewMotor.getQuadraturePosition()
		
		if startLevel == 1:
			if goalLevel == 2:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to2 * -1
			elif goalLevel == 3:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to3 * -1
		elif startLevel == 2:
			goalPosition = self.ticksPerInchLifter * self.Lifter2to3 * -1
		
		if currentLeftLeadScrewPosition > goalPosition and (self.topLeftLeadScrewHallEffect.get()) < self.topLeftLeadScrewHallEffectThreshold:
			self.leftLeadScrewMotor.set(-1 * self.lifterSpeed)
		else:
			self.leftLeadScrewMotor.set(0)
			self.queue.remove()
			
			
	def raiseRight(self, startLevel, goalLevel):
		
		currentRightLeadScrewPosition = self.rightLeadScrewMotor.getQuadraturePosition()
		
		if startLevel == 1:
			if goalLevel == 2:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to2 * -1
			elif goalLevel == 3:
				goalPosition = self.ticksPerInchLifter * self.Lifter1to3 * -1
		elif startLevel == 2:
			goalPosition = self.ticksPerInchLifter * self.Lifter2to3 * -1
		
		if currentRightLeadScrewPosition > goalPosition and (self.topRightLeadScrewHallEffect.get()) < self.topRightLeadScrewHallEffectThreshold:
			self.rightLeadScrewMotor.set(-1 * self.lifterSpeed)
		else:
			self.rightLeadScrewMotor.set(0)
			self.queue.remove()
			
			
	def driveQuadratureReset(self):
		
		self.frontLeftMotor.setQuadraturePosition(0, 0)
		self.frontRightMotor.setQuadraturePosition(0, 0)
		self.rearLeftMotor.setQuadraturePosition(0, 0)
		self.rearRightMotor.setQuadraturePosition(0, 0)
		'''
	def crabRight(self, distance):
		
		currentFrontPosition = self.frontLeftMotor.getQuadraturePosition()
		currentRearPosition = self.rearLeftMotor.getQuadraturePosition()
		
		currentPosition = (currentFrontPosition + currentRearPosition)/2
		goalPosition = self.ticksPerInchCrabbing * distance
		
		#print('function is set up')
		#print('current is ' + str(currentPosition))
		#print('goal is ' + str(goalPosition))
		if currentPosition < goalPosition:
			
			if math.isclose(currentFrontPosition, currentRearPosition, abs_tol=self.crabTolerance):
				print(str(currentPosition))
				print('motors should be moving the same speed')
				
			elif currentFrontPosition > currentPosition:
				print('rear motors should be moving faster')
				print(str(currentPosition))
				self.bLCrabSpeed += 0.01
				self.bRCrabSpeed += 0.01
				self.fLCrabSpeed += -0.01
				self.fRCrabSpeed += -0.01
			
				
				
			else:
				print('front motors should be moving faster')
				print(str(currentPosition))
				self.fLCrabSpeed += 0.01
				self.fRCrabSpeed += 0.01
				self.bLCrabSpeed += -0.01
				self.bRCrabSpeed += -0.01
				
				
		else:
			self.frontLeftMotor.set(0)
			self.frontRightMotor.set(0)
			self.rearLeftMotor.set(0)
			self.rearRightMotor.set(0)
			self.queue.remove()
			
			print('you have reached your goal')
		
		self.frontLeftMotor.set(self.fLCrabSpeed)
		self.frontRightMotor.set(self.fRCrabSpeed)
		self.rearLeftMotor.set(self.bLCrabSpeed)
		self.rearRightMotor.set(self.bRCrabSpeed)
		'''
		
	def depositPayload(self, level, payload):
		
		JOB = Job()
		JOB.function = 'self.pulleyHeight'
		JOB.parameters = '(' + str(level) + ', ' + str(payload) + ')'
		JOB.driveLock = True
		self.queue.add(JOB)
		
		JOB = Job()
		JOB.function = 'self.dispense'
		JOB.parameters = '(' + str(payload) + ')'
		JOB.driveLock = True
		self.queue.add(JOB)
	def levelSelector(self):
		'''This function returns the level as an integer by checking the rotary switch controlling rocket level.'''
		
		if self.auxiliary2.getRawButton(self.selector1):
			return(1)
		elif self.auxiliary2.getRawButton(self.selector2):
			return(2)
		elif self.auxiliary2.getRawButton(self.selector3):
			return(3)
		else:
			pass
			
	def Pulley_encoder(self):
		currentPosition= self.pulleyMotor.getQuadraturePosition()
	def pulleyHeight(self, level, payload): # level 0 is the floor, payload 1 is hatch, payload 2 is cargo, payload 3 is cargo ship cargo(not done yet)
		'''Moves the Pulley to certain levels, with a certain offset based on hatch or cargo. The cargo ship has a unique offset (supposedly), and the hatch has no offset.'''
		currentPosition = self.pulleyMotor.getQuadraturePosition()
		
		if payload == 1: # hatch
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
				
		elif payload == 6:
			if level==1: #6 is the rocket ball
				print('moving at ' + self.pulleyMotorModifier)
				goalPosition = self.ticksPerInchPulley * self.alignB1
		elif payload == 5: #5 is the rocket hatch
			if level == 1:
				print('moving at ' + self.pulleyMotorModifier)
				goalPosition= self.ticksPerInchPulley * self.alignH
		elif payload == 4: #4 is the cargoship ball
			if level == 1:
				print('moving at ' + self.pulleyMotorModifier)
				goalPosition = self.ticksPerInchPulley* self.alignCB
		else:
			goalPosition = self.ticksPerInchPulley * self.cargoShipHeightInches
			
			

			
			
		if currentPosition < (goalPosition - (self.ticksPerInchPulley * self.pulleyDeadbandInches)): # this sets a deadband for the encoders on the pulley so that the pulley doesnt go up and down forever
			self.pulleyMotor.set(self.pulleyMotorModifier)
			
		elif currentPosition > (goalPosition + (self.ticksPerInchPulley * self.pulleyDeadbandInches)): #and (topPulleyHallEffect.get()) < self.topPulleyHallEffectThreshold
			self.pulleyMotor.set(-1 * self.pulleyMotorModifier)
			
		else:
			self.pulleyMotor.set(0)
			self.queue.remove()
	def dispense(self, payload):
		
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
	def resetSpinBar(self):
		
		currentPosition = self.spinBarMotor.getQuadraturePosition()
		offset = currentPosition % self.ticksPerRevolution
		
		if (offset) > self.spinBarDeadBand:
			self.spinBarMotor.set(-1 * self.spinBarResetSpeed)
		else:
			self.spinBarMotor.set(0)
			self.spinBarMotor.setQuadraturePosition(offset, 0)
			self.queue.remove()
	def spinBar(self, velocity):
		
		self.spinBarMotor.set(velocity)
	def resetPulley(self): # to bring the pulley back to its starting height
		# go down until the hall effect sensor reads the magnet, then stop and set encoder value to 0
		
		if (self.bottomPulleyHallEffect.get()) < self.bottomPulleyHallEffectThreshold:
			self.pulleyMotor.set(-1 * self.pulleyMotorModifier)
		else:
			self.pulleyMotor.set(0)
			self.pulleyMotor.setQuadraturePosition(0, 0)
			self.queue.remove()
	def robotInit(self):
		"""Robot initialization function"""
		
		
	def autonomousInit(self):
	
		print('autonomous starting')
		self.raisedPulley = False
		self.pulleyMotor.setQuadraturePosition(0,0)
		self.leftLeadScrewMotor.setQuadraturePosition(0,0)
		self.rightLeadScrewMotor.setQuadraturePosition(0,0)
		self.frontRightMotor.setQuadraturePosition(0,0)
		self.rearRightMotor.setQuadraturePosition(0,0)
		self.frontLeftMotor.setQuadraturePosition(0,0)
		self.rearLeftMotor.setQuadraturePosition(0,0)
	def autonomousPeriodic(self):
		if self.raisedPulley == False:
			self.pulleyHeight(1,1)
		else:
			pass
		# checks switches and sensors, which feed the queue with jobs
		self.checkSwitches()
		# we are checking if a job is in the queue, and then calling the function that the first job makes using eval
		
		if len(self.queue.queue) > 0:
			
			currentJob = self.queue.peek()
			print(str(currentJob.function))
			eval(currentJob.function + currentJob.parameters)
			
			#allows the driver to drive the robot when the currentJob allows them to, using the driveLock parameter in the job
			if currentJob.driveLock == False:
				self.drive.driveCartesian(self.driveStick.getX(), self.driveStick.getY(), self.driveStick.getZ(), 0)
			
		else:
			self.drive.driveCartesian(self.driveStick.getX(), self.driveStick.getY(), self.driveStick.getZ(), 0)
			
		
	
		if self.auxiliary2.getRawButton(1) == True:
			self.adjust_ready = False
			self.checkSwitches()
			print('vision entered')
			currentPosition = self.pulleyMotor.getQuadraturePosition() 
			'''(self.IRSensor.getVoltage() > 0.1) and''' '''(self.IRSensor.getVoltage() < self.ball_dist) and '''
			if ((self.adjust_ready == False) and (self.auxiliary2.getRawButton(6) == True)): #rocket ball
				print('Quad pos is ' + str(currentPosition))
				print('entered the rocket ball')
				self.pulleyMotor.set(self.pulleyMotorModifier)
				if currentPosition > -3000:
					self.pulleyMotorModifier += 0.05
					print('moving at ' + str(self.pulleyMotorModifier))
				else:
					self.pulleyHeight(6,1) 
					self.pulleyMotorModifier =0.6
					self.adjust_ready= 1
					'''
			if (self.IRSensor.getVoltage() > 0.1)  and (self.IRSensor.getVoltage() < self.hatch_dist)  and (self.adjust_ready == 0): #rocket hatch
				self.pulleyMotorModifier = 0.05
				self.pulleyMotor.set(self.pulleyMotorModifier)
				if self.pulleyMotor.getQuadraturePosition() > 10:
					self.pulleyMotorModifier += 0.05
				else:
					self.pulleyHeight(5,1)
					self.pulleyMotorModifier =0.5
					self.adjust_ready= 1
					'''
					'''(self.IRSensor.getVoltage() > 0.1) and''' '''(self.IRSensor.getVoltage() < self.ball_dist) and'''
			if  ((self.adjust_ready == False) and (self.auxiliary2.getRawButton(7) == True)): #cargo ball
				print('entered the cargo ball')
				print('Quad pos is ' + str(currentPosition))
				if currentPosition > -3000:
					self.pulleyMotorModifier += 0.05
					print('moving at ' + str(self.pulleyMotorModifier))
					self.pulleyMotor.set(self.pulleyMotorModifier)
				else:
					self.pulleyHeight(4,1)
					self.pulleyMotorModifier =0.6
					self.adjust_ready= 1
				
			if self.adjust_ready == True:
				test = 0
				testy = 0
				testz = 0
				try:
					test = sd.getValue('adjust_x', 0)
					testy = sd.getValue('adjust_y', 0)
					testz = sd.getValue('adjust_z', 0)
					print('x ' + str(test))
					print('y ' + str(testy))
					print('z ' + str(testz))
				except Exception as e:
					print(str(e.args))
				
				self.drive.driveCartesian(self.driveStick.getX(test), self.driveStick.getY(testy), self.driveStick.getZ(testz), 0)
		
	def teleopInit(self):
		
		print('teleop starting')
		
	def checkSwitches(self):
		
		if self.auxiliary1.getRawButton(self.eStop): #E-Stop button pressed, stop all motors and remove all jobs from job queue.
			
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
			
			# for testing this button will set lead screw positions to 0
			
			'''if self.driveStick.getRawButton(1):
				print('button 1 works')
				self.crabRight(self.crab3)
			if self.driveStick.getRawButton(2):
				print('button 2 works')
				self.driveQuadratureReset()'''
			
			# buttons controlling spinBar (3 position momentary switch)
			
			if self.auxiliary2.getRawButton(self.leftLeadScrewDown): # left lead screw out manual
				self.leftLeadScrewMotor.set(self.lifterSpeed)
				#print(str(self.leftLeadScrewMotor.getQuadraturePosition()))
				
			elif self.auxiliary2.getRawButton(self.leftLeadScrewUp): # left lead screw in manual
				self.leftLeadScrewMotor.set(-1 * self.lifterSpeed)
				#print(str(self.leftLeadScrewMotor.getQuadraturePosition()))
			else:
				self.leftLeadScrewMotor.set(0)
				#print(str(self.leftLeadScrewMotor.getQuadraturePosition()))
				
			if self.auxiliary2.getRawButton(self.rightLeadScrewDown): # right lead screw out manual
				self.rightLeadScrewMotor.set(self.lifterSpeed)
			elif self.auxiliary2.getRawButton(self.rightLeadScrewUp): # right lead screw in manual
				self.rightLeadScrewMotor.set(-1 * self.lifterSpeed)
			else:
				self.rightLeadScrewMotor.set(0)
				
				
			if self.auxiliary2.getRawButton(self.spinBarIn): # cargo collecting
				#if self.IRSensor.getVoltage() < self.IRSensorThreshold: # IR distance sensor stops the spinBar from spinning in when the ball is already in
					#self.spinBarMotor.set(-1)
				#else:
					#self.spinBarMotor.set(0)
				self.spinBarMotor.set(-1)
			elif self.auxiliary2.getRawButton(self.spinBarOut): # manual cargo depositing
				self.spinBarMotor.set(1)
				
			elif self.auxiliary1.getRawButton(self.manualHatchDeposit): # manual hatch depositing
				self.spinBarMotor.set(self.hatchDepositSpeed)
				
			else:
				self.spinBarMotor.set(0)
				
			if self.auxiliary2.getRawButton(self.manualPulleyUp) and self.auxiliary2.getRawButton(1) == False: # manual pulley up
				print('you pulled pulley up')
				self.pulleyMotor.set(-1*self.pulleyMotorModifier)
				
			elif self.auxiliary2.getRawButton(self.manualPulleyDown) and self.auxiliary2.getRawButton(1) == False: # manual pulley down
				print('you pulled pulley down')
				self.pulleyMotor.set(self.pulleyMotorModifier)
			else:
				self.pulleyMotor.set(0)
				
				# buttons controlling Pulley (2 buttons and a rotary switch)
				
				# hatch buttons
				
			if self.auxiliary1.getRawButton(self.autoHatchDeposit): # hatch movement and depositing (auto)
				
				self.depositPayload(self.levelSelector(), 1)
				
				#Liam's thing
			elif self.auxiliary1.getRawButton(11):
				self.spinBarMotor.set(.2)

			
			elif self.auxiliary1.getRawButton(self.hatchCollectHeight): # hatch collecting (from player station)
				hatchCollectManual = Job()
				hatchCollectManual.function = 'self.pulleyHeight'
				hatchCollectManual.parameters = '(1, 1)'
				hatchCollectManual.driveLock = True
				self.queue.add(hatchCollectManual)
				
				
				hatchCollectManual = Job()
				hatchCollectManual.function = 'self.resetSpinBar'
				hatchCollectManual.parameters = '()'
				hatchCollectManual.driveLock = False
				self.queue.add(hatchCollectManual)
				
				
			# cargo buttons
				
			elif self.auxiliary1.getRawButton(self.autoCargoDeposit): # cargo movement and depositing
				
				self.depositPayload(self.levelSelector(), 2)
				
				
			elif self.auxiliary1.getRawButton(self.autoCargoShipDeposit): # cargo ship depositing
				x=self.levelSelector()
				self.depositPayload(self.levelSelector(), 3)
				
				
			# Pulley reset button
				
			elif self.auxiliary1.getRawButton(self.pulleyReset): # pulley reset
				resetPulley = Job()
				resetPulley.function = 'self.resetPulley'
				resetPulley.parameters = '()'
				resetPulley.driveLock = False
				self.queue.add(resetPulley)
				
				
			# buttons controlling baseLifter (3 buttons)
				
			elif self.auxiliary1.getRawButton(self.hab1to2): # hab level 1 to level 2
				self.hab(1, 2)
				
			elif self.auxiliary1.getRawButton(self.hab1to3): # hab level 1 to level 3
				self.hab(1, 3)
				
			elif self.auxiliary1.getRawButton(self.hab2to3): # hab level 2 to level 3
				self.hab(2, 3)
			else:
				pass
				
			#reset of the lead screws to drive height based on a joystick button
			while self.driveStick.getRawButton(8):
				if self.topRightLeadScrewHallEffect:
					self.rightLeadScrewMotor.set(-.3)
				else:
					self.rightLeadScrewMotor.set(0)
					self.rightLeadScrewMotor.setQuadraturePosition(0,0)
				if self.topLeftLeadScrewHallEffect:
					self.leftLeadScrewMotor.set(-.3)
				else:
					self.leftLeadScrewMotor.set(0)
					self.leftLeadScrewMotor.setQuadraturePosition(0,0)
	def teleopPeriodic(self):
		# checks switches and sensors, which feed the queue with jobs
		self.checkSwitches()
		# we are checking if a job is in the queue, and then calling the function that the first job makes using eval
		
		#print('br' + str(self.rearLeftMotor.getQuadraturePosition()))
		#print('fl' + str(self.frontLeftMotor.getQuadraturePosition()))
		
		if len(self.queue.queue) > 0:
			
			currentJob = self.queue.peek()
			print(str(currentJob.function))
			eval(currentJob.function + currentJob.parameters)
			
			#allows the driver to drive the robot when the currentJob allows them to, using the driveLock parameter in the job
			if currentJob.driveLock == False:
				self.drive.driveCartesian(self.driveStick.getX(), self.driveStick.getY(), self.driveStick.getZ(), 0)
			
		else:
			self.drive.driveCartesian(self.driveStick.getX(), self.driveStick.getY(), self.driveStick.getZ(), 0)
	
		if self.auxiliary2.getRawButton(1) == True:
			self.adjust_ready = False
			self.checkSwitches()
			#print('vision entered')
			currentPosition = self.pulleyMotor.getQuadraturePosition() 
			'''(self.IRSensor.getVoltage() > 0.1) and''' '''(self.IRSensor.getVoltage() < self.ball_dist) and '''
			if ((self.adjust_ready == False) and (self.auxiliary2.getRawButton(6) == True)): #rocket ball
				#print('Quad pos is ' + str(currentPosition))
				#print('entered the rocket ball')
				self.pulleyMotor.set(self.pulleyMotorModifier)
				if currentPosition > -3000:
					self.pulleyMotorModifier += 0.05
				#	print('moving at ' + str(self.pulleyMotorModifier))
				else:
					self.pulleyHeight(6,1) 
					self.pulleyMotorModifier =0.6
					self.adjust_ready= 1
					'''
			if (self.IRSensor.getVoltage() > 0.1)  and (self.IRSensor.getVoltage() < self.hatch_dist)  and (self.adjust_ready == 0): #rocket hatch
				self.pulleyMotorModifier = 0.05
				self.pulleyMotor.set(self.pulleyMotorModifier)
				if self.pulleyMotor.getQuadraturePosition() > 10:
					self.pulleyMotorModifier += 0.05
				else:
					self.pulleyHeight(5,1)
					self.pulleyMotorModifier =0.5
					self.adjust_ready= 1
					'''
					'''(self.IRSensor.getVoltage() > 0.1) and''' '''(self.IRSensor.getVoltage() < self.ball_dist) and'''
			if  ((self.adjust_ready == False) and (self.auxiliary2.getRawButton(7) == True)): #cargo ball
				#print('entered the cargo ball')
				#print('Quad pos is ' + str(currentPosition))
				if currentPosition > -3000:
					self.pulleyMotorModifier += 0.05
				#	print('moving at ' + str(self.pulleyMotorModifier))
					self.pulleyMotor.set(self.pulleyMotorModifier)
				else:
					self.pulleyHeight(4,1)
					self.pulleyMotorModifier =0.6
					self.adjust_ready= 1
				
			if self.adjust_ready == True:
				print('vision drive entered')
				test = 0
				testy = 0
				testz = 0
				try:
					test = sd.getValue('adjust_x', 0)
					testy = sd.getValue('adjust_y', 0)
					testz = sd.getValue('adjust_z', 0)
					print('x ' + str(test))
					print('y ' + str(testy))
					print('z ' + str(testz))
				except Exception as e:
					print(str(e.args))
				
				self.drive.driveCartesian(self.driveStick.getX(testx), self.driveStick.getY(testy), self.driveStick.getZ(testz), 0)
		
				
				
			
if __name__ == "__main__":
	wpilib.run(MyRobot)
