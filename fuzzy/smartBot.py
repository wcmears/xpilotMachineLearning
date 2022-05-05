#Import libraries, including the degree of membership libraries we created
import math
import csv
import libpyAI as ai
from object_distance import ObjectDistance
from turn_angle import TurnAngle
from wall_distance import WallDistance
from speed import Speed
from genetic_algorithm import evolve_one_generation
global generation
generation = 1
global count
count = 0
global check
check = 0
global rowCount
rowCount = 2
global chromosome
with open('fuzzy_population.csv', newline = '') as f:
    csv_reader = csv.reader(f)
    csv_headings = next(csv_reader)
    line = next(csv_reader)
    chromosome = line[0]

def AI_loop():
    # Release keys
    global chromosome
    global generation 
    global count 
    global check
    global rowCount
    ai.thrust(0)
    ai.turnLeft(0)
    ai.turnRight(0)
    ai.setTurnSpeed(20)
    ai.setPower(35)

    # Wall Avoidance
    tracking = int(ai.selfTrackingDeg())
    track_wall = ai.wallFeeler(2000, tracking)
    wall_dist = WallDistance(track_wall, chromosome)
    bot_speed = Speed(ai.selfSpeed(), chromosome)
    wall_danger = calculate_wall_danger(wall_dist, bot_speed)

    # Offense
    enemy_id = ai.closestShipId()
    if enemy_id != -1:
        enemy_distance = ObjectDistance(ai.enemyDistanceId(enemy_id), chromosome)
        ai.lockClose()
        enemy_angle = TurnAngle(abs(ai.selfHeadingDeg() - ai.lockHeadingDeg()), chromosome)
        enemy_chance = calculate_enemy_chance(enemy_angle, enemy_distance)
    else:
        enemy_chance = 0
    

    # Defense
    bullet_xcoor = ai.closestItemX()
    bullet_ycoor = ai.closestItemY()
    ship_xcoor = ai.selfX()
    ship_ycoor = ai.selfY()
    
    if bullet_xcoor == -1 or bullet_ycoor == -1:
        bullet_danger = 0
    else:       

        # Calculating Euclidean dist between ship and bullet
        bullet_dis = math.dist([bullet_xcoor, bullet_ycoor], [ship_xcoor, ship_ycoor])

        # Calculating the angle between the ship and the bullet
        alpha = abs(ship_xcoor - bullet_xcoor) / bullet_dis
        bullet_ang = math.degrees(math.asin(alpha))
    
        # Give inputs and calculate bullet danger based off of aggregation and defuzzification functions
        # at the bottom of this code
        bullet_dist = ObjectDistance(bullet_dis, chromosome)
        bullet_angle = TurnAngle(bullet_ang, chromosome)
        bullet_danger = calculate_bullet_danger(bullet_dist, bullet_angle)

    heading = int(ai.selfHeadingDeg())
    left_wall = ai.wallFeeler(2000, heading + 90)
    right_wall = ai.wallFeeler(2000, heading - 90)
    front_wall = ai.wallFeeler(2000, heading)
    topWall = ai.wallFeeler(2000,90)
    bottomWall = ai.wallFeeler(2000,heading-180)
    
    max_rating = max(wall_danger, bullet_danger, enemy_chance)
    
    if wall_danger == bullet_danger == enemy_chance:
        wall_danger += 1
    	
    print("wall danger: " + str(wall_danger), "bullet danger: " + str(bullet_danger), "enemy chance: " + str(enemy_chance))
    
    # Fire wall danger with top priority
    if wall_danger == max_rating:  
          WALL_DIST = 350 
          if track_wall < WALL_DIST and left_wall < right_wall:
            ai.turnRight(1)
          elif track_wall < WALL_DIST and leftWall >= right_wall:
            ai.turnLeft(1)
          elif left_wall < right_wall:
            ai.turnRight(1)
          else:
            ai.turnLeft(1)
 
          #Thrust rules  
          if ai.selfSpeed() == 0 and front_wall < 300:
            ai.thrust(0)  
          elif front_wall > WALL_DIST+350 and track_wall < WALL_DIST and ai.selfSpeed() < 10:
            ai.thrust(1)
          elif front_wall > WALL_DIST and ai.selfSpeed() < 6:
            ai.thrust(1)
            ai.fireShot()
          elif topWall < 100:
            ai.thrust(1)
          elif right_wall < 100:
            ai.thrust(1)
          elif left_wall < 100: 
            ai.thrust(1)
          elif bottomWall < 100:
            ai.thrust(1)
          else:
            ai.fireShot()
    # Fire enemy chance rating. Statements were made so the bot turns in the direction which allows it to aim at the enemy quickest               
    elif enemy_chance == max_rating:
        enemy_deg = ai.lockHeadingDeg()
       #Shoot if enemy is within 40 degrees of heading 
        if abs(heading - enemy_deg) < 40:
            ai.fireShot() 	
        elif heading < 180 and enemy_deg < 180:
            if heading > enemy_deg:
                ai.turnRight(1)
            else:
                ai.turnLeft(1)
        elif heading > 180 and enemy_deg > 180:
            if enemy_deg > heading:
                ai.turnLeft(1)
            else:
                ai.turnRight(1)
        elif heading > 180 and enemy_deg < 180:
            if enemy_deg > (heading - 180):
                ai.turnRight(1)
            else:
                ai.turnLeft(1)
        else:
            if enemy_deg < (heading+180):
                ai.turnLeft(1)
            else:
                ai.turnRight(1)     
    # If bullet danger is max, thrust pilot to avoid danger. Sets cap for speed so the pilot doesn't lose control   
    elif bullet_danger == max_rating:
        if ai.selfSpeed() < 6:
            ai.thrust(1)

    if ai.selfAlive() == 1:    
        count += 1
        check = 0
   
    if ai.selfAlive() == 0 and check == 0 and rowCount < 52:
    	
    	r = csv.reader(open('fuzzy_population.csv'))
    	lines = list(r)
    	lines[rowCount - 1][1] = str(count)
    	writer = csv.writer(open('fuzzy_population.csv', 'w', newline = ''))
    	writer.writerows(lines)
    	chromosome = lines[rowCount - 1][0]
    	rowCount += 1
    	check = 1
    	count = 0

    elif ai.selfAlive() == 0 and check == 0 and rowCount == 52:
        evolve_one_generation()
        with open('fuzzy_population.csv', newline = '') as f:
            csv_reader = csv.reader(f)
            csv_headings = next(csv_reader)
            line = next(csv_reader)
            chromosome = line[0]
        rowCount = 2
        count = 0
        check = 1
        generation += 1
        print('Generation ' + str(generation))

