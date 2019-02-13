import ctre, wpilib


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
		if len(self.queue) > 0
			return(self.queue.pop())
		else:
			return()

class MyRobot(wpilib.TimedRobot):
	
	self.ticksPerInchPulley = 30 # 30 ticks per inch is just a guess, the number is probably different
	self.ticksperInchLifter = 30
	self.ticksperInchWheels = 30
	self.ticksperInchCrabbing = 31
	
	self.queue = Queue()
	
	self.ds = wpilib.DriverStation.getInstance()
	
	self.hatch1HeightInches = 20 # these numbers are just guesses, and are in inches
	self.hatch2HeightInches = 48
	self.hatch3HeightInches = 76
	
	self.cargo1HeightInches = 28
	self.cargo2HeightInches = 56
	self.cargo3HeightInches = 84
	
	self.frontLeftChannel = 0
	self.frontRightChannel = 0
	self.rearLeftChannel = 0
	self.rearRightChannel = 0
	self.leftLeadScrewChannel = 0
	self.rightLeadScrewChannel = 0
	self.pulleyChannel = 0
	self.spinBarChannel = 0
	
	self.frontLeftMotor = ctre.WPI_TalonSRX(self.frontLeftChannel)
	self.frontRightMotor = ctre.WPI_TalonSRX(self.frontRightChannel)
	self.rearLeftMotor = ctre.WPI_TalonSRX(self.rearLeftChannel)
	self.rearRightMotor = ctre.WPI_TalonSRX(self.rearRightChannel)
	self.leftLeadScrewMotor = ctre.WPI_TalonSRX(self.leftLeadScrewChannel)
	self.rightLeadScrewMotor = ctre.WPI_TalonSRX(self.rightLeadScrewChannel)
	self.pulleyMotor = ctre.WPI_TalonSRX(self.pulleyChannel)
	self.spinBarMotor = ctre.WPI_TalonSRX(self.spinBarChannel)
	
	self.drive = MecanumDrive(
			self.frontLeftMotor,
			self.rearLeftMotor,
			self.frontRightMotor,
			self.rearRightMotor,
		)
	
	self.pulleyMotorModified = (self.pulleyMotor * 0.5) # slows down the Pulley motor speed just in case it goes way too fast
	self.pulleyDeadbandInches = .5 #how many inches we are okay with the pulley being off (to avoid the jiggle)
	
	def hab(startLevel, goalLevel):
		raiseBase(startLevel, goalLevel)
		crabLeft(self.crab1)
		raiseLeft(startLevel,goalLevel)
		crabLeft(self.crab2)
		lowerLeft(goalLevel)
		raiseRight(startLevel,goalLevel)
		crabLeft(self.crab3)
		lowerRight(goalLevel)
		crabLeft(self.crab4)
		
	def depositPayload(level, payload):
		align()
		pullyHeight(level, payload)
		dispense(payload)
		
	def align():
		
		
	def spinBar(velocity):
		self.spinBarMotor.set(velocity)
		
	#to bring the pulley back to its starting height
	def resetPulley(): 
		#go down until the hall effect sensor reads the magnet, then stop and set
		#encoder value to 0
		
	def collectHatch():
		
		
		
	def levelSelector():
		'''This function returns the level as an integer by checking the rotary switch controlling rocket level.'''
		
		volts = wpilib.AnalogInput(1).getVoltage()
		if volts < 0.1:
			return(0)
		elif volts < 1.1:
			return(1)
		elif volts < 2.1:
			return(2)
		elif volts < 3.1:
			return(3)
		
	def pulleyHeight(level, payload): # level 0 is the floor, payload 1 is hatch, payload 2 is cargo, payload 3 is cargo ship cargo(not done yet)
		'''Moves the Pulley to certain levels, with a certain offset based on hatch or cargo. The cargo ship has a unique offset (supposedly), and the hatch has no offset.'''
		
		currentPosition = self.pulleyMotorModified.getQuadraturePosition()
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
			return()
			
		if currentPosition < (goalPosition - (self.ticksPerInchPulley * self.pulleyDeadbandInches)): # this sets a deadband for the encoders on the pulley so that the pulley doesnt go up and down forever
			self.pulleyMotorModified.set(0.5)
		elif currentPosition > (goalPosition + (self.ticksPerInchPulley * self.pulleyDeadbandInches)):
			self.pulleyMotorModified.set(-0.5)
		else:
			self.pulleyMotorModified.set(0)
		
	def dispense(payload):
	
		if payload == 1:
			self.spinBarMotor.set(1)
		elif payload == 2:
			self.spinBarMotor.set(0.1) #add code to drive backward slightly
		

	# insert functions
	def robotInit(self):
		"""Robot initialization function"""
		
	def autonomousInit(self):
		pass
	def autonomousPeriodic(self):
		pass
	def teleopInit(self):
		pass
	def checkSwitches(self):
		
		if E-Stop == 1: #E-Stop button pressed, stop all motors and remove all jobs from job queue.
			
			self.frontLeftMotor = 0
			self.frontRightMotor = 0
			self.rearLeftMotor = 0
			self.rearRightMotor = 0
			self.leftLeadScrewMotor = 0
			self.rightLeadScrewMotor = 0
			self.pulleyMotorModified = 0
			self.spinBarMotor = 0
			
			#Remove all queued Jobs
			
			for i in (len(self.queue.queue) - 1):
				self.queue.remove()
			
			
		else: #Check every other switch
			
			
			# buttons controlling spinBar (3 position momentary switch)
			
			
				pass
				
			if self.ds.getStickButton(0, 1): # spinBar in
				if wpilib.AnalogInput(0).getVoltage() < 2.5: # this isn't doing anything because the IR sensor has lost it's original purpose of detecting cargo or hatch
					self.spinBarMotor.set(-1)
				else:
					self.spinBarMotor.set(0)
					
				
			elif self.ds.getStickButton(0, 2): # spinBar out
				self.spinBarMotor.set(1)
				
			else:
				self.spinBarMotor.set(0)
			
			
			
			# buttons controlling Pulley (2 buttons and a rotary switch)
			
			# hatch buttons
			
			if self.ds.getStickButton(0, 3): # hatch Pulley height
				pulleyHeightAndDepositHatch = Job()
				pulleyHeightAndDepositHatch.function = 'pulleyHeightAndDeposit'
				pulleyHeightAndDepositHatch.parameters = '(' + str(self.levelSelector) + ', 1)' # first parameter is the level, the second parameter is added height based on hatch or cargo
				pulleyHeightAndDepositHatch.driveLock = True
				self.queue.add(pulleyHeightAndDepositHatch)
				
			elif self.ds.getStickButton(0, 4):
				collectHatch = Job()
				collectHatch.function = 'collectHatch'
				collectHatch.parameters = '()'
				collectHatch.driveLock = True
				self.queue.add(collectHatch)
				
			# cargo buttons
				
			elif self.ds.getStickButton(0, 5): # cargo Pulley height
				pulleyHeightAndDepositCargo = Job()
				pulleyHeightAndDepositCargo.function = 'pulleyHeightAndDeposit'
				pulleyHeightAndDepositCargo.parameters = '(' + str(self.levelSelector) + ', 2)'
				pulleyHeightAndDepositCargo.driveLock = True
				self.queue.add(pulleyHeightAndDepositCargo)
				
			elif self.ds.getStickButton(0, 6): # cargo ship Pulley height
				pulleyHeightAndDepositCargoShip = Job()
				pulleyHeightAndDepositCargoShip.function = 'pulleyHeightAndDeposit'
				pulleyHeightAndDepositCargoShip.parameters = '(1, 3)' # random number for cargo ship height
				
			# Pulley reset button
				
			elif self.ds.getStickButton(0, 7): # Pulley reset
				resetPulley = Job()
				resetPulley.function = 'resetPulley'
				resetPulley.parameters = '()'
				resetPulley.driveLock = False
				self.queue.add(resetPulley)
				
				
				
			# buttons controlling baseLifter (3 buttons)
			
			if self.ds.getStickButton(0, 8): # hab level 1 to level 2
				hab = Job()
				hab.function = 'hab'
				hab.parameters = '(1, 2)'
				hab.driveLock = True
				self.queue.add(hab)
				
			elif self.ds.getStickButton(0, 9): # hab level 1 to level 3
				hab = Job()
				hab.function = 'hab'
				hab.parameters = '(1, 3)'
				hab.driveLock = True
				self.queue.add(hab)
				
			elif self.ds.getStickButton(0, 10): # hab level 2 to level 3
				hab = Job()
				hab.function ='hab'
				hab.parameters = '(2, 3)'
				hab.driveLock = True
				self.queue.add(hab)
				
	def teleopPeriodic(self):
		
		# checks switches and sensors, which feed the queue with jobs
		checkSwitches()
		
		# we are checking if a job is in the queue, and then calling the function that the first job makes using eval
		if len(self.queue.queue) > 0:
			currentJob = self.queue.queue.peek()
			eval(currentJob.function + currentJob.parameters)
		
		# allows the driver to drive the robot when the currentJob allows them to, using the driveLock parameter in the job
		if currentJob.drivelock = False:
			self.drive.driveCartesian(
					self.stick.getX(), self.stick.getY(), self.stick.getZ(), 0
				)
		
if __name__ == "__main__":
	wpilib.run(MyRobot)
