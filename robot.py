import ctre, wpilib,




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
	
	
	
	self.queue = Queue()
	
	frontLeftChannel = 0
	frontRightChannel = 0
	rearLeftChannel = 0
	rearRightChannel = 0
	leftLeadScrewChannel = 0
	rightLeadScrewChannel = 0
	pullyChannel = 0
	spinBarChannel = 0
	
	self.frontLeftMotor = ctre.WPI_TalonSRX(frontLeftChannel)
	self.frontRightMotor = ctre.WPI_TalonSRX(frontRightChannel)
	self.rearLeftMotor = ctre.WPI_TalonSRX(rearLeftChannel)
	self.rearRightMotor = ctre.WPI_TalonSRX(rearRightChannel)
	self.leftLeadScrewMotor = ctre.WPI_TalonSRX(leftLeadScrewChannel)
	self.rightLeadScrewMotor = ctre.WPI_TalonSRX(rightLeadScrewChannel)
	self.pullyMotor = ctre.WPI_TalonSRX(mastMotorChannel)
	self.spinBarMotor = ctre.WPI_TalonSRX(spinBarChannel)
	
	
	def levelSelector():
	volts = wpilib.AnalogInput(1).getVoltage()
		if volts < 1.1:
			return(1)
		elif volts < 2.1:
			return(2)
		elif volts < 3.1:
			return(3)
	
	def pullyHeight(level, offset)
		'''Moves the pully to certain levels, with a certain offset based on hatch or cargo. The cargo ship has a unique offset (supposedly), and the hatch has no offset.'''
		
	def spinBar(direction)
		'''Spins the manipulator either in or out for gathering or depositing the cargo and hatches. Positive 1 rotates cargo out of the manipulator.
		Negative 1 rotates the cargo into the manipulator. The direction parameter determines this number.'''
		
	# insert functions
	
	def robotInit(self):
		"""Robot initialization function"""
	def autonomousInit(self):
		pass
	def autonomousPeriodic(self):
		pass
	def teleopInit(self):
		
	def teleopPeriodic(self):
		
		# buttons controlling spinBar (3 position momentary switch)
		if self.ds.getStickButton(0, 1): # spinBar in
			spinBar = Job()
			spinBar.function = 'spinBar'
			spinBar.parameters = '(-1)' # -1 is supposed to mean full speed in, but is just a guess
			spinBar.driveLock = False
			self.queue.add(spinBar)
		if self.ds.getStickButton(0, 2): # spinBar out
			spinBar = Job()
			spinBar.function = 'spinBar'
			spinBar.parameters = '(1)'
			spinBar.driveLock = False
			self.queue.add(spinBar)
		if wpilib.AnalogInput(0).getVoltage() > 2.5: # if ball is sensed by IR, spinBarMotor set to 0
			self.spinBarMotor.set(0)
		# buttons controlling pully (2 buttons and a rotary switch)
		if self.ds.getStickButton(0, 3): # hatch pully height
			pullyHeightHatch = Job()
			pullyHeightHatch.function = 'pullyHeight'
			pullyHeightHatch.parameters = '(' + str(self.levelSelector) + ', 0)' # first parameter is the level, the second parameter is added height based on hatch or cargo
			pullyHeightHatch.driveLock = True
			self.queue.add(pullyHeightHatch)
		if self.ds.getStickButton(0, 3): # cargo pully height
			pullyHeightCargo = Job()
			pullyHeightCargo.function = 'pullyHeight'
			pullyHeightCargo.parameters = '(' + str(self.levelSelector) + ', 20)' # 20 is random number representing difference in height between hatch and cargo spots
			pullyHeightCargo.driveLock = True
			self.queue.add(pullyHeightCargo)
		if self.ds.getStickButton(0, 4): # cargo ship pully height
			pullyHeightCargoShip = Job()
			pullyHeightCargoShip.function = 'pullyHeight'
			pullyHeightCargoShip.parameters = '(1, 25)' # random number for cargo ship height
		# buttons controlling baseLifter
		if self.ds.getStickButton(0, 5):
			
		
if __name__ == "__main__":
	wpilib.run(MyRobot)
