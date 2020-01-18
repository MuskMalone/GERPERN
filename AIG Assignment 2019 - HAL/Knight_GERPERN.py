import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Decision(object):

    def __init__(self, trueNode = None, falseNode = None, message = "", nodeType = "question", knight = None):

        self.trueNode = trueNode
        self.falseNode = falseNode
        self.message = message
        self.nodeType = nodeType
        self.knight = knight

    def getBranch(self):

        answer = eval(self.message)
        
        if answer == True:
            return self.trueNode
        else:
            return self.falseNode

    def makeDecision(self):

        if self.nodeType == "question":
            branch = self.getBranch()
            return branch.makeDecision()
        else:
            return self

class Knight_GERPERN(Character):

    def __init__(self, world, image, base, position):

        Character.__init__(self, world, "knight", image)

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "knight_move_target", None)
        self.target = None

        self.positions = {}
        self.dodge_vector = None
        self.dodge_cooldown = 0.
        self.detection_distance = 150

        self.healing_lvl = 0
        self.heal_cooldown_lvl = 0
        self.melee_cooldown_lvl = 0

        self.maxSpeed = 80
        self.min_target_distance = 100
        self.melee_damage = 20
        self.melee_cooldown = 2.
        self.true_target_index = 0
        if self.base.spawn_node_index == 0:
            self.true_target_index = 22
        elif self.base.spawn_node_index == 4:
            self.true_target_index = 0

        self.currentLane = None
        self.graph = Graph(self)
        self.generate_pathfinding_graphs("improved_knight_paths.txt")

        #state decision diagram
        self.fleeingNode = Decision(message = "fleeing", nodeType = "answer", knight = self) #fleeing state
        self.dodgingNode = Decision(message = "dodging", nodeType = "answer", knight = self) #dodging state
        self.seekingNode = Decision(message = "seeking", nodeType = "answer", knight = self) #seeking state
        self.attackingNode = Decision(message = "attacking", nodeType = "answer", knight = self) #attacking state
        self.isneartargetNode = Decision(self.attackingNode, self.dodgingNode, message = "(self.knight.position - self.knight.target.position).length() <= (self.knight.min_target_distance/3)", nodeType = "question", knight = self) #is distance from target short
        self.istargetattackNode = Decision(self.isneartargetNode, self.attackingNode, message = "self.knight.target.current_ranged_cooldown <= 0", nodeType = "question", knight = self) #is target able to attack
        self.isdodgedNode = Decision(self.istargetattackNode, self.attackingNode, message = "self.knight.dodge_cooldown <= 0", nodeType = "question", knight = self) #is dodging allowed
        self.israngedNode = Decision(self.isdodgedNode, self.attackingNode, message = "self.knight.is_enemy_ranged()", nodeType = "question", knight = self) #is single enemy ranged
        self.multipleenemyNode = Decision(self.attackingNode, self.israngedNode, message = "len(self.knight.get_enemy_list()) > 1", nodeType = "question", knight = self) #is multiple enemy
        self.healthenoughNode = Decision(self.fleeingNode, self.multipleenemyNode, message = "self.knight.current_hp <= 2*(self.knight.max_hp / 4)", nodeType= "question", knight = self) #is health enough
        self.root = Decision(self.healthenoughNode, self.seekingNode, "len(self.knight.get_enemy_list()) > 0", nodeType = "question", knight = self) #is enemy there 

        fleeing_state = KnightStateFleeing_GERPERN(self)
        dodging_state = KnightStateDodging_GERPERN(self)
        seeking_state = KnightStateSeeking_GERPERN(self)
        attacking_state = KnightStateAttacking_GERPERN(self)
        ko_state = KnightStateKO_GERPERN(self)

        self.brain.add_state(fleeing_state)
        self.brain.add_state(dodging_state)
        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("seeking")
        

    def render(self, surface):

        #self.graph.render(surface)
        Character.render(self, surface)
        if self.target:
            pygame.draw.line(surface, (255, 0, 0), self.position, self.target.position)


    def process(self, time_passed):
        
        Character.process(self, time_passed)
        if self.can_level_up():            
            leveled_up = False
            while leveled_up is False:
                choice = randint(1, 100)
                if choice <= 35 and self.healing_cooldown > self.melee_cooldown:
                    self.level_up("healing cooldown")
                    leveled_up = True
                elif choice > 35 and choice <= 70:
                    self.level_up("healing")
                    leveled_up = True
                elif choice > 70 and choice <= 90:
                    self.level_up("hp")
                    leveled_up = True
                elif choice >90 and choice <= 95:
                    self.level_up("melee_cooldown")
                    leveled_up = True
                elif choice >95 and choice <= 100:
                    self.level_up("melee damage")
                    leveled_up = True
                else:
                    leveled_up = False

        self.dodge_cooldown -= time_passed
        #print(str(len(self.get_enemy_list())))

    def get_enemy_list(self):
        entities = self.world.entities
        near_entities = {}

        for name, entity in entities.items():

            # neutral entity
            if entity.team_id == 2:
                continue

            # same team
            if entity.team_id == self.team_id:
                continue

            if entity.name == "projectile" or entity.name == "explosion":
                continue

            if entity.ko:
                continue

            if (self.position - entity.position).length() <= self.detection_distance:
                near_entities[name] = entity

        return near_entities

    def is_enemy_ranged(self):

        if self.target is not None:
            if self.target.name == "archer" or self.target.name == "wizard" or self.target.name == "tower" or self.target.name == "base":
                return True
            else:
                return False

        return False
        # --- Reads a set of pathfinding graphs from a file ---
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