# Functions for aggregation and defuzzification
# Clipping is done by taking the minimum degree of membership for two variables (ex. fast bot speed with 0.2 and near wall 0.4 would give degree of membership 0.2). Since three degrees of membership are given for each danger rating (high, avg, and low danger) the max of the three is returned.
def calculate_wall_danger(wall_dist: WallDistance, bot_speed: Speed):
    wall_high_danger_dom_one = min(wall_dist.near_dom, bot_speed.fast_dom)
    wall_high_danger_dom_two = min(wall_dist.medium_dom, bot_speed.fast_dom)
    wall_high_danger_dom_three = min(wall_dist.near_dom, bot_speed.medium_dom)
    wall_high_danger_dom = max(wall_high_danger_dom_one, wall_high_danger_dom_two,  wall_high_danger_dom_three)

    wall_avg_danger_dom_one = min(wall_dist.near_dom, bot_speed.slow_dom)
    wall_avg_danger_dom_two = min(wall_dist.medium_dom, bot_speed.medium_dom)
    wall_avg_danger_dom_three = min(wall_dist.far_dom, bot_speed.fast_dom)
    wall_avg_danger_dom = max(wall_avg_danger_dom_one, wall_avg_danger_dom_two, wall_avg_danger_dom_three)

    wall_low_danger_dom_one = min(wall_dist.medium_dom, bot_speed.slow_dom)
    wall_low_danger_dom_two = min(wall_dist.far_dom, bot_speed.medium_dom)
    wall_low_danger_dom_three = min(wall_dist.far_dom, bot_speed.slow_dom)
    wall_low_danger_dom = max(wall_low_danger_dom_one, wall_low_danger_dom_two, wall_low_danger_dom_three)

    return calculate_centroid(wall_low_danger_dom, wall_avg_danger_dom, wall_high_danger_dom)


