class Job:
    def __init__(self):
        self.function = ""  #Name of function to call
        self.parameters = "()"  #Parameters to pass to function.  Always put inside ().
        self.drivelock=0    #Boolean value denoting whether user input for drive is honored.

class FIFOQueue:
    def __init__(self):
        self.queue = list()

    #add will put the passed item on the back end of the list.
    def add(self, item):
        self.queue.insert(0,item)

    #peek will return the value of the object at the front of the FIFO queue, but leave it in the list.
    def peek(self):
        QueueLength=len(self.queue)
        if QueueLength > 0:
            return(self.queue[QueueLength-1])
        else:
            return()

    #remove will return the value of the oject at the front of the FIFO queue AND remove it from the FIFO queue.
    def remove(self):
        if len(self.queue)>0:
            return(self.queue.pop())
        else:
            return()


#Example 1

JobQueue=FIFOQueue()
for i in range(0,3):
    JobQueue.add(i)
print("Queue Length: "+ str(len(JobQueue.queue)))
print("Job Queue: " + str(JobQueue.queue))
print("Peeking: " + str(JobQueue.peek()))
print("")
print("Queue Length: "+ str(len(JobQueue.queue)))
print("Job Queue: " + str(JobQueue.queue))
print(JobQueue.remove())
print("")
print("Queue Length: "+ str(len(JobQueue.queue)))
print(JobQueue.queue)
print("")
print("")

