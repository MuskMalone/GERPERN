import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Wizard_GERPERN(Character):

    def __init__(self, world, image, projectile_image, base, position, explosion_image = None):

        Character.__init__(self, world, "wizard", image)

        self.projectile_image = projectile_image
        self.explosion_image = explosion_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "wizard_move_target", None)
        self.target = None

        self.maxSpeed = 50
        self.min_target_distance = 100
        self.projectile_range = 100
        self.projectile_speed = 100

        self.explosion_radius = self.explosion_image.get_width()/2
        self.targetList = []
        self.trueTarget = None
        self.level = 0
        self.friendlyKnight = getKnight(self)
        self.opp_team_id = 1-self.base.team_id
        self.currentPath = None
        if self.base.team_id == 1:
            self.planBPath = [4,1,5,2]
        else:
            self.planBPath = []

        self.planB = False

        self.graph = Graph(self)
        self.generate_pathfinding_graphs("improved_knight_paths.txt")

        self.new_index = 0
        if self.base.spawn_node_index == 0:
            self.new_index = 22
        elif self.base.spawn_node_index == 4:
            self.new_index = 0

        retreating_state = WizardStateRetreating_GERPERN(self)
        meditating_state = WizardStateMeditating_GERPERN(self)
        seeking_state = WizardStateSeeking_GERPERN(self)
        defending_state = WizardStateDefending_GERPERN(self)
        attacking_state = WizardStateAttacking_GERPERN(self)
        ko_state = WizardStateKO_GERPERN(self)

        self.brain.add_state(retreating_state)
        self.brain.add_state(meditating_state)
        self.brain.add_state(seeking_state)
        self.brain.add_state(defending_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("meditating")

    def render(self, surface):

        #self.graph.render(surface)
        Character.render(self, surface)

        font = pygame.font.SysFont("arial", 24, True)
        #for x in self.graph.nodes:
        #    i = self.graph.nodes[x]
        #    i_x,i_y = i.position
        #    coord = font.render(str(i_x)+ ","+ str(i_y), True, (255, 255, 255))
        #    surface.blit(coord, (i_x, i_y))

    def process(self, time_passed):
        
        Character.process(self, time_passed)
        
        level_up_stats = ["ranged cooldown", "ranged damage", "hp", "speed", "projectile range"]
        if self.can_level_up():
            if self.level < 3:
                self.level_up(level_up_stats[0])
            else:
                self.level_up(level_up_stats[1])         
            
            self.level += 1

    def generate_pathfinding_graphs(self, filename):

        f = open(filename, "r")

        # Create the nodes
        line = f.readline()
        while line != "connections\n":
            data = line.split()
            self.graph.nodes[int(data[0])] = Node(self.graph, int(data[0]), int(data[1]), int(data[2]))
            line = f.readline()

        # Create the connections
        line = f.readline()
        while line != "paths\n":
            data = line.split()
            node0 = int(data[0])
            node1 = int(data[1])
            distance = (Vector2(self.graph.nodes[node0].position) - Vector2(self.graph.nodes[node1].position)).length()
            self.graph.nodes[node0].addConnection(self.graph.nodes[node1], distance)
            self.graph.nodes[node1].addConnection(self.graph.nodes[node0], distance)
            line = f.readline()

        # Create the orc paths, which are also Graphs
        self.paths = []
        line = f.readline()
        while line != "":
            path = Graph(self)
            data = line.split()
            
            # Create the nodes
            for i in range(0, len(data)):
                node = self.graph.nodes[int(data[i])]
                path.nodes[int(data[i])] = Node(path, int(data[i]), node.position[0], node.position[1])

            # Create the connections
            for i in range(0, len(data)-1):
                node0 = int(data[i])
                node1 = int(data[i + 1])
                distance = (Vector2(self.graph.nodes[node0].position) - Vector2(self.graph.nodes[node1].position)).length()
                path.nodes[node0].addConnection(path.nodes[node1], distance)
                path.nodes[node1].addConnection(path.nodes[node0], distance)
                
            self.paths.append(path)
            line = f.readline()

        f.close()


class WizardStateRetreating_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "retreating")
        self.wizard = wizard

    def do_actions(self):
        
        self.wizard.velocity = self.wizard.move_target.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip()
            self.wizard.velocity *= self.wizard.maxSpeed

        opponent_distance = (self.wizard.position - self.wizard.target.position).length()

        # Continue attacking while moving back if enemies in range
        if targetListUpdate(self.wizard) > 0:
            self.wizard.target = self.wizard.targetList[0]
            self.wizard.trueTarget = findBestTarget(0, None, 0, 999, self.wizard)

            # opponent within range
            if opponent_distance <= self.wizard.min_target_distance:
                if self.wizard.current_ranged_cooldown <= 0:
                    self.wizard.ranged_attack(self.wizard.trueTarget, self.wizard.explosion_image)
                    self.wizard.heal()

        # Else heal
        else:
            self.wizard.heal()

    def check_conditions(self):

        if (self.wizard.position - self.wizard.move_target.position).length() < 8:
            # continue on path
            if self.current_connection < self.path_length:
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

        nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)
        if nearest_node == self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index] and targetListUpdate(self.wizard) == 0:
            self.wizard.target = None
            return "seeking"

        elif (nearest_opponent.position - self.wizard.position).length() >= (self.wizard.min_target_distance*0.8) and self.wizard.current_hp/self.wizard.max_hp >= 0.6:
            return "attacking"
            
        elif self.wizard.current_hp/self.wizard.max_hp >= 0.6 and (self.wizard.world.get(self.wizard.target.id) is None or self.wizard.target.ko or targetListUpdate(self.wizard) == 0):
            self.wizard.target = None
            return "seeking"

    def entry_actions(self):
        #print("retreating")

        nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)
        self.path = pathFindAStar(self.wizard.path_graph, \
                                  nearest_node, \
                                  self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index])
        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.wizard.move_target.position = self.path[0].fromNode.position

        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.base.spawn_node_index].position