def calculate_enemy_chance(enemy_angle: TurnAngle, enemy_distance: ObjectDistance):
    high_enemy_chance_dom_one = min(enemy_angle.small_dom, enemy_distance.near_dom)
    high_enemy_chance_dom_two = min(enemy_angle.medium_dom, enemy_distance.near_dom)
    high_enemy_chance_dom_three = min(enemy_angle.small_dom, enemy_distance.medium_dom)
    high_enemy_chance_dom = max(high_enemy_chance_dom_one, high_enemy_chance_dom_two,  high_enemy_chance_dom_three) 

    avg_enemy_chance_dom_one = min(enemy_angle.large_dom, enemy_distance.near_dom)
    avg_enemy_chance_dom_two = min(enemy_angle.medium_dom, enemy_distance.medium_dom)
    avg_enemy_chance_dom_three = min(enemy_angle.small_dom, enemy_distance.far_dom)
    avg_enemy_chance_dom = max(avg_enemy_chance_dom_one, avg_enemy_chance_dom_two, avg_enemy_chance_dom_three) 

    low_enemy_chance_dom_one = min(enemy_angle.medium_dom, enemy_distance.far_dom)
    low_enemy_chance_dom_two = min(enemy_angle.large_dom, enemy_distance.medium_dom)
    low_enemy_chance_dom_three = min(enemy_angle.large_dom, enemy_distance.far_dom)
    low_enemy_chance_dom = max(low_enemy_chance_dom_one, low_enemy_chance_dom_two, low_enemy_chance_dom_three)
    
    return calculate_centroid(low_enemy_chance_dom, avg_enemy_chance_dom, high_enemy_chance_dom)


def calculate_bullet_danger(bullet_dist: ObjectDistance, bullet_angle: TurnAngle):
    bullet_high_danger_dom_one = min(bullet_dist.near_dom, bullet_angle.small_dom)
    bullet_high_danger_dom_two = min(bullet_dist.near_dom, bullet_angle.medium_dom)
    bullet_high_danger_dom_three = min(bullet_dist.medium_dom, bullet_angle.small_dom)
    bullet_high_danger_dom = max(bullet_high_danger_dom_one, bullet_high_danger_dom_two, bullet_high_danger_dom_three)

    bullet_med_danger_dom_one = min(bullet_dist.near_dom, bullet_angle.large_dom)
    bullet_med_danger_dom_two = min(bullet_dist.medium_dom, bullet_angle.medium_dom)
    bullet_med_danger_dom_three = min(bullet_dist.far_dom, bullet_angle.small_dom)
    bullet_med_danger_dom = max(bullet_med_danger_dom_one, bullet_med_danger_dom_two, bullet_med_danger_dom_three) 

    bullet_low_danger_dom_one = min(bullet_dist.medium_dom, bullet_angle.large_dom)
    bullet_low_danger_dom_two = min(bullet_dist.far_dom, bullet_angle.medium_dom)
    bullet_low_danger_dom_three = min(bullet_dist.far_dom, bullet_angle.large_dom)
    bullet_low_danger_dom = max(bullet_low_danger_dom_one, bullet_low_danger_dom_two, bullet_low_danger_dom_three)

    return calculate_centroid(bullet_low_danger_dom, bullet_med_danger_dom, bullet_high_danger_dom)
    

# Function to calculate the centroid of three aggregated outputs. This is done in intervals of 10, and the crisp output returned is a number 0-100. 30 is meant to represent 0+10+20, 180 is 30+40+50+60, and 340 is the sum of the rest of the numbers through 100. This is divided by the amount of intervals each degree of membership had in the sum (ex. low has 0, 10, and 20 so low's degree of membership is divided by 3).
def calculate_centroid(low, medium, high):
    if (low+medium+high) == 0:
    	return 0
    else:
    	return (30 * low + 180 * medium + 340 * high) / (3 * low + 4 * medium + 4 * high)
    
ai.start(AI_loop, ["-name", "bestBot", "-join", "localhost"])
