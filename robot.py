import ctre, wpilib,

ticksPerInch = 30 # 30 ticks per inch is just a guess, the number is probably different


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
	
	self.ds = wpilib.DriverStation.getInstance()
	
	frontLeftChannel = 0
	frontRightChannel = 0
	rearLeftChannel = 0
	rearRightChannel = 0
	leftLeadScrewChannel = 0
	rightLeadScrewChannel = 0
	PulleyChannel = 0
	spinBarChannel = 0
	
	self.frontLeftMotor = ctre.WPI_TalonSRX(frontLeftChannel)
	self.frontRightMotor = ctre.WPI_TalonSRX(frontRightChannel)
	self.rearLeftMotor = ctre.WPI_TalonSRX(rearLeftChannel)
	self.rearRightMotor = ctre.WPI_TalonSRX(rearRightChannel)
	self.leftLeadScrewMotor = ctre.WPI_TalonSRX(leftLeadScrewChannel)
	self.rightLeadScrewMotor = ctre.WPI_TalonSRX(rightLeadScrewChannel)
	self.PulleyMotor = ctre.WPI_TalonSRX(mastMotorChannel)
	self.spinBarMotor = ctre.WPI_TalonSRX(spinBarChannel)
	
	self.PulleyMotor = (self.PulleyMotor * 0.5) # slows down the Pulley motor speed just in case it goes way too fast
	
	def levelSelector():
	volts = wpilib.AnalogInput(1).getVoltage()
		if volts < 1.1:
			return(1)
		elif volts < 2.1:
			return(2)
		elif volts < 3.1:
			return(3)
	
	def pulleyHeight(level, payload): # payload 1 is hatch, payload 2 is cargo, payload 3 is cargo ship cargo
		'''Moves the Pulley to certain levels, with a certain offset based on hatch or cargo. The cargo ship has a unique offset (supposedly), and the hatch has no offset.'''
		
		currentPosition = self.PulleyMotor.getQuadraturePosition()
		
		if payload == 1:
			if level == 1:
				goalPosition = self.inches * 20
			elif level == 2:
				goalPosition = self.inches * 48
			else: # level 3 is the only other option the Pulley has, so the else is for level 3
				goalPosition = self.inches * 76
		elif payload == 2:
			if level == 1:
				goalPosition = self.inches * 36
			elif level == 2:
				goalPosition = self.inches * 64
			else:
				goalPosition = self.inches * 92
		else:
			return()
		
		if currentPosition < (goalPosition - (self.inches * 0.5)):
			self.PulleyMotor.set(0.5)
		elif currentPosition > (goalPosition + (self.inches * 0.5)):
			self.PulleyMotor.set(-0.5)
		else:
			self.PulleyMotor.set(0)
			
		
	# insert functions
	def robotInit(self):
		"""Robot initialization function"""
	def autonomousInit(self):
		pass
	def autonomousPeriodic(self):
		pass
	def teleopInit(self):
		self.PulleyMotor.setQuadraturePosition((self.inches * 5), 0)
		
	def checkSwitches(self):
	
		if E-Stop == 1: #E-Stop button pressed, stop all motors and remove all jobs from job queue.
			self.frontLeftMotor = 0
			self.frontRightMotor = 0
			self.rearLeftMotor = 0
			self.rearRightMotor = 0
			self.leftLeadScrewMotor = 0
			self.rightLeadScrewMotor = 0
			self.PulleyMotor = 0
			self.spinBarMotor = 0
			#Remove all queued Jobs
			
			'''
			for i in (len(self.queue) - 1):
				self.queue.remove()
			'''
			
		else: #Check every other switch
			
			
			
			# buttons controlling spinBar (3 position momentary switch)
			
			if wpilib.AnalogInput(0).getVoltage() < 2.5: # if ball is sensed by IR, spinBarMotor set to 0
			
				if self.ds.getStickButton(0, 1): # spinBar in
					spinBar = Job()
					spinBar.function = 'spinBar'
					spinBar.parameters = '(-1)' # -1 is supposed to mean full speed in, but is just a guess
					spinBar.driveLock = False
					self.queue.add(spinBar)
					
				elif self.ds.getStickButton(0, 2): # spinBar out
					spinBar = Job()
					spinBar.function = 'spinBar'
					spinBar.parameters = '(1)'
					spinBar.driveLock = False
					self.queue.add(spinBar)
			else:
				self.spinBarMotor.set(0)
			
			
			
			# buttons controlling Pulley (2 buttons and a rotary switch)
			
			# hatch buttons
			
			if self.ds.getStickButton(0, 3): # hatch Pulley height
				pulleyHeightHatch = Job()
				pulleyHeightHatch.function = 'pulleyHeight'
				pulleyHeightHatch.parameters = '(' + str(self.levelSelector) + ', 1)' # first parameter is the level, the second parameter is added height based on hatch or cargo
				pulleyHeightHatch.driveLock = True
				self.queue.add(pulleyHeightHatch)
				
			elif self.ds.getStickButton(0, 4):
				collectHatch = Job()
				collectHatch.function = 'collectHatch'
				collectHatch.parameters = '()'
				collectHatch.driveLock = True
				self.queue.add(collectHatch)
				
			# cargo buttons
				
			elif self.ds.getStickButton(0, 5): # cargo Pulley height
				pulleyHeightCargo = Job()
				pulleyHeightCargo.function = 'pulleyHeight'
				pulleyHeightCargo.parameters = '(' + str(self.levelSelector) + ', 2)'
				pulleyHeightCargo.driveLock = True
				self.queue.add(pulleyHeightCargo)
				
			elif self.ds.getStickButton(0, 6): # cargo ship Pulley height
				pulleyHeightCargoShip = Job()
				pulleyHeightCargoShip.function = 'pulleyHeight'
				pulleyHeightCargoShip.parameters = '(1, 3)' # random number for cargo ship height
				
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
		
		checkSwitches()
if __name__ == "__main__":
	wpilib.run(MyRobot)
