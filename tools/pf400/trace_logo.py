import json
import logging
from typing import List, Tuple, Optional
import time
from tools.pf400.driver import Pf400Driver, Location
import os

path = os.path.dirname(os.path.abspath(__file__))

def load_coordinates_from_file(file_path: str) -> List[List[float]]:
    full_path = os.path.join(path, file_path)
    with open(full_path, "r") as f:
        return json.load(f)

def calculate_coordinate_offsets(coordinates):
    """
    Calculate relative offsets between consecutive coordinate points.
    """
    if len(coordinates) < 2:
        return []
    
    offsets = []
    for i in range(1, len(coordinates)):
        prev_x, prev_y = coordinates[i-1]
        curr_x, curr_y = coordinates[i]
        dx = curr_x - prev_x
        dy = curr_y - prev_y
        offsets.append([dx, dy])
    
    return offsets

def calculate_absolute_coordinates(robot_driver: Pf400Driver, offsets: List[List[float]], scale: int = 1) -> List[Location]:
    """
    Calculate absolute coordinates based on current robot position and offsets.
    Each coordinate is calculated based on the previous coordinate (cumulative offsets).
    """
    
    # Get current Cartesian position
    current_pos_response = robot_driver.wherec()
    logging.info(f"Current position response: {current_pos_response}")

    pos_values = current_pos_response.split()
    
    # Extract x, y, z, yaw, pitch, roll (skip the first "0" status code)
    current_coords = [float(val) for val in pos_values[1:]]
    logging.info(f"Starting coordinates: x={current_coords[0]}, y={current_coords[1]}, z={current_coords[2]}")
    
    # Calculate new coordinates for each offset
    absolute_coordinates = []
    
    # Start with the current position as the base
    last_coords = current_coords.copy()
    
    for i, (dx, dy) in enumerate(offsets):
        # Create new coordinate set based on LAST position (not original position)
        new_coords = last_coords.copy()
        
        # Modify x and z (index 0 and 2) based on dx and dy offsets
        new_coords[0] += dx * scale  # x coordinate
        new_coords[2] += dy * scale  # z coordinate (using dy for z-axis modification)

        # Create Location object
        new_location = Location(new_coords)
        absolute_coordinates.append(new_location)
        
        # Update last_coords for the next iteration
        last_coords = new_coords.copy()
        
        logging.info(f"Calculated coordinate {i+1}: x={new_coords[0]}, y={new_coords[1]}, z={new_coords[2]}")
        logging.info(f"  Offset applied: dx={dx * scale}, dy={dy * scale}")
    
    return absolute_coordinates

def move_through_coordinates(robot_driver: Pf400Driver, coordinates: List[Location], 
                           motion_profile: int = 1, delay_between_moves: float = 1.0):
    """
    Move the robot through each coordinate in sequence.
    """
    for i, location in enumerate(coordinates):
        try:
            robot_driver.tcp_ip.write(f"movec 1 {location.to_string()}")
                
        except Exception as e:
            logging.error(f"Failed to move to coordinate {i+1}: {str(e)}")
            raise
    
    while(True):
        state = robot_driver.communicator.get_state()
        if state == "0 20" or state == "0 21":
            break

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    FREE_ONLY = True #set to true to run trace, set to false to set arm to free mode
    TCP_HOST = "192.168.0.1" 
    TCP_PORT = 10100         
    JOINTS = 6               
    GPL_VERSION = "v2"       
    
    #Custom profile, max speed, acc and decc, non straight (curved).
    MOTION_PROFILE = "1 100 100 100 100 0 0 0 0"
    # Initialize robot driver
    robot_driver = Pf400Driver(
        tcp_host=TCP_HOST,
        tcp_port=TCP_PORT,
        joints=JOINTS,
        gpl_version=GPL_VERSION
    )


    try:
        robot_driver.initialize()
        if FREE_ONLY:
            robot_driver.free()
            robot_driver.get_sys_speed()
            input("Please manually position robot arm and press Enter to continue")
        robot_driver.register_motion_profile(MOTION_PROFILE)
        robot_driver.unfree()
        coordinates = load_coordinates_from_file("coordinator.json")
        offsets = calculate_coordinate_offsets(coordinates)
        # Calculate absolute coordinates based on current position and offsets
        absolute_coordinates = calculate_absolute_coordinates(robot_driver, offsets, 1)

        #Write to local file for debuggin 
        with open(os.path.join(path,"absolute_coordinates.txt"),"w") as f:
            for loc in absolute_coordinates:
                f.write(f"{loc.to_string()}\n")
        
        start_time = time.time()
        # Move through each coordinate
        move_through_coordinates(
            robot_driver, 
            absolute_coordinates, 
            motion_profile=1,
            delay_between_moves=0
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"Total time elapsed is {elapsed_time:.2f}")
        
        print("Movement sequence completed successfully!")
            
    except Exception as e:
        logging.error(f"Error during robot operation: {str(e)}")
        raise
        
    finally:
        # Clean up - close robot connection
        logging.info("Closing robot connection...")
        robot_driver.close()