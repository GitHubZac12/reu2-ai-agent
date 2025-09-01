# agent.py is an AI agent made to generate a list of commands which can be read by the Interbotix VX300 robotic arm.
# Two files are generated and each hold the same set of commands for the robotic arm. A JSON file for simple integration
# of the command list into Unity(which only supports C#) and a Python file for easy testing of the generated command list
# in a more common ROS2 simulator or on the physical robotic arm. 

# Import standard and external libraries
import os
import math
import json
from llama_index.core.agent import ReActAgent  # ReAct-based agent from LlamaIndex
from llama_index.core.tools import FunctionTool  # Utility for wrapping functions as tools
from llama_index.llms.openai import OpenAI  # OpenAI LLM wrapper from LlamaIndex

# Set the OpenAI API key
os.environ["OPENAI_API_KEY"] = ""

# Initialize lists to store outputs
json_commands = []   # Stores Unity-compatible JSON commands
python_commands = [] # Stores raw Python commands (for ROS2 python script generation)

# Hold the robot’s position in Cartesian space
arm_state = {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0
}

# ----------- Function Tool Definitions -----------

# Move the robot's postion in Cartesian space
def move_cartesian(x: float = 0.0, y: float = 0.0, z: float = 0.0):
    # Update the robot's current state
    arm_state["x"] += x
    arm_state["y"] += y
    arm_state["z"] += z

    # Append a JSON-friendly version of the command
    json_commands.append({
        "type": "cartesian_move",
        "x": arm_state["x"],
        "y": arm_state["y"],
        "z": arm_state["z"]
    })

    # Append a Python-friendly version of the command
    python_commands.append(
        f"bot.arm.set_ee_cartesian_trajectory(x={arm_state['x']}, y={arm_state['y']}, z={arm_state['z']})"
    )

# Rotate the robot's joints by a specified degree value
def rotate_joint(joint_name: str, degrees: float):
    radians = math.radians(degrees)

    # Append a JSON-friendly version of the command
    json_commands.append({
        "type": "rotate_joint",
        "joint_name": joint_name,
        "degrees": degrees
    })

    # Append a Python-friendly version of the command
    python_commands.append(
        f"bot.arm.set_single_joint_position(joint_name='{joint_name}', position={radians})"
    )

# Control the robot's gripper
def control_gripper(action: str):

    # Append a JSON-friendly version of the command
    json_commands.append({
        "type": "gripper",
        "action": action.lower()
    })

    # Append a Python-friendly version of the command
    python_commands.append(
        f"bot.gripper.{action}()"
    )

# ----------- Wrap All Functions as LLM Tools -----------

tools = [
    FunctionTool.from_defaults(fn=move_cartesian),
    FunctionTool.from_defaults(fn=rotate_joint),
    FunctionTool.from_defaults(fn=control_gripper)
]

# ----------- Create the LLM and Agent -----------

# Load the OpenAI model via LlamaIndex
llm = OpenAI(model="gpt-4o-mini", temperature=0)

# Create a ReActAgent that uses the provided tools and model
agent = ReActAgent.from_tools(tools, llm=llm, verbose=True, max_iterations=20)

# User input in natural language (example movement script)
user_input = (
    "move up 5 meters, move forward 10 meters, move down 5 meters, close gripper, move up 5 meters, rotate base 180 degrees, open gripper"
)

# Initialize chat history for agent
chat_history = []

# Run the agent on the user's input
agent_response = agent.stream_chat(user_input, chat_history=chat_history)

# Print results for debugging/inspection
print(agent_response)
print(json_commands)
print(python_commands)

# ----------- Save Commands to Files -----------

# Write the Unity-readable JSON command queue file
def write_json_file(filename="generated_json_commands.json"):
    with open(filename, "w") as f:
        json.dump(json_commands, f, indent=2)

# Write the Python script that executes ROS2 commands using Interbotix's library
def write_python_file(filename="generated_python_commands.py"):
    with open(filename, "w") as f:
        f.write("from interbotix_xs_modules.arm import InterbotixManipulatorXS\n\n")
        f.write("bot = InterbotixManipulatorXS(\n")
        f.write("    robot_model='vx300',\n")
        f.write("    group_name='arm',\n")
        f.write("    gripper_name='gripper'\n")
        f.write(")\n\n")
        for command in python_commands:
            f.write(f"{command.strip()}\n")

# generate files
write_json_file()
write_python_file()
