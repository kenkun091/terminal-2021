import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.suicide_direction = None   # "left" or "right"
        self.attack_next_round = False
        self.opponent_missing_1_14 = False
        self.opponent_missing_26_14 = False

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        
        ## edits start
        #game_state.attempt_spawn(DEMOLISHER, [24, 10], 3)
        ## edits end
        
        
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        # self.starter_strategy(game_state)
        self.new_strategy(game_state)

        game_state.submit_turn()
        
        


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def new_strategy(self, game_state):

        # check if we should suicide strategy
        if game_state.get_resource(MP) >= 11 + game_state.turn_number * 0.1 and game_state.turn_number >= 21:
            if self.detect_enemy_left_corner_unit(game_state, unit_type=TURRET, valid_x=None, valid_y=None) < self.detect_enemy_right_corner_unit(game_state, unit_type=TURRET, valid_x=None, valid_y=None):
                self.suicide_direction = "left"
            else:
                self.suicide_direction = "right"


        self.defense_strategy(game_state, suicide_direction=self.suicide_direction)
        self.attack_strategy(game_state, suicide_direction=self.suicide_direction)
            

    def attack_strategy(self, game_state, suicide_direction=None):
        # if game_state.turn_number < 3:
        #     self.stall_with_interceptors(game_state)
        #     return  # skip rest of attack_strategy

        # before turn 25, send demos to weak points
        if game_state.turn_number < 21 and game_state.get_resource(MP) >= 6 + 3 * (game_state.turn_number // 10):
            # list all possible paths
            friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
            deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
            damages = []
            for location in deploy_locations:
                path = game_state.find_path_to_edge(location)
                damage = 0
                for path_location in path:
                    damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
                    damages.append(damage)
            # attack the weakest using SCOUTS 
            idx_min = damages.index(min(damages))
            loc_scout = deploy_locations[idx_min]
            game_state.attempt_spawn(DEMOLISHER, loc_scout, 1000)
            return  # skip rest of attack_strategy
        
        if suicide_direction is not None and self.attack_next_round == False:
            # we will send the ships next round
            self.attack_next_round = True
        elif suicide_direction is not None and self.attack_next_round == True:
            # execute the suicide attack

            game_state.attempt_spawn(WALL, [[23,11]])
            game_state.attempt_remove([[23,11]])

            if self.suicide_direction == "left":
            # # check if hole 2nd spot over from corner position
            #     if game_state.contains_stationary_unit([1, 14]):
            #         # 2 wave scout rush
            #         game_state.attempt_spawn(SCOUT, [16, 2], int(game_state.get_resource(MP) / 2.4))  # < half in first wave
            #         game_state.attempt_spawn(SCOUT, [17, 3], 100)
            #     else:   # spawn demo in front to break wall, then scout behind
            #         game_state.attempt_spawn(DEMOLISHER, [10, 3], 4)
            #         game_state.attempt_spawn(SCOUT, [22, 8], 100)
                game_state.attempt_spawn(SCOUT, [14, 0], int(game_state.get_resource(MP) / 2.1))  # < half in first wave
                game_state.attempt_spawn(SCOUT, [16, 2], 100)
                    

            if self.suicide_direction == "right":
            # # check if hole 2nd spot over from corner position
            #     if game_state.contains_stationary_unit([26, 14]):
            #         # 2 wave scout rush
            #         game_state.attempt_spawn(SCOUT, [11, 2], int(game_state.get_resource(MP) / 2.4))  # < half in first wave
            #         game_state.attempt_spawn(SCOUT, [10, 3], 100)
            #     else:   # spawn demo in front to break wall, then scout behind
            #         game_state.attempt_spawn(DEMOLISHER, [17, 3], 4)
            #         game_state.attempt_spawn(SCOUT, [5, 8], 100)
                game_state.attempt_spawn(SCOUT, [13, 0], int(game_state.get_resource(MP) / 2.1))  # < half in first wave
                game_state.attempt_spawn(SCOUT, [11, 2], 100)
                    

            self.attack_next_round = False
            self.suicide_direction = None





    def defense_strategy(self, game_state, suicide_direction=None):
        """
        suicide_strategy is "left" or "right"
        """
        wall1 = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [5, 11], [22, 11], [11, 9], [16, 9]]
        turret1 = [[5, 10], [22, 10], [11, 8], [16, 8]]
        upgrade1 = [[5, 10], [22, 10]]

        game_state.attempt_spawn(WALL, wall1)
        game_state.attempt_spawn(TURRET, turret1)
        game_state.attempt_upgrade(upgrade1)

        wall2 = [[4, 12], [23, 12], [10, 9], [12, 9], [15, 9], [17, 9], [6, 11], [21, 11], [4, 11], [23, 11], [7, 9], [20, 9]]
        turret2 = [[2, 12], [3, 12], [24, 12], [25, 12], [12, 8], [15, 8], [9, 8], [19, 8], [6, 10], [21, 10]]
        upgrade2 = [[2, 13], [3, 13], [24, 13], [25, 13], [2, 12], [3, 12], [24, 12], [25, 12], [6, 10], [21, 10], [8, 8], [11, 8], [12, 8], [15, 8], [16, 8], [19, 8], [18, 8], [6, 11], [21, 11]]
        game_state.attempt_spawn(WALL, wall2)
        game_state.attempt_spawn(TURRET, turret2)
        game_state.attempt_upgrade(upgrade2)

        wall3 = [[7, 10], [8, 9], [9, 9], [13, 9], [14, 9], [18, 9], [19, 9], [20, 10], [1, 12], [26, 12]]
        turret3 = [[8, 8], [18, 8], [3, 11], [24, 11]]
        upgrade3 = [[0, 13], [1, 13], [26, 13], [27, 13], [1, 12], [26, 12], [5, 11], [22, 11] , [8, 9], [9, 9], [12, 9], [15, 9], [18, 9], [19, 9], [11, 8], [13, 8], [14, 8], [16, 8]]
        game_state.attempt_spawn(WALL, wall3)
        game_state.attempt_spawn(TURRET, turret3)
        game_state.attempt_upgrade(upgrade3)

        support3 = [[11, 4], [12, 4], [13, 4], [14, 4], [15, 4], [16, 4], [12, 3], [13, 3], [14, 3], [15, 3]]
        game_state.attempt_spawn(SUPPORT, support3)



        left_corner = [[0,13], [1,13], [1,12], [2,12], [3,11]]
        right_corner = [[27,13], [26,13], [26,12], [25,12], [24,11]]


        



        """
        # wall pieces to remove when we use suicide strategy
        right_door = [26,13]
        left_door = [1,13]
        # turn 1 initial setup
        turn_1_turrets = [[0, 13], [24, 12], [22, 10]]
        turn_1_walls = [[1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [4, 11], [5, 10], [6, 9], [21, 9], [7, 8], [20, 8], [8, 7], [19, 7], [9, 6], [18, 6], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5], [17, 5]]
        later_turrets = [[4, 12], [5, 12], [22, 12], [23, 12], [5, 11], [19, 10], [20, 10], [21, 10], [19, 9], [20, 9]]
        later_walls = [[3, 13], [4, 13], [5, 13], [22, 13], [23, 13], [24, 13], [19, 11], [20, 11], [18, 10], [18, 9]]

        support_points = [[13, 2], [14, 2], [13, 3], [14, 3], [13, 4], [14, 4], [12, 3], [15, 3], [12, 4], [15, 4], [11, 4], [16, 4]]   # NOTE: this is in order of middle first


        # if we are about to attack, build supports and save 1 SP
        if suicide_direction == "right":
            turn_1_walls.remove(right_door)
            game_state.attempt_remove([right_door])

            if self.attack_next_round:  # is actually attacking this round, spend on support and save 1 SP
                for support_point in support_points:
                    if game_state.get_resource(SP) < 5:
                        return
                    game_state.attempt_spawn(SUPPORT, [support_point])

        elif suicide_direction == "left":
            turn_1_walls.remove(left_door)
            game_state.attempt_remove([left_door])

            if self.attack_next_round:  # is actually attacking this round, spend on support and save 1 SP
                for support_point in support_points:
                    if game_state.get_resource(SP) < 5:
                        return
                    game_state.attempt_spawn(SUPPORT, [support_point])



        #should be just enough to build turn 1
        game_state.attempt_spawn(TURRET, turn_1_turrets)
        game_state.attempt_spawn(WALL, turn_1_walls)


        game_state.attempt_spawn(TURRET, later_turrets)
        game_state.attempt_spawn(WALL, later_walls)
        game_state.attempt_spawn(SUPPORT, support_points)



        # # build or rebuild anything that was destroyed
        # v_wall_points = [[2, 11], [3, 10], [4, 9], [5, 8], [19, 8], [6, 7], [19, 7], [7, 6], [18, 6], [8, 5], [17, 5], [9, 4], [16, 4], [10, 3], [15, 3], [11, 2], [12, 2], [13, 2], [14, 2]]

        # left_turret_points = [[1, 12], [2, 12]]
        # left_wall_points = [[0, 13], [1, 13], [2, 13]]

        # right_turret_points = [[25, 13], [26, 13], [23, 12], [24, 12], [25, 12], [25, 11], [20, 10], [21, 10], [20, 9]]
        # right_wall_points = [[23, 13], [24, 13], [27, 13], [26, 12], [20, 11], [21, 11], [19, 10]]
        # right_support_points = [[22, 10], [21, 9], [20, 8]]

        # game_state.attempt_spawn(WALL, v_wall_points)
        # game_state.attempt_spawn(TURRET, left_turret_points)

        # game_state.attempt_spawn(TURRET, right_turret_points)
        # game_state.attempt_spawn(WALL, left_wall_points)
        # game_state.attempt_spawn(WALL, right_wall_points)
        # game_state.attempt_spawn(SUPPORT, right_support_points)
        
        # use extra points to upgrade front turrets then walls
        for location in reversed([x for x in game_state.game_map]):     # check frontline first by reversing list
            if game_state.get_resource(SP) < 5:     # 5 = cost + save 1 SP
                break
            for unit in game_state.game_map[location]:
                if unit.unit_type == TURRET:
                    game_state.attempt_upgrade([location])
        
        for location in reversed([x for x in game_state.game_map]):
            if game_state.get_resource(SP) < 3:    # 3 = cost + save 1 SP
                break
            for unit in game_state.game_map[location]:
                # if unit.unit_type == WALL and not location in v_wall_points:
                if unit.unit_type == WALL and location != right_door and location != left_door and location[1] > 9: # skip doors and lower walls
                    game_state.attempt_upgrade([location])

        for location in reversed([x for x in game_state.game_map]):
            if game_state.get_resource(SP) < 8:     # save some SP in the bank
                break
            for unit in game_state.game_map[location]:
                if unit.unit_type == SUPPORT:
                    game_state.attempt_upgrade([location])

        # spend SP on anything else
        for location in reversed([x for x in game_state.game_map]):
            if game_state.get_resource(SP) < 8:    # save some SP in the bank
                break
            for unit in game_state.game_map[location]:
                if location != right_door and location != left_door:    # skip doors
                    game_state.attempt_upgrade([location])
        """


    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                self.demolisher_line_strategy(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some Factories to generate more resources
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def destroy_left_corner_strategy(self, game_state):
        if self.detect_enemy_left_corner_unit(game_state, unit_type=None, valid_x=None, valid_y=None) > 6:
            self.demolisher_line_strategy(game_state)



    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        spawns = 0  # only spawn 2
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0 and spawns < 2:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            spawns += 1
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def demolisher_double_line_strategy(self, game_state):
        """
        Build double lines of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)


    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def detect_enemy_left_corner_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        corner_locations = [[0, 14], [1, 14], [2, 14], [3,14], [4,14], [5,14],  [1,15], [2,15], [3,15],[4,15], [5,15]]
        for location in corner_locations:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def detect_enemy_right_corner_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        corner_locations = [[22,14], [23,14],[24,14], [25,14],[26,14], [27,14], [22,15], [23,15], [24,15],[25,15], [26,15]]
        for location in corner_locations:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units


    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
