import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Decision(object):

    def __init__(self, trueNode = None, falseNode = None, message = "", nodeType = "question"):

        self.trueNode = trueNode
        self.falseNode = falseNode
        self.message = message
        self.nodeType = nodeType

    def getBranch(self):

        answer = exec(self.message)

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
        self.flee_cooldown = 0.
        self.detection_distance = 200

        self.maxSpeed = 80
        self.min_target_distance = 100
        self.melee_damage = 20
        self.melee_cooldown = 2.

        deciding_state = KnightStateDeciding_GERPERN(self)
        fleeing_state = KnightStateFleeing_GERPERN(self)
        dodging_state = KnightStateDodging_GERPERN(self)
        seeking_state = KnightStateSeeking_GERPERN(self)
        attacking_state = KnightStateAttacking_GERPERN(self)
        ko_state = KnightStateKO_GERPERN(self)

        self.brain.add_state(deciding_state)
        self.brain.add_state(fleeing_state)
        self.brain.add_state(dodging_state)
        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("seeking")
        

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        level_up_stats = ["hp", "speed", "melee damage", "melee cooldown"]
        if self.can_level_up():
            choice = randint(0, len(level_up_stats) - 1)
            self.level_up(level_up_stats[choice])

        self.flee_cooldown -= time_passed
        self.get_enemy_count()
        print(str(self.is_enemy_ranged()))

    def get_enemy_count(self):
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

        print(str(len(near_entities)))
        return len(near_entities)

    def is_enemy_ranged(self):

        if self.target is not None:
            if self.target.name == "archer" or self.target.name == "wizard" or self.target.name == "tower" or self.target.name == "base":
                return True
            else:
                return False

        return False


class KnightStateDeciding_GERPERN(State):
        
    def __init__(self, knight):

        State.__init__(self, "deciding")
        self.knight = knight

        self.fleeingNode = Decision(message = "fleeing", nodeType = "answer")
        self.dodgingNode = Decision(message = "dodging", nodeType = "answer")
        self.seekingNode = Decision(message = "seeking", nodeType = "answer")
        self.attackingNode = Decision(message = "attacking", nodeType = "answer")
        self.root = Decision(self.fleeingNode, self.dodgingNode, "Does it have fur?", nodeType = "question")
    
    def do_actions(self):
        return None

    def check_conditions(self):
        action = root.makeDecision()

        answer = print(action.message)

        return None

    def entry_actions(self):
        return None

    def exit_actions(self):
        return None

class KnightStateFleeing_GERPERN(State):
    
    def __init__(self, knight):

        State.__init__(self, "fleeing")
        self.knight = knight

    def do_actions(self):

        # colliding with target
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


    def check_conditions(self):

        # target is gone
        
        if self.knight.world.get(self.knight.target.id) is None or self.knight.target.ko:
            self.knight.target = None
            return "seeking"

        target_distance = (self.knight.position - self.knight.target.position).length()
        if self.knight.flee_cooldown <= 0:
            if self.knight.target.name == "wizard" or self.knight.target.name == "archer" or self.knight.target.name == "tower":
                if target_distance <= self.knight.target.min_target_distance:
                    if self.knight.target.current_melee_cooldown <= 0 or self.knight.target.current_ranged_cooldown <= 0:
                        return "dodging"
            
        return None

    def entry_actions(self):
        return None

    def exit_actions(self):
        self.knight.positions["pos2"] = Vector2(self.knight.position.x, self.knight.position.y)
        return None

class KnightStateDodging_GERPERN(State):
    
    def __init__(self, knight):

        State.__init__(self, "dodging")
        self.knight = knight
        self.dodged = False
        self.og_position = None
        self.dodge_position = None
        self.dodge_target =  None

    def do_actions(self):

        self.knight.velocity = self.dodge_target - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip();
            self.knight.velocity *= 40 #self.knight.maxSpeed

    def check_conditions(self):

        #check if hes dodged
        if (self.knight.position - self.dodge_position).length() <= 3:
            self.dodge_target = self.og_position
            self.dodged = True

        if self.dodged == True and (self.knight.position - self.og_position).length() <= 3:
            self.dodged = False
            return "seeking"
            
        return None


    def entry_actions(self):
        print(str(self.knight.positions["pos1"]))
        print(str(self.knight.positions["pos2"]))
        dir_vector = (self.knight.positions["pos1"] - self.knight.positions["pos2"])*1000
        dodge_vector = dir_vector.rotate(90)
        dodge_vector.normalize_ip()

        self.og_position = Vector2(self.knight.position.x, self.knight.position.y)
        self.dodge_position = Vector2(self.knight.position.x, self.knight.position.y) + (dodge_vector*21)
        self.dodge_target = self.dodge_position

    def exit_actions(self):
        self.knight.flee_cooldown = 3 #set the dodging cooldown
        return None


class KnightStateSeeking_GERPERN(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight
        self.knight.path_graph = self.knight.world.paths[randint(0, len(self.knight.world.paths)-1)]


    def do_actions(self):

        self.knight.velocity = self.knight.move_target.position - self.knight.position
        if self.knight.velocity.length() > 0:
            self.knight.velocity.normalize_ip();
            self.knight.velocity *= self.knight.maxSpeed


    def check_conditions(self):

        # check if opponent is in range
        nearest_opponent = self.knight.world.get_nearest_opponent(self.knight)
        if nearest_opponent is not None:
            opponent_distance = (self.knight.position - nearest_opponent.position).length()
            if opponent_distance <= self.knight.min_target_distance:
                    self.knight.target = nearest_opponent

                    return "attacking"
        
        if (self.knight.position - self.knight.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.knight.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            
        return None


    def entry_actions(self):

        nearest_node = self.knight.path_graph.get_nearest_node(self.knight.position)

        self.path = pathFindAStar(self.knight.path_graph, \
                                  nearest_node, \
                                  self.knight.path_graph.nodes[self.knight.base.target_node_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.knight.move_target.position = self.path[0].fromNode.position

        else:
            self.knight.move_target.position = self.knight.path_graph.nodes[self.knight.base.target_node_index].position
    def exit_actions(self):
        self.knight.positions["pos1"] = Vector2(self.knight.position.x, self.knight.position.y)
        print(str(self.knight.positions["pos1"]))
        return None

class KnightStateAttacking_GERPERN(State):

    def __init__(self, knight):

        State.__init__(self, "attacking")
        self.knight = knight

    def do_actions(self):

        # colliding with target
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


    def check_conditions(self):

        # target is gone
        
        if self.knight.world.get(self.knight.target.id) is None or self.knight.target.ko:
            self.knight.target = None
            return "seeking"

        target_distance = (self.knight.position - self.knight.target.position).length()
        if self.knight.flee_cooldown <= 0:
            if self.knight.target.name == "wizard" or self.knight.target.name == "archer" or self.knight.target.name == "tower":
                if target_distance <= self.knight.target.min_target_distance:
                    if self.knight.target.current_melee_cooldown <= 0 or self.knight.target.current_ranged_cooldown <= 0:
                        return "dodging"
            
        return None

    def entry_actions(self):
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
            self.knight.path_graph = self.knight.world.paths[randint(0, len(self.knight.world.paths)-1)]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.knight.current_hp = self.knight.max_hp
        self.knight.position = Vector2(self.knight.base.spawn_position)
        self.knight.velocity = Vector2(0, 0)
        self.knight.target = None

        return None