class WizardStateMeditating_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "meditating")
        self.wizard = wizard

    def do_actions(self):

        print("Wizard_GERPERN is meditating, gaining immense knowledge and waiting for the right moment to strike")
        # Check if HP is full
        if self.wizard.current_hp != self.wizard.max_hp:
            self.wizard.heal()

    def check_conditions(self):
        
        if self.wizard.planB != True:
            # Check if any target in range
            if targetListUpdate(self.wizard) > 0:
                self.wizard.target = self.wizard.targetList[0]
                return "attacking"
        
        else:
            print("Wizard_GERPERN notices both his towers are down but points are higher than", TEAM_NAME[self.wizard.opp_team_id]+"'s")
            print("Wizard_GERPERN will now defend and his team shall win by points instead!")
            return "defending"

        if self.wizard.planB != True:
            laneChosen = laneCheck(self.wizard)

            if teamTowerCount(self.wizard) == 0 and oppTowerCount(self.wizard) > teamTowerCount(self.wizard): #and self.wizard.world.scores[self.wizard.base.team_id] > self.wizard.world.scores[self.wizard.opp_team_id]:
                self.wizard.planB = True

            if laneChosen != None:
                self.wizard.path_graph = self.wizard.paths[laneChosen]
                self.wizard.currentPath = laneChosen
                return "seeking"

    def entry_actions(self):
        #print("meditating")
        self.wizard.velocity = Vector2(0, 0)

def teamTowerCount(self):
    towerCount = 0
    for entity in self.world.entities.values():
        if entity.name == "tower" and entity.team_id == self.base.team_id:
            towerCount += 1

    return towerCount

def oppTowerCount(self):
    towerCount = 0
    for entity in self.world.entities.values():
        if entity.name == "tower" and entity.team_id == self.opp_team_id:
            towerCount += 1

    return towerCount

