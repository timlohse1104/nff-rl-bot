from tools import  *
from objects import *
from routines import *


#This file is for strategy

class ExampleBot(GoslingAgent):
    def run(agent):

        # VARIABLES
        # Locations
        my_location = agent.me.location
        ball_location = agent.ball.location
        foe_location = agent.foes[0].location if len(agent.foes) == 1 else None
        own_goal_location = agent.friend_goal.location
        foe_goal_location = agent.foe_goal.location
        left_field = Vector3(4200*-side(agent.team), ball_location.y + (1000*-side(agent.team)), 0)
        right_field = Vector3(4200*side(agent.team), ball_location.y + (1000*-side(agent.team)), 0)
        print(side(agent.team))
        print(-side(agent.team))
        # new axis friend goal <-> ball <-> foe goal
        my_goal_to_ball,my_ball_distance = (ball_location - own_goal_location).normalize(True)
        goal_to_me = my_location - own_goal_location
        my_distance = my_goal_to_ball.dot(goal_to_me)
        foe_goal_to_ball,foe_ball_distance = (ball_location - foe_goal_location).normalize(True)
        foe_goal_to_foe = foe_location - foe_goal_location
        foe_distance = foe_goal_to_ball.dot(foe_goal_to_foe)
        me_onside = my_distance - 200 < my_ball_distance
        foe_onside = foe_distance - 200 < foe_ball_distance
        # TODO: new axis me <-> ball <-> foe
        # Always get closest boost pad between me and my own goal
        defensive_boosts = [boost for boost in agent.boosts if boost.active and abs(own_goal_location.y - boost.location.y) - 200 < abs((own_goal_location.y - my_location.y))]
        if len(defensive_boosts) > 0:
            closest_pad = defensive_boosts[0]
            for boost in defensive_boosts:
                if (boost.location - my_location).magnitude() < (closest_pad.location - my_location).magnitude():
                    closest_pad = boost
        else:
            closest_pad = None
        pad_close = ((closest_pad.location - my_location).magnitude() < 200) if closest_pad is not None else False
        # other vars
        close = (my_location - ball_location).magnitude() < 2000
        have_boost = agent.me.boost > 20
        enemy_close = (my_location - foe_location).magnitude() < 750
        me_supersonic = agent.me.supersonic
        me_to_ball = (my_location - ball_location).magnitude()
        
        return_to_goal = False
        pickup_boost = False
    

        # DEBUGGING (if blue team)
        if agent.team == 0: 
            agent.debug_stack()
            agent.debug_info()
            # print(f"me_onside: {me_onside}")
            agent.line(own_goal_location, ball_location, [255,255,255])
            agent.line(foe_goal_location, ball_location, [255,255,255])
            my_point = own_goal_location + (my_goal_to_ball * my_distance)
            agent.line(my_point - Vector3(0,0,100), my_point + Vector3(0,0,100), [0,255,0])
            agent.text(f"Speed: {agent.me.velocity.magnitude():.1f}")
        

        # STRATEGY
        # Always check if stack currently has routine to work
        if len(agent.stack) < 1:
            # Kickoff
            if agent.kickoff_flag:
                agent.push(kickoff())

            # Want to grab boost always if its very close
            # elif pad_close and not me_supersonic and :

            # If we are in a good situation and facing the foe goal we try to shoot or put it in a good spot
            elif (close and me_onside) or (not foe_onside and me_onside):
                targets = {"goal":(agent.foe_goal.left_post - Vector3(50,0,0), agent.foe_goal.right_post + - Vector3(50,0,0)), "upfield":(left_field, right_field)}
                shots = find_hits(agent, targets)
                # Possible goal shots
                if len(shots["goal"]) > 0:
                    agent.push(shots["goal"][0])
                # Possible upfield shots
                elif len(shots["upfield"]) > 0 and abs(own_goal_location.y - ball_location.y) < 8490:
                    agent.push(shots["upfield"][0])
                else:
                    if closest_pad is not None:
                        pickup_boost = True

            # If we are not in a good position we retreat to further back boost pads
            elif not me_onside and not have_boost:
                if me_to_ball < 500:
                    targets = {"goal":(agent.foe_goal.left_post - Vector3(50,0,0), agent.foe_goal.right_post + - Vector3(50,0,0)), "upfield":(left_field, right_field)}
                    shots = find_hits(agent, targets)
                    # Possible goal shots
                    if len(shots["goal"]) > 0:
                        agent.push(shots["goal"][0])
                    # Possible upfield shots
                    elif len(shots["upfield"]) > 0 and abs(own_goal_location.y - ball_location.y) < 8490:
                        agent.push(shots["upfield"][0])
                    else:
                        return_to_goal = True
                if closest_pad is not None:
                    agent.push(goto_boost(closest_pad, own_goal_location))
                else:
                    return_to_goal = True

            # If we are not in a good position but we are able to kill the enemy
            elif not me_onside and me_supersonic or agent.me.boost > 60:
                agent.push(demo(foe_location))
                agent.controller.boost = True

            else:
                if me_supersonic and enemy_close:
                    agent.push(demo(foe_location))
                return_to_goal = True

        if return_to_goal:
            agent.push(goto(own_goal_location + Vector3(0,500,0)))
            # relative_friend_goal = own_goal_location - my_location
            # angles = defaultPD(agent, agent.me.local(relative_friend_goal))
            # defaultThrottle(agent, 2300)
            # agent.controller.boost = False if abs(angles[1]) > 0.5 or agent.me.airborne else agent.controller.boost
            # agent.controller.handbrake = True if abs(angles[1]) > 2.8 else False
        
        if pickup_boost:
            agent.push(goto_boost(closest_pad))