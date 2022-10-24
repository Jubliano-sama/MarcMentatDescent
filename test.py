from py_mentat import *
import os
from time import sleep

#list that links elements to a connected node to check isolated forces
elementNodeDictionary = {
    1:1,
    2:3,
    5:2,
    7:4,
    8:6,
    10:6,
    3:5,
    4:2,
    11:14,
    9:4,
    12:2,
    76:3,
    79:5,
    82:2,
    83:2,
    61:4
}

nodeMaxXDictionary = {
17:1100,
14:1100,
4:500,
6:500,
2:500 }

nodeMinXDictionary = {
17:-500,
14:1100,
4:0,
6:0,
2:-500 }

nodeMaxYDictionary = {
17:900,
14:500,
4:900,
6:900,
2:900 }

nodeMinYDictionary = {
17:500,
14:500,
4:500,
6:500,
2:0 }

#6 not included, because it's set to change symmetrically with 4
changeableNodes = {17,14,2,4}

jobPath = "C:\\Users\\tommi\\Downloads\\design_2_tommie_backup_job1.t16"
#0.1 initally, lower for more precision is recommended
stepSize = 0.1

#gets the maximum buckling force present in loaded job
def getMaxBucklingForce():
    py_send("*post_numerics")
    py_send("*post_value Comp 11 of Stress")
    max = 0
    for key, value in elementNodeDictionary.items():
        py_send("*post_deisolate_elements all_existing")
        py_send("post_isolate_elements " + str(key) + " #")
        length = py_get_float("element_edge_length(" + str(key) + ",0)")
        force = py_get_float("scalar_2(" + str(value) + ")")
        if force < 0:
            bucklingForce = length**2 * force
            if max > bucklingForce:
                max = bucklingForce
    return max

#determines the direction a node should move in (if any) to lessen buckling force
def determineGradientForNode(nodeNumber):
    #if node is not middle node(because they need to move symmetrically)
    if nodeNumber != 6 and nodeNumber != 4:
        #get baseline number
        submitAndOpenJob()
        baseline = getMaxBucklingForce()
        py_send("*post_close")

        #get coordinates of node
        x = py_get_float("node_x(" + str(nodeNumber) + ")")
        y = py_get_float("node_y(" + str(nodeNumber) + ")")
        z = py_get_float("node_z(" + str(nodeNumber) + ")")
        
        #determine x gradient
        py_send("*edit_nodes " + str(nodeNumber) + " " + str(x + 0.1) + " " + str(y) + " " + str(z))
        submitAndOpenJob()
        xgradient = (baseline - getMaxBucklingForce())
        py_send("*post_close")
        #reset
        py_send("edit_nodes " + str(nodeNumber) + " " + str(x) + " " + str(y) + " " + str(z))
        
        #determine y gradient
        py_send("*edit_nodes " + str(nodeNumber) + " " + str(x) + " " + str(y + 0.1) + " " + str(z))
        submitAndOpenJob()
        ygradient = (baseline - getMaxBucklingForce())
        py_send("*post_close")
        #reset
        py_send("edit_nodes " + str(nodeNumber) + " " + str(x) + " " + str(y) + " " + str(z))
        
        return(xgradient, ygradient)
        
    else:
        #get baseline number
        submitAndOpenJob()
        baseline = getMaxBucklingForce()
        py_send("*post_close")

        #get coordinates of node
        x = py_get_float("node_x " + str(nodeNumber))
        y = py_get_float("node_y " + str(nodeNumber))
        z = py_get_float("node_z " + str(nodeNumber))
        
        #determine x gradient
        py_send("edit_nodes " + str(4) + " " + str(x + 0.1) + " " + str(y) + " " + str(z))
        py_send("edit_nodes " + str(6) + " " + str(x + 0.1) + " " + str(y) + " " + str(z))
        submitAndOpenJob()
        xgradient = (baseline - getMaxBucklingForce())
        py_send("*post_close")
        #reset
        py_send("edit_nodes " + str(4) + " " + str(x) + " " + str(y) + " " + str(z))
        py_send("edit_nodes " + str(6) + " " + str(x) + " " + str(y) + " " + str(z))
        
        
        #determine y gradient
        py_send("edit_nodes " + str(4) + " " + str(x) + " " + str(y + 0.1) + " " + str(z))
        py_send("edit_nodes " + str(6) + " " + str(x) + " " + str(y + 0.1) + " " + str(z))
        submitAndOpenJob()
        ygradient = (baseline - getMaxBucklingForce())
        py_send("*post_close")
        #reset
        py_send("edit_nodes " + str(4) + " " + str(x) + " " + str(y) + " " + str(z))
        py_send("edit_nodes " + str(6) + " " + str(x) + " " + str(y) + " " + str(z))
        return(xgradient, ygradient)
    

def submitAndOpenJob():
    if os.path.exists(jobPath):
        os.remove(jobPath)
    py_send("*submit_job 1")
    while not os.path.exists(jobPath):
        sleep(0.1)
    py_send("*post_open_default")
  
#clamps number between min and max value
def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)    

#performs gradient descent on model
def updateDesign():
    updateCoords = []
    for node in changeableNodes:
        py_send(str(node))
        rawx, rawy = determineGradientForNode(node)
        updateCoords.append([node, rawx*stepSize*-1, rawy*stepSize*-1])
    for update in updateCoords:
        #if not middle node
        if update[0] != 4 and update[0] != 6:
            #saves current node coords to base update on
            x = py_get_float("node_x(" + str(update[0]) + ")")
            y = py_get_float("node_y(" + str(update[0]) + ")")
            z = py_get_float("node_z(" + str(update[0]) + ")")
            #updates node based on maximum and minimum values and the update array
            py_send("*edit_nodes " + str(update[0]) + " " + str(clamp(update[1] + x, nodeMinXDictionary[update[0]], nodeMaxXDictionary[update[0]])) + " " + str(clamp(update[2] + y, nodeMinYDictionary[update[0]], nodeMaxYDictionary[update[0]])) + " " + str(z))
        else:
            x = py_get_float("node_x(" + str(4) + ")")
            y = py_get_float("node_y(" + str(4) + ")")
            z = py_get_float("node_z(" + str(4) + ")")
            py_send("*edit_nodes " + str(4) + " " + str(clamp(update[1] + x, nodeMinXDictionary[4], nodeMaxXDictionary[4])) + " " + str(clamp(update[2] + y, nodeMinYDictionary[4], nodeMaxYDictionary[4])) + " " + str(z))
            
            x = py_get_float("node_x(" + str(6) + ")")
            y = py_get_float("node_y(" + str(6) + ")")
            z = py_get_float("node_z(" + str(6) + ")")
            py_send("*edit_nodes " + str(6) + " " + str(clamp(update[1] + x, nodeMinXDictionary[6], nodeMaxXDictionary[6])) + " " + str(clamp(update[2] + y, nodeMinYDictionary[6], nodeMaxYDictionary[6])) + " " + str(z))
        
#iteratively performs gradient descent
#keep in mind: even when optimising only 4 nodes, this can take 8 minutes per iteration on a fast computer
for x in range(1):
    updateDesign()
    
#output new max buckling force (proxy)
submitAndOpenJob()
py_send(str(getMaxBucklingForce()))
py_send("*post_close")