class WizardStateSeeking_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "seeking")
        self.wizard = wizard

    def do_actions(self):
        
        self.wizard.velocity = self.wizard.move_target.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip();
            self.wizard.velocity *= self.wizard.maxSpeed
        toBePosition = self.wizard.position + 2*self.wizard.velocity

        # Check if HP is full
        if self.wizard.current_hp != self.wizard.max_hp:

            nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
            if self.wizard.current_hp/self.wizard.max_hp < 0.3 or (toBePosition - nearest_opponent.position).length() > self.wizard.min_target_distance:
                self.wizard.heal()
        
        #self.wizard.planB = True
        #self.wizard.current_hp = 0
    def check_conditions(self):

        # Check if any target in range
        if targetListUpdate(self.wizard) > 0:
            self.wizard.target = self.wizard.targetList[0]
            return "attacking"
        elif (self.wizard.position - self.wizard.move_target.position).length() < 8:
            # continue on path
            if self.current_connection < self.path_length:
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

    def entry_actions(self):
        #print("seeking")
        nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)
        self.path = pathFindAStar(self.wizard.path_graph, \
                                  nearest_node, \
                                   self.wizard.path_graph.nodes[self.wizard.new_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.wizard.move_target.position = self.path[0].fromNode.position

        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.new_index].position

def getKnight(self):
    for entity in self.world.entities.values():

        if entity.name == "knight" and entity.team_id == self.base.team_id:
            return entity

def laneCheck(self):
    topLane = 0
    midLane1 = 0
    midLane2 = 0
    bottomLane = 0
    pathToTake = None

    for entity in self.world.entities.values():
        
        if entity.name == "orc" and entity.team_id == self.base.team_id and entity.ko != True:
            #print(self.world.paths[0])
            #print(entity.brain.states["seeking"].path_graph)
            orcPath = entity.brain.states["seeking"].path_graph

            if orcPath == self.world.paths[0]:
                topLane +=1
            elif orcPath == self.world.paths[1]:
                bottomLane += 1
            elif orcPath == self.world.paths[2]:
                midLane2 += 1
            else:
                midLane1 += 1
    
    print("top: ",topLane,"mid1: ",midLane1,"mid2: ",midLane2,"bottom: ",bottomLane)
    # If Knight exists, go to same lane
    if self.friendlyKnight.ko != True:
        print("Wizard_GERPERN has decided on it's plan: Follow the Knight!")
        pathToTake = self.friendlyKnight.currentLane

        return pathToTake

    # If all lanes have same no. of Orcs, return None
    elif (topLane == midLane1 == midLane2 == bottomLane) and topLane <= 1:
        return None

    # Else return lane with most Orcs
    else:
        laneDic = {topLane:"0", midLane1:"3", midLane2:"2", bottomLane:"1"}
        print("top: ",topLane,"mid1: ",midLane1,"mid2: ",midLane2,"bottom: ",bottomLane)
        return int(laneDic.get(max(laneDic)))

def targetListUpdate(self):

    self.targetList.clear()

    for entity in self.world.entities.values():
        
            if entity.team_id != self.opp_team_id:
                continue

            if entity.name == "projectile" or entity.name == "explosion":
                continue

            if entity.ko:
                continue

            if pygame.math.Vector2(self.position).distance_to(entity.position) > self.min_target_distance:
                continue

            else:
                self.targetList.append(entity)

    return len(self.targetList)


class WizardStateDefending_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "defending")
        self.wizard = wizard

    def do_actions(self):
        
        self.wizard.velocity = self.wizard.move_target.position - self.wizard.position
        if self.wizard.velocity.length() > 0:
            self.wizard.velocity.normalize_ip();
            self.wizard.velocity *= self.wizard.maxSpeed
        toBePosition = self.wizard.position + 2*self.wizard.velocity

        # Check if HP is full
        if self.wizard.current_hp != self.wizard.max_hp:

            nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
            if self.wizard.current_hp/self.wizard.max_hp < 0.3 or (toBePosition - nearest_opponent.position).length() > self.wizard.min_target_distance:
                self.wizard.heal()

    def check_conditions(self):

        # Check if any target in range
        if targetListUpdate(self.wizard) > 0:
            self.wizard.target = self.wizard.targetList[0]
            return "attacking"
        elif (self.wizard.position - self.wizard.move_target.position).length() < 8:
            # continue on path
            if self.current_connection < self.path_length:
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

            else:
                if self.wizard.currentPath == 4:
                    path = self.wizard.planBPath[2]
                    destinationIndex = self.wizard.planBPath[3]
                else:
                    path = self.wizard.planBPath[0]
                    destinationIndex = self.wizard.planBPath[1]

                self.wizard.path_graph = self.wizard.paths[path]
                self.wizard.currentPath = path
                nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)
        
                self.path = pathFindAStar(self.wizard.path_graph, \
                                          nearest_node, \
                                          self.wizard.path_graph.nodes[destinationIndex])
        
                self.path_length = len(self.path)

                if (self.path_length > 0):
                    self.current_connection = 0
                    self.wizard.move_target.position = self.path[0].fromNode.position

                else:
                    self.wizard.move_target.position = self.wizard.path_graph.nodes[destinationIndex].position

    def entry_actions(self):
        #print("defending")
        self.wizard.path_graph = self.wizard.paths[4]
        self.wizard.currentPath = 4
        nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)
        destinationIndex = 1
        
        self.path = pathFindAStar(self.wizard.path_graph, \
                                  nearest_node, \
                                   self.wizard.path_graph.nodes[destinationIndex])
        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.wizard.move_target.position = self.path[0].fromNode.position

        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[destinationIndex].position


