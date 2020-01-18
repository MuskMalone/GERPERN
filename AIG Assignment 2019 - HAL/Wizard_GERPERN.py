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

        seeking_state = WizardStateSeeking_GERPERN(self)
        attacking_state = WizardStateAttacking_GERPERN(self)
        ko_state = WizardStateKO_GERPERN(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("seeking")

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)
        
        level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range"]
        if self.can_level_up():
            choice = randint(0, len(level_up_stats) - 1)
            self.level_up(level_up_stats[choice])      


class WizardStateSeeking_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "seeking")
        self.wizard = wizard

        self.wizard.path_graph = self.wizard.world.paths[randint(0, len(self.wizard.world.paths)-1)]
        

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
        
        # ---------------- ORIGINAL CODE ---------------------
        ## check if opponent is in range
        #nearest_opponent = self.wizard.world.get_nearest_opponent(self.wizard)
        #if nearest_opponent is not None:
        #    opponent_distance = (self.wizard.position - nearest_opponent.position).length()
        #    if opponent_distance <= self.wizard.min_target_distance:
        #            self.wizard.target = nearest_opponent
        #            return "attacking"
        #
        #if (self.wizard.position - self.wizard.move_target.position).length() < 8:
        #
        #    # continue on path
        #    if self.current_connection < self.path_length:
        #        self.wizard.move_target.position = self.path[self.current_connection].toNode.position
        #        self.current_connection += 1
        #    
        #return None
        # -----------------------------------------------------

        # Check if any target in range
        if targetListUpdate(self.wizard) > 0:
            self.wizard.target = self.wizard.targetList[0]
            return "attacking"
        elif (self.wizard.position - self.wizard.move_target.position).length() < 8:
            # continue on path
            if self.current_connection < self.path_length:
                self.wizard.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

        return None

    def entry_actions(self):
        print("seeking")
        nearest_node = self.wizard.path_graph.get_nearest_node(self.wizard.position)

        self.path = pathFindAStar(self.wizard.path_graph, \
                                  nearest_node, \
                                  self.wizard.path_graph.nodes[self.wizard.base.target_node_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.wizard.move_target.position = self.path[0].fromNode.position

        else:
            self.wizard.move_target.position = self.wizard.path_graph.nodes[self.wizard.base.target_node_index].position

##def laneCheck(self):
##    topLane = 0
##    midLane1 = 0
##    midLane2 = 0
##    bottomLane = 0
##    knightExists = False
##
##    for entity in self.world.entities.values():
##
##        if entity.ko:
##            continue
##
##        if entity.team_id == self.team_id and entity.name = "orc":
##            if entity.path_graph == self.world.paths[0]:
##                topLane +=1
##            elif entity.path_graph == self.world.paths[1]:
##                bottomLane += 1
##            elif entity.path_graph == self.world.paths[2]:
##                midLane2 += 1
##            else:
##                midLane1 += 1:
##        
##        elif entity.team_id == self.team_id and entity.name = "knight":
##            knightPath = entity.path_graph
##
##        # If equal no. of Orcs in each lane, look for Knight
##        if (topLane == midLane1 == midLane2 == bottomLane) and knightExists:
##            return 
##
##    laneDic = {topLane:"0", midLane1:"3", midLane2:"2", bottomLane:"1"}

def targetListUpdate(self):

    self.targetList.clear()

    for entity in self.world.entities.values():

            if entity.team_id == 2:
                continue

            if entity.team_id == self.team_id:
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


class WizardStateAttacking_GERPERN(State):

    def __init__(self, wizard):

        State.__init__(self, "attacking")
        self.wizard = wizard

    def do_actions(self):
        
        opponent_distance = (self.wizard.position - self.wizard.target.position).length()
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
        
        # target is gone
        if self.wizard.world.get(self.wizard.target.id) is None or self.wizard.target.ko or targetListUpdate(self.wizard) == 0:
            self.wizard.target = None
            return "seeking"
            
        return None

    def entry_actions(self):
        print("attacking")
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
            xTotal += target.position[0]
            yTotal += target.position[1]
            totalTargets += 1
        
        midpoint = Vector2((xTotal/totalTargets), (yTotal/totalTargets))

        for target in self.targetList:
            if pygame.math.Vector2(midpoint).distance_to(target.position) <= self.explosion_radius:
                totalTargetHP += target.current_hp
                targetsInRange += 1

        if targetsInRange == targetListUpdate(self):
            return midpoint
        else:
            return findBestTarget(0, midpoint, targetsInRange, totalTargetHP, self)

    # Else find best point to hit within target range
    currentPoint = Vector2(self.position[0], self.position[1]+0.001)
    bestSoFar = bestTargetSoFar
    numTargets = numOfTargets
    step = Vector2(cos(radians(directionToCheck)), sin(radians(directionToCheck))) - currentPoint
    step.normalize_ip()
    for i in range(6):
        targetsInRange = 0
        totalTargetHP = 0

        for target in self.targetList:
            if currentPoint.distance_to(target.position) <= self.explosion_radius:
                targetsInRange += 1
                totalTargetHP += target.current_hp
      
        if targetsInRange > numTargets:
            numTargets = targetsInRange
            x, y = currentPoint
            bestSoFar = Vector2(x, y)

        elif targetsInRange == numTargets:
            if totalTargetHP < totalHP:
                print("target updated to", target.name)
                totalHP = totalTargetHP
                x, y = currentPoint
                bestSoFar = Vector2(x, y)

        currentPoint += (step*self.explosion_radius)

    if directionToCheck == 315:
        return bestSoFar
        
    
    return findBestTarget(directionToCheck+45, bestSoFar, numTargets, totalTargetHP, self)


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
            self.wizard.path_graph = self.wizard.world.paths[randint(0, len(self.wizard.world.paths)-1)]
            return "seeking"
            
        return None

    def entry_actions(self):
        print("ko")
        self.wizard.current_hp = self.wizard.max_hp
        self.wizard.position = Vector2(self.wizard.base.spawn_position)
        self.wizard.velocity = Vector2(0, 0)
        self.wizard.target = None

        return None