class KnightStateFleeing_GERPERN(State):

    def __init__(self, knight):

        State.__init__(self, "fleeing")
        self.knight = knight
        self.path_graph = self.knight.paths[randint(2,3)]


    def do_actions(self):

        self.knight.velocity = self.knight.move_target.position - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip();
            self.knight.velocity *= self.knight.maxSpeed

        if self.knight.current_healing_cooldown <= 0:
            self.knight.heal()
        #print(str(self.knight.get_enemy_list()))

    def check_conditions(self):

        ## check if opponent is in range
        #nearest_opponent = self.knight.world.get_nearest_opponent(self.knight)
        #if nearest_opponent is not None:
        #    opponent_distance = (self.knight.position - nearest_opponent.position).length()
        #    if opponent_distance <= self.knight.min_target_distance:
        #            self.knight.target = nearest_opponent

        #            return "attacking"
        
        if (self.knight.position - self.knight.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.knight.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

        action = self.knight.root.makeDecision()
        state = action.message
        if state != self.knight.brain.active_state.name:
            return state

        return None


    def entry_actions(self):

        nearest_node = self.path_graph.get_nearest_node(self.knight.position)

        self.path = pathFindAStar(self.path_graph, \
                                  nearest_node, \
                                  self.path_graph.nodes[self.knight.base.spawn_node_index])

        
        self.path_length = len(self.path)
        #print(str(len(self.path)))

        if (self.path_length > 0):
            self.current_connection = 0
            self.knight.move_target.position = self.path[0].fromNode.position

        else:
            self.knight.move_target.position = self.path_graph.nodes[self.knight.base.spawn_node_index].position

    def exit_actions(self):
        return None

class KnightStateDodging_GERPERN(State):
    
    def __init__(self, knight):

        State.__init__(self, "dodging")
        self.knight = knight
        self.dodged = False
        self.og_position = None
        self.dodge_position = None
        self.dodge_target =  None
        self.pos = Vector2(0,0)

    def do_actions(self):

        self.knight.velocity = self.dodge_target - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip();
            self.knight.velocity *= self.knight.maxSpeed

    def check_conditions(self):

        #print(str(self.pos) + "before")
        #check if hes dodged
        if self.dodged is False and (self.knight.position - self.dodge_position).length() <= 5:
            self.dodge_target = self.og_position
            self.dodged = True
        if self.knight.position == self.pos:
            self.dodge_target = self.og_position
            self.dodged = True

        if self.dodged == True:# and (self.knight.position - self.og_position).length() <= 5:
            self.dodged = False
            action = self.knight.root.makeDecision()
            state = action.message
            if state != self.knight.brain.active_state.name:
                return state
        self.pos = Vector2(self.knight.position.x, self.knight.position.y)
        #print(str(self.pos) + "after")
        return None


    def entry_actions(self):

        dir_vector = (Vector2(self.knight.position.x, self.knight.position.y) - Vector2(self.knight.target.position.x, self.knight.target.position.y))*1000
        dodge_vector = dir_vector.rotate(90)
        dodge_vector.normalize_ip()
        chance = randint(0,1)
        #if chance == 0:
        #    dodge_vector = dodge_vector*1
        #else:
        #    dodge_vector = dodge_vector*-1

        self.og_position = Vector2(self.knight.position.x, self.knight.position.y)
        self.dodge_position = Vector2(self.knight.position.x, self.knight.position.y) + (dodge_vector*40)
        self.dodge_target = self.dodge_position

    def exit_actions(self):
        self.knight.dodge_cooldown = 0. #set the dodging cooldown
        return None


class KnightStateSeeking_GERPERN(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight
        pathChosen = randint(2,3)
        self.path_graph = self.knight.paths[pathChosen]
        self.knight.currentLane = pathChosen

    def do_actions(self):

        self.knight.velocity = self.knight.move_target.position - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip();
            self.knight.velocity *= self.knight.maxSpeed

        #print(str(self.knight.get_enemy_list()))
    def check_conditions(self):
        
        if (self.knight.position - self.knight.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.knight.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1

        action = self.knight.root.makeDecision()
        state = action.message
        if state != self.knight.brain.active_state.name:
            return state

        return None


    def entry_actions(self):
        self.knight.target = None
        nearest_node = self.path_graph.get_nearest_node(self.knight.position)

        self.path = pathFindAStar(self.path_graph, \
                                  nearest_node, \
                                  self.path_graph.nodes[self.knight.true_target_index])

        
        self.path_length = len(self.path)
        #print(str(len(self.path)))
        if (self.path_length > 0):
            self.current_connection = 0
            self.knight.move_target.position = self.path[0].fromNode.position

        else:
            self.knight.move_target.position = self.path_graph.nodes[self.knight.true_target_index].position

    def exit_actions(self):
        self.knight.positions["pos1"] = Vector2(self.knight.position.x, self.knight.position.y)
        # check if opponent is in range
        return None

class KnightStateAttacking_GERPERN(State):

    def __init__(self, knight):

        State.__init__(self, "attacking")
        self.knight = knight

    def do_actions(self):

        # colliding with target
        if self.knight.target is not None:
            if pygame.sprite.collide_rect(self.knight, self.knight.target):
                self.knight.velocity = Vector2(0, 0)
                if self.knight.current_healing_cooldown <= 0:
                    self.knight.melee_attack(self.knight.target)
                    self.knight.heal()

            else:
                self.knight.velocity = self.knight.target.position - self.knight.position
                if self.knight.velocity.length() > 0:
                    self.knight.velocity.normalize_ip();
                    self.knight.velocity *= self.knight.maxSpeed
        # CHANGE OPPONENT STATE
        #if self.knight.target.name != "tower" and self.knight.target.name != "base":
        #    self.knight.target.brain.set_state("seeking")

    def check_conditions(self):

        nearest_opponent = self.knight.world.get_nearest_opponent(self.knight)
        if nearest_opponent is not None:
            self.knight.target = nearest_opponent
        action = self.knight.root.makeDecision()
        state = action.message
        if state != self.knight.brain.active_state.name:
            return state

        return None

    def entry_actions(self):
        ##INSTANT WIN
        #for entity in self.knight.world.entities.values():
        #    if entity.team_id != 2 and entity.team_id != self.knight.team_id:
        #        if entity.name == "base":
        #            entity.current_hp = -1
        return None

    def exit_actions(self):
        self.knight.positions["pos2"] = Vector2(self.knight.position.x, self.knight.position.y)
        return None


class KnightStateKO_GERPERN(State):

    def __init__(self, knight):

        State.__init__(self, "ko")
        self.knight = knight

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.knight.current_respawn_time <= 0:
            self.knight.current_respawn_time = self.knight.respawn_time
            self.knight.ko = False
            return "seeking"
            
        return None

    def entry_actions(self):

        self.knight.current_hp = self.knight.max_hp
        self.knight.position = Vector2(self.knight.base.spawn_position)
        self.knight.velocity = Vector2(0, 0)
        self.knight.target = None

        return None