class WizardStateAttacking_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "attacking")
        self.wizard = wizard
        
    def do_actions(self):
        opponent_distance = (self.wizard.position - self.wizard.target.position).length()
        if targetListUpdate(self.wizard) > 0:
            self.wizard.target = self.wizard.targetList[0]
            self.wizard.trueTarget = findBestTarget(0, None, 0, 999, self.wizard)

        # opponent within range
        if opponent_distance <= self.wizard.min_target_distance:
            self.wizard.velocity = Vector2(0, 0)
            if self.wizard.current_ranged_cooldown <= 0:
                self.wizard.ranged_attack(self.wizard.trueTarget, self.wizard.explosion_image)
                self.wizard.heal()

        else:
            self.wizard.velocity = self.wizard.target.position - self.wizard.position
            if self.wizard.velocity.length() > 0:
                self.wizard.velocity.normalize_ip();
                self.wizard.velocity *= self.wizard.maxSpeed


    def check_conditions(self):

        if self.wizard.planB != True:
            nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
            if self.wizard.current_hp/self.wizard.max_hp <= 0.4 or (self.wizard.position - nearest_opponent.position).length() <= 40:
                return "retreating"

        # target is gone
        if self.wizard.world.get(self.wizard.target.id) is None or self.wizard.target.ko or targetListUpdate(self.wizard) == 0:
            self.wizard.target = None
            if self.wizard.planB != True:
                return "seeking"
            else:
                return "defending"
            
        return None

    def entry_actions(self):
        #print("attacking")
        return None


def findBestTarget(directionToCheck, bestTargetSoFar, numOfTargets, totalHP, self):

    # First Iteration - Check if midpoint can hit all targets
    if bestTargetSoFar == None:

        xTotal = 0
        yTotal = 0
        targetsInRange = 0
        totalTargets = 0
        totalTargetHP = 0

        for target in self.targetList:
            x, y = target.position
            xTotal += x
            yTotal += y
            totalTargets += 1

            #print("Target at:",x,",",y)
        
        midpoint = Vector2((xTotal/totalTargets), (yTotal/totalTargets))
        #print("Derived Midpoint:",midpoint)

        for target in self.targetList:
            if (midpoint - target.position).length() <= self.explosion_radius:
                #print("distance:",(midpoint - target.position).length(),"is lesser than",self.explosion_radius)
                totalTargetHP += target.current_hp
                targetsInRange += 1

        if targetsInRange == targetListUpdate(self):
            #print("midpoint:",midpoint,"totalTargets:",len(self.targetList))
            return midpoint
        else:
            #print("midpoint:",midpoint,"totalTargets:",len(self.targetList),"targets in range:",targetsInRange)
            return findBestTarget(0, midpoint, targetsInRange, totalTargetHP, self)

    # Else find best point to hit within target range
    currentPoint = Vector2(self.position[0], self.position[1]+0.001)
    bestSoFar = bestTargetSoFar
    numTargets = numOfTargets
    step = Vector2(cos(radians(directionToCheck)), sin(radians(directionToCheck))) - currentPoint
    step.normalize_ip()
    for i in range(5): # Only takes 5 iterations to cover min_target_distance
        targetsInRange = 0
        totalTargetHP = 0

        for target in self.targetList:
            #print("currentPoint:",currentPoint,"target pos:",target.position, "distance:",(currentPoint - target.position).length())
            if (currentPoint - target.position).length() <= self.explosion_radius:
                #print(target.name,"is in range")
                targetsInRange += 1
                totalTargetHP += target.current_hp
      
        if targetsInRange > numTargets:
            #print("found better target at",currentPoint,"with", targetsInRange,"targets")
            numTargets = targetsInRange
            x, y = currentPoint
            bestSoFar = Vector2(x, y)

        elif targetsInRange == numTargets:
            if totalTargetHP < totalHP:
                #print("target updated to", target.name)
                totalHP = totalTargetHP
                x, y = currentPoint
                bestSoFar = Vector2(x, y)

        currentPoint += (step*self.explosion_radius)

    if directionToCheck == 330:
        if numTargets == 0:
            return self.targetList[0].position
        return bestSoFar
        
   # Check again at an angle 30 degrees more
    return findBestTarget(directionToCheck+30, bestSoFar, numTargets, totalTargetHP, self)


class WizardStateKO_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "ko")
        self.wizard = wizard

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.wizard.current_respawn_time <= 0:
            self.wizard.current_respawn_time = self.wizard.respawn_time
            self.wizard.ko = False
            return "meditating"
            
        return None

    def entry_actions(self):
        #print("ko")
        self.wizard.current_hp = self.wizard.max_hp
        self.wizard.position = Vector2(self.wizard.base.spawn_position)
        self.wizard.velocity = Vector2(0, 0)
        self.wizard.target = None

        return None
