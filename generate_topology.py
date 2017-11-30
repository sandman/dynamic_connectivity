import networkx as nx
import numpy as np
import random
import operator
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.spatial.distance import cdist
import math

random.seed(datetime.now())

# Garage related parameters
floors = 4
capacityPerFloor = 40  # Only supports same capacity for all floors
capacityOfFloors = capacityPerFloor*np.ones(floors)
coverageProbFloor = [0.9, 0.8, 0.7, 0.2]
inCoverageCapacity = capacityOfFloors * coverageProbFloor
occupancy = np.zeros(floors)

#positions in the garage
x_pos = [5*(i+1) for i in range(10)]
y_pos = [3, 14, 19, 30]
z_pos = [2, 6, 10, 14]
positions = [[x,y,z] for z in z_pos for y in y_pos for x in x_pos]
availPositions = positions
# Probability of Relay capable UEs among universe
relayProb = 0.3

#Traffic parameters
# Parking duration distribution (Weibull) - Data Analytics for Smart Parking Applications http://www.mdpi.com/1424-8220/16/10/1575/pdf
scale_par = 45.7422
shape_par = 0.6039

#Radio propagation parameters
ple = 2.5 # Path Loss Exponent
minSINR = 0 # SINR Threshold in dB

class Vehicle:

    def __init__(self):
        """

        :rtype: object
        """
        self.id = random.randint(1, 1000)
        #self.active = True
        self.remainingTime =  round(scale_par*np.random.weibull(shape_par))
        self.batteryLevel = 10
        self.relayCap = (0 if random.random() > relayProb else 1)
        self.position = [0,0,0]
        self.floor = 0
        self.connectedList = []
        self.transmitPower = 0.02 # Transmit power in W

class BaseStation:

    def __init__(self):
        self.id = 0
        self.active = True
        self.connectedList = []
        self.position = [200, 200, 50]
        self.transmitPower = 40 # Transmit power in W

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
simTime = 200
arrivalsPerUnitTime = 0.700
avgInterArrivalTime = float(1/float(arrivalsPerUnitTime))
totalCars = int(simTime/avgInterArrivalTime)
interArrivalTimes = [round(random.expovariate(avgInterArrivalTime)) for i in range(100*totalCars)]
arrivalTimes = list(accumulate(interArrivalTimes))

#print '[%s]' % ', '.join(map(str, interArrivalTimes))
#print '[%s]' % ', '.join(map(str, arrivalTimes))

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
            if np.any(np.greater(capacityOfFloors,occupancy)): #Available parking in garage
                v = Vehicle()
                #print "Park duration: %d" % v.remainingTime
                tmp = np.greater_equal(occupancy, inCoverageCapacity)
                if np.all(tmp): #UE out of coverage of BS
                    # UE must connect to in coverage UE..
                    # Assign a floor to UE based on prioritized list of floors (this will change for coverage optimized deployment)
                    #print "Adding vehicle out-of-coverage"
                    v.floor = np.nonzero(tmp)[0][0]
                    # idx = capacityPerFloor*v.floor + np.random.randint(capacityPerFloor)
                    # v.position = availPositions[idx]

                    # Randomly select an available position from the selected floor
                    v.position = random.choice([item for item in availPositions if item[2] == z_pos[v.floor]])
                    availPositions.remove(v.position) #Remove the selected position from the list of available positions

                    #v.active = True
                    # TODO: Update v.connectedList according to graph status (ex. radio distance..)
                    G.add_node(v)
                    occupancy[v.floor] = occupancy[v.floor] +1
                    v.connectedList = (n for n in G if G.node[n].floor == v.floor)
                    print 'Adding out-of-coverage. Occupancy: [%s]' % ', '.join(map(str, occupancy))
                else:   #UE in coverage of BS..
                    #print "Adding vehicle in-coverage"
                    v.floor = np.nonzero(tmp==0)[0][0]
                    v.position = random.choice([item for item in availPositions if item[2] == z_pos[v.floor]])
                    availPositions.remove(v.position) #Remove the selected position from the list of available positions
                    v.active = True
                    # TODO: Update v.connectedList according to graph status (ex. radio distance..)

                    #posList = [(n.position,n.id) for n in G]
                    #distances = cdist(v.position,[item[0] for item in posList],'euclidean')
                    posList = [n.position for n in G]
                    distances = cdist(v.position, posList, 'euclidean')
                    #nDistances = distances[:G.__len__()]
                    rDistances = np.power(distances, -ple)
                    Pi = v.transmitPower*np.ones(G.__len__())
                    Pk = [n.transmitPower for n in G]

                    w_forward = np.multiply(Pi,rDistances)
                    w_backward = np.multiply(Pk,rDistances)

                    for idx, w in enumerate(w_forward):
                        tmp = [w_backward[i] for i in range(w_backward.size) if i != idx]
                        linkForward.append(float(x / float(sum(tmp))))
                        print "x: %d sum: %f" % (x, sum(tmp))

                    for idx, w in enumerate(w_backward):
                        tmp



                    #print nDistances
                    G.add_node(v)
                    elist = [(v, n) for n in G if n.floor == v.floor]
                    G.add_edges_from(elist)
                    occupancy[v.floor] = occupancy[v.floor] +1
                    v.connectedList = (n for n in G if G.node[n].floor == v.floor)
                    print 'Adding in-coverage. Occupancy: [%s]' % ', '.join(map(str, occupancy))

            else:
                print "No space available in parking lot!"

    # Now do common bookkeeping..
    for n in G.nodes():
        if n.id != 0:
            n.remainingTime = n.remainingTime - 1
            if n.remainingTime <= 0:
                toBeRemoved.add_node(n)
                occupancy[n.floor] = occupancy[n.floor] - 1
                availPositions.append(n.position)  # Add the position back to the list of available positions
                #print "Removing vehicle %d" % n.id

    #print "Before deletion: %d" % len(G)
    G.remove_nodes_from(toBeRemoved)
    if toBeRemoved:
        print "Deleted: %d nodes. Total nodes: %d " % (len(toBeRemoved), (len(G)-1))
    toBeRemoved.clear()
    sizeG.append(len(G)-1)
    #print "Number of vehicles: %d" % (len(G) - 1)

print "End of simulation."

A = nx.adjacency_matrix(G)
print A

# Results plotting..
plt.grid()
plt.figure(1)
plt.plot(sizeG)
plt.ylabel('Number of vehicles')
plt.xlabel('Time (mins)')

plt.figure(2)
plt.grid()
plt.bar([1, 2 ,3 ,4],np.divide(occupancy,capacityOfFloors))
plt.xlabel('Floor')
plt.ylabel('Occupancy Ratio')
plt.ylim([0 , 1])
plt.xticks([1 ,2 ,3 ,4])



plt.show()