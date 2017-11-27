import networkx as nx
import numpy as np
import random
import operator
import matplotlib.pyplot as plt
import math

# Garage related parameters
floors = 4
capacityPerFloor = 50*np.ones(floors)
coverageProbFloor = [0.9, 0.8, 0.7, 0.2]
inCoverageCapacity = capacityPerFloor * coverageProbFloor
occupancy = np.zeros(floors)

# Probability of Relay capable UEs among universe
relayProb = 0.3

#Traffic parameters
poissonLambda = 1/5 #1/10 # Arrival rate of vehicles per minute
# Parking duration distribution (Weibull)
scale_par = 45.7422
shape_par = 0.6039

class Vehicle:

    def __init__(self):
        """

        :rtype: object
        """
        self.id = random.randint(1, 1000)
        #self.active = True
        self.parkDuration = int(scale_par*np.random.weibull(shape_par))
        self.remainingTime =  self.parkDuration
        self.batteryLevel = 10
        self.relayCap = (0 if random.random() > relayProb else 1)
        self.position = [0,0]
        self.floor = 0
        self.connectedList = []

class BaseStation:

    def __init__(self):
        self.id = 0
        self.active = True
        self.connectedList = []

# Helper function for vehicle arrival times

def accumulate(iterable, func=operator.add):
    'Return running totals'
    # accumulate([1,2,3,4,5]) --> 1 3 6 10 15
    # accumulate([1,2,3,4,5], operator.mul) --> 1 2 6 24 120
    it = iter(iterable)
    total = next(it)
    yield total
    for element in it:
        total = func(total, element)
        yield total


#Sim parameters
simTime = 1000
arrivalsPerUnitTime = 200
avgInterArrivalTime = float(1/float(arrivalsPerUnitTime))
totalCars = int(simTime/avgInterArrivalTime)
interArrivalTimes = [round(random.expovariate(avgInterArrivalTime)) for i in range(10*totalCars)]
arrivalTimes = list(accumulate(interArrivalTimes))

#print '[%s]' % ', '.join(map(str, interArrivalTimes))
print '[%s]' % ', '.join(map(str, arrivalTimes))

#Init Graph
G = nx.Graph()
bs = BaseStation()
G.add_node(bs)
toBeRemoved = nx.Graph()  # Create a sub-graph of nodes to be removed in every iteration
#Graph params
sizeG = []

#Sim loop
for t in range(0,simTime,1):
    if arrivalTimes.count(t) > 0:
        #New arrival
        print "Iter: %d New Arrival(s): %d vehicle(s)" % (t , arrivalTimes.count(t))
        for vehi in range(1, arrivalTimes.count(t)+1):
            if np.any(np.greater(capacityPerFloor,occupancy)): #Available parking in garage
                v = Vehicle()
                print "Park duration: %d" % v.parkDuration
                tmp = np.greater_equal(occupancy, inCoverageCapacity)
                if np.all(tmp) == 'True': #UE out of coverage of BS
                    # UE must connect to in coverage UE..
                    # Assign a floor to UE based on prioritized list of floors (this will change for coverage optimized deployment)
                    print "Adding vehicle out-of-coverage"
                    v.floor = tmp.index('True')
                    #v.active = True
                    # TODO: Update v.connectedList according to graph status (ex. radio distance..)
                    G.add_node(v)
                    occupancy[v.floor] = occupancy[v.floor] +1
                    v.connectedList = (n for n in G if G.node[n].floor == v.floor)
                else:   #UE in coverage of BS..
                    print "Adding vehicle in-coverage"
                    v.floor = np.nonzero(tmp==0)[0]
                    v.active = True
                    # TODO: Update v.connectedList according to graph status (ex. radio distance..)
                    G.add_node(v)
                    occupancy[v.floor] = occupancy[v.floor] +1
                    v.connectedList = (n for n in G if G.node[n].floor == v.floor)

            else:
                print "No space available in parking lot!"

    # Now do common bookkeeping..
    for n in G.nodes():
        if n.id != 0:
            n.remainingTime = n.remainingTime - 1
            if n.remainingTime == 0:
                toBeRemoved.add_node(n)
                occupancy[n.floor] = occupancy[n.floor] - 1
                print "Removing vehicle %d" % n.id

    G.remove_nodes_from(toBeRemoved)
    toBeRemoved.clear()

    sizeG.append(G.number_of_nodes())
    print "Number of vehicles: %d" % len(G)


# Results plotting..
plt.grid()
plt.figure(1)
plt.plot(sizeG)
plt.ylabel('Number of vehicles')
plt.xlabel('Time (mins)')

plt.figure(2)
plt.grid()
plt.bar([1, 2 ,3 ,4],np.divide(occupancy,capacityPerFloor))
plt.xlabel('Floor')
plt.ylabel('Occupancy Ratio')
plt.ylim([0 , 1])
plt.xticks([1 ,2 ,3 ,4])



plt.show()