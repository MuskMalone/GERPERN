import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *

class Archer_GERPERN(Character):

    def __init__(self, world, image, projectile_image, base, position):

        Character.__init__(self, world, "archer", image)

        self.projectile_image = projectile_image

        self.base = base
        self.position = position
        self.move_target = GameEntity(world, "archer_move_target", None)
        self.target = None
        self.Action = "not kited"
        self.maxSpeed = 50
        self.min_target_distance = 100
        self.projectile_range = 100
        self.projectile_speed = 100
        self.normal_pos = None        
        self.Seconds_passed = None
        self.Start_ticks = None
        self.enemy_atk_cd = 0
        self.kite_position = None
        self.enemy_type = None
        self.attacked = "false"
        seeking_state = ArcherStateSeeking_GERPERN(self)
        attacking_state = ArcherStateAttacking_GERPERN(self)
        ko_state = ArcherStateKO_GERPERN(self)
        kiting_state = ArcherStateKiting_GERPERN(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(kiting_state)
        self.brain.add_state(ko_state)
        
        self.brain.set_state("seeking")

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)
        
        level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range"]
        if self.can_level_up():
            choice = randint(0, len(level_up_stats) - 1)
            self.level_up(level_up_stats[2])
            
    
    def getcharLane_Position(self,E):
        Arect = E.image.get_rect(topleft=self.position)
        Lane = None
        LanePosition = None
        AR_TL_x, AR_TL_y = Arect.topleft
        AR_BR_x, AR_BR_y = Arect.bottomright
        R1_TL_x, R1_TL_y = Vector2(110,250)       #1.Get the top left and bottom right of the mountains and the archer
        R1_BR_x, R1_BR_y = Vector2(736,670)       #3. if yes, the archer shld be in the bot lane, 
        R2_TL_x, R2_TL_y = Vector2(312, 90)       #4. If no, check if the archer is above the top mountain (Compare the top left and btm right). If it is above the top mountain, it should be in top lane
        R2_BR_x, R2_BR_y = Vector2(910, 476)      #5. Once we got the lane, we get the archer's position(directly beside/bellow mountain)
                                                  #6. return both the position and Lane
        left_of_M1 = AR_TL_x < R1_TL_x
        bottom_of_M1 = AR_BR_y > R1_BR_y        
        right_of_M2 = AR_BR_x > R2_BR_x
        top_of_M2 = AR_TL_y < R2_TL_y

        if bottom_of_M1:
            Lane = "Bottom"
            if E.name == "base":
                    LanePosition = "Bottom_Side"
            else:
                if right_of_M2:
                    LanePosition = "Bottom_Right_Corner"                    
                elif left_of_M1:
                    LanePosition = "Bottom_Left_Corner"                
                else:
                    LanePosition = "Bottom_Side"
                
        elif top_of_M2:
            Lane = "Top"
            if E.name == "base":
                    LanePosition = "Top_Side"
            else:
                if right_of_M2:
                    LanePosition = "Top_Right_Corner"                    
                elif left_of_M1:
                    LanePosition = "Top_Left_Corner"                
                else:
                    LanePosition = "Top_Side"
                    
        else:
            if right_of_M2:
                Lane = "Top"
                LanePosition = "Right_Side"
            elif left_of_M1:
                Lane = "Bottom"
                LanePosition = "Left_Side"
            else:    
                Lane = "Mid"
                if AR_TL_x >= 345 and AR_BR_x <= 671:
                    LanePosition = "HexagonArea"
                else:
                    LanePosition = "midPath"
        print("LP: ",LanePosition)
        return Lane,LanePosition

    def MovetoSafeLocation_Safe(self,A_Lane,A_LanePos):
        currentx, currenty = self.position
        self.kite_position = Vector2(0,0)
      
        if A_Lane == "Top":
            if A_LanePos == "Top_Side":
                if self.base.team_id == 1:
                    self.kite_position = Vector2(970,50)
                else:
                    self.kite_position = Vector2(150,50)
            elif A_LanePos == "Right_Side":
                if self.base.team_id == 1:
                    self.kite_position = Vector2(970,628)
                else:
                    self.kite_position = Vector2(970,50)
            else:
                if self.base.team_id == 1:
                    if currentx >= 970:
                        self.kite_position = Vector2(970,628)
                    else:
                        self.kite_position = Vector2(970,50)
                else:
                    if currenty <= 50:
                        self.kite_position = Vector2(150,50)
                    else:
                        self.kite_position = Vector2(970,50)
                        
        elif A_Lane == "Bottom":
            if A_LanePos == "Bottom_Side":
                if self.base.team_id == 1:
                    self.kite_position = Vector2(855,727)
                else:
                    self.kite_position = Vector2(40,716)
            elif A_LanePos == "Left_Side":
                if self.base.team_id == 1:
                    self.kite_position = Vector2(40,716)
                else:
                    self.kite_position = Vector2(44,164)
            else:
                if self.base.team_id == 1:
                    if currenty >= 716:
                        self.kite_position = Vector2(855,727)
                    else:
                        self.kite_position = Vector2(40,716)
                else:
                    if currentx <= 44:
                        self.kite_position = Vector2(44,164)
                    else:
                        self.kite_position = Vector2(44,716)

            

        self.velocity = self.kite_position - self.position
        if self.velocity.length() > 0:
            self.velocity.normalize_ip();
            self.velocity *= self.maxSpeed

            
    def MovetoSafeLocation_Aggro(self,A_Lane,A_LanePos,B_Lane,B_LanePos):        
        currentx, currenty = self.position
        safe_x = currentx
        safe_y = currenty
        enemyx,enemyy = self.target.position
        
        if A_Lane == "Top":
            if A_LanePos == B_LanePos:
                if A_LanePos == "Top_Side":
                    safe_y = currenty - 40
                    safe_x = currentx + ((enemyx-currentx)/abs(enemyx-currentx))*40
                    
                elif A_LanePos == "Right_Side":
                    safe_x = currentx + 40
                    safe_y = currenty +((enemyy-currenty)/abs(enemyy-currenty))*40
                else:
                    if abs(enemyx-currentx) > abs(enemyy-currenty):
                        safe_y = currenty - 40
                        safe_x = currentx
                    else:
                        safe_x = currentx + 40
                        safe_y = currenty
            else:
                if abs(enemyx-currentx) > abs(enemyy-currenty):
                    safe_y = currenty - 40
                    safe_x = currentx
                else:
                    safe_x = currentx + 40
                    safe_y = currenty
                
        elif A_Lane == "Bottom":
            if A_LanePos == B_LanePos:           
                if A_LanePos == "Bottom_Side":
                 
                    safe_y = currenty + 40
                    safe_x = currentx + ((enemyx-currentx)/abs(enemyx-currentx))*40
                    
                elif A_LanePos == "Left_Side":
                   
                    safe_x = currentx - 40
                    safe_y = currenty +((enemyy-currenty)/abs(enemyy-currenty))*40

                else:
                    if abs(enemyx-currentx) > abs(enemyy-currenty):
                       
                        safe_y = currenty + 40
                        safe_x = currentx
                    else:
                       
                        safe_x = currentx - 40
                        safe_y = currenty
                                        
            else:
                if abs(enemyx-currentx) > abs(enemyy-currenty):
                    safe_y = currenty + 40
                    safe_x = currentx
                else:
                    safe_x = currentx - 40
                    safe_y = currenty
               

        else:
           # print("Corner")
            if A_LanePos == B_LanePos:                
                if A_LanePos == "Top_Side":
                    safe_y = currenty - 40
                    safe_x = currentx + ((enemyx-currentx)/abs(enemyx-currentx))*40 
                elif A_LanePos == "Right_Side":
                    safe_x = currentx + 40
                    safe_y = currenty +((enemyy-currenty)/abs(enemyy-currenty))*40 
            else:
               # print("Diff_Corner")
                if abs(enemyx-currentx) > abs(enemyy-currenty):
                    safe_y = currenty + 40
                    safe_x = currentx
                else:
                    safe_x = currentx - 40
                    safe_y = currenty
                                                
        self.kite_position = Vector2(safe_x,safe_y)
        self.velocity = self.kite_position - self.position
        if self.velocity.length() > 0:
            self.velocity.normalize_ip();
            self.velocity *= self.maxSpeed
        
     
    def GetEnemyType(self):
        blue_knight_image = pygame.image.load("assets/blue_knight_32_32.png").convert_alpha()
        blue_archer_image = pygame.image.load("assets/blue_archer_32_32.png").convert_alpha()
        blue_wizard_image = pygame.image.load("assets/blue_wizard_32_32.png").convert_alpha()
        blue_tower_image = pygame.image.load("assets/blue_tower.png").convert_alpha()
        blue_base_image = pygame.image.load("assets/blue_base.png").convert_alpha()
        blue_orc_image = pygame.image.load("assets/blue_orc_32_32.png").convert_alpha()
        red_knight_image = pygame.image.load("assets/red_knight_32_32.png").convert_alpha()
        red_archer_image = pygame.image.load("assets/red_archer_32_32.png").convert_alpha()        
        red_wizard_image = pygame.image.load("assets/red_wizard_32_32.png").convert_alpha()
        red_tower_image = pygame.image.load("assets/red_tower.png").convert_alpha()     
        red_base_image = pygame.image.load("assets/red_base.png").convert_alpha()
        red_orc_image = pygame.image.load("assets/red_orc_32_32.png").convert_alpha()
        
        if self.target.name == "archer" or self.target.name == "tower" or self.target.name == "base":
            self.enemy_type = "aggro_ranged"
        if self.target.image == red_knight_image or self.target.image == blue_knight_image or self.target.image == red_orc_image or self.target.image == blue_orc_image:
            self.enemy_type = "melee"
        if self.target.image == red_wizard_image or self.target.image == blue_wizard_image:
            self.enemy_type = "safe_melee"
            
    

        



class ArcherStateKiting_GERPERN(State):

    def __init__(self, archer):
        State.__init__(self, "kiting")
        self.archer = archer
        
        
        self.archer.path_graph = self.archer.world.paths[randint(0, len(self.archer.world.paths)-1)]
        
        
    def do_actions(self):
        if self.archer.target != None:
            if self.archer.enemy_type == "aggro_ranged":
                if self.archer.target.ranged_cooldown > self.archer.ranged_cooldown:
                    self.archer.enemy_atk_cd = self.archer.ranged_cooldown - 0.5
                else:
                    self.archer.enemy_atk_cd = self.archer.target.ranged_cooldown - 0.5
            else:
                x,y = self.archer.position 
                archer_x, archer_y = self.archer.position
                Archer_Lane,Arhcer_LanePosition = self.archer.getcharLane_Position(self.archer)
                self.archer.MovetoSafeLocation_Safe(Archer_Lane,Arhcer_LanePosition)
        
        self.archer.Seconds_passed =(pygame.time.get_ticks()- self.archer.Start_ticks)/1000


    def check_conditions(self):
        if self.archer.target == None:
            if (self.archer.position - self.archer.normal_pos).length() < 5:
                self.archer.velocity = Vector2(0,0)
                self.archer.normal_pos = None
                self.archer.enemy_type = None
                self.archer.Action = "not kited"
                return "seeking"

        else:
            if self.archer.enemy_type == "aggro_ranged": 
                if (self.archer.position -  self.archer.kite_position).length() < 2:
                    self.archer.velocity = Vector2(0,0)
                    
                if self.archer.Seconds_passed >= self.archer.enemy_atk_cd :
                    if self.archer.Action == "not kited":
                        self.archer.Action = "kited"
                    else:
                        self.archer.Action = "not kited"
                    return "attacking"
            else:
                if(self.archer.position -  self.archer.target.position).length() >= self.archer.min_target_distance:
                    self.archer.velocity = Vector2(0,0)
                if self.archer.Seconds_passed >= self.archer.ranged_cooldown:
                   return "attacking"
            

    def entry_actions(self):
        print("Kite_position",self.archer.kite_position)
        print("normal_position",self.archer.normal_pos)
        if self.archer.target == None:
            self.archer.kite_position = self.archer.normal_pos
            self.archer.velocity = self.archer.kite_position - self.archer.position
            if self.archer.velocity.length() > 0:
                self.archer.velocity.normalize_ip();
                self.archer.velocity *= self.archer.maxSpeed
            

        else:
           
            if self.archer.enemy_type == "aggro_ranged":            
                if self.archer.Action == "not kited":
                    x,y = self.archer.position 
                    self.archer.normal_pos = Vector2(x,y)               #Record the archer's original position so that it can move back to this pos
                    archer_x, archer_y = self.archer.position
                    enemy_x, enemy_y = self.archer.target.position
                    Archer_Lane,Arhcer_LanePosition = self.archer.getcharLane_Position(self.archer)
                    Enemy_Lane,Enemy_LanePosition = self.archer.getcharLane_Position(self.archer.target)
                    self.archer.MovetoSafeLocation_Aggro(Archer_Lane,Arhcer_LanePosition,Enemy_Lane,Enemy_LanePosition)
                    
                    
                else:
                    self.archer.kite_position = self.archer.normal_pos
                    self.archer.velocity = self.archer.kite_position - self.archer.position
                    if self.archer.velocity.length() > 0:
                        self.archer.velocity.normalize_ip();
                        self.archer.velocity *= self.archer.maxSpeed            
            else:
                x,y = self.archer.position 
                archer_x, archer_y = self.archer.position
                Archer_Lane,Arhcer_LanePosition = self.archer.getcharLane_Position(self.archer)
                
                self.archer.MovetoSafeLocation_Safe(Archer_Lane,Arhcer_LanePosition)
            
            
        self.archer.Start_ticks = pygame.time.get_ticks()
            
        
        

       


class ArcherStateSeeking_GERPERN(State):

    def __init__(self, archer):

        State.__init__(self, "seeking")
        self.archer = archer

        #self.archer.path_graph = self.archer.world.paths[randint(0, len(self.archer.world.paths)-1)]
        self.archer.path_graph = self.archer.world.paths[0]


    def do_actions(self):

        #A_rect = self.archer.GetORects()
        Archer_Lane,Arhcer_LanePosition = self.archer.getcharLane_Position(self.archer)
        self.archer.velocity = self.archer.move_target.position - self.archer.position
        if self.archer.velocity.length() > 0:
            self.archer.velocity.normalize_ip();
            self.archer.velocity *= self.archer.maxSpeed


    def check_conditions(self):

        # check if opponent is in range
        nearest_opponent = self.archer.world.get_nearest_opponent(self.archer)
        if nearest_opponent is not None:
            opponent_distance = (self.archer.position - nearest_opponent.position).length()
            if opponent_distance <= self.archer.min_target_distance:
                self.archer.target = nearest_opponent
                self.archer.GetEnemyType()
                redtower = pygame.image.load("assets/red_tower.png").convert_alpha()
                if self.archer.target.image == redtower:
                    print("Enemy type: ",self.archer.target.image)
                return "attacking"
        
        if (self.archer.position - self.archer.move_target.position).length() < 8:

            # continue on path
            if self.current_connection < self.path_length:
                self.archer.move_target.position = self.path[self.current_connection].toNode.position
                self.current_connection += 1
            
        return None

    def entry_actions(self):
        
        nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)

        self.path = pathFindAStar(self.archer.path_graph, \
                                  nearest_node, \
                                  self.archer.path_graph.nodes[self.archer.base.target_node_index])

        
        self.path_length = len(self.path)

        if (self.path_length > 0):
            self.current_connection = 0
            self.archer.move_target.position = self.path[0].fromNode.position

        else:
            self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.target_node_index].position


class ArcherStateAttacking_GERPERN(State):

    def __init__(self, archer):
        
        State.__init__(self, "attacking")
        self.archer = archer

    def do_actions(self):

        opponent_distance = (self.archer.position - self.archer.target.position).length()

        # opponent within range
        if opponent_distance <= self.archer.min_target_distance:
            self.archer.velocity = Vector2(0, 0)
            if self.archer.current_ranged_cooldown <= 0:
                self.archer.ranged_attack(self.archer.target.position)
                self.archer.attacked = "True"
                

        else:
            self.archer.velocity = self.archer.target.position - self.archer.position
            if self.archer.velocity.length() > 0:
                self.archer.velocity.normalize_ip();
                self.archer.velocity *= self.archer.maxSpeed


    def check_conditions(self):

        if self.archer.attacked == "True":
            self.archer.attacked = "false"
            return "kiting"

        # target is gone
        if self.archer.world.get(self.archer.target.id) is None or self.archer.target.ko:
            self.archer.target = None
            if self.archer.enemy_type == "aggro_ranged":
                if self.archer.position != self.archer.normal_pos:
                    return "kiting"
            
            self.archer.normal_pos = None
            self.archer.enemy_type = None
            self.archer.Action = "not kited"
            return "seeking"

        return None

    def entry_actions(self):

        return None


class ArcherStateKO_GERPERN(State):

    def __init__(self, archer):

        State.__init__(self, "ko")
        self.archer = archer

    def do_actions(self):

        return None


    def check_conditions(self):

        # respawned
        if self.archer.current_respawn_time <= 0:
            self.archer.current_respawn_time = self.archer.respawn_time
            self.archer.ko = False
            self.archer.path_graph = self.archer.world.paths[randint(0, len(self.archer.world.paths)-1)]
            return "seeking"
            
        return None

    def entry_actions(self):

        self.archer.current_hp = self.archer.max_hp
        self.archer.position = Vector2(self.archer.base.spawn_position)
        self.archer.velocity = Vector2(0, 0)
        self.archer.target = None

        return None
