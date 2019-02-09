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





#Example 2
def add(first, second):
    return(str(first+second))

def factorial(number):
    result=1
    for i in range(1,number+1):
        result=result*i
    return(result)


JobQueue=FIFOQueue()

job1=Job()
job1.function="add"
job1.parameters="(2,6)"
job1.drivelock=1
JobQueue.add(job1)


job2=Job()
job2.function="factorial(iteration)"
job2.parameters=""
JobQueue.add(job2)



#For each job JobQueue, evaluate the expression and execute.
#Run each job five times before removing from queue.
iteration=1
while len(JobQueue.queue)>0:
    if iteration<6:
        print("Queue Length:" + str(len(JobQueue.queue)))
        CurrentJob=JobQueue.peek()
        print(eval(CurrentJob.function+CurrentJob.parameters))
        iteration=iteration+1
    else:
        print("Removing job")
        JobQueue.remove()
        iteration=1


