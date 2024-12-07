# factorio_mcp.py

from fastmcp import FastMCP
import httpx
import os
from typing import Optional, List, Union, Dict

# Create MCP server with httpx dependency
mcp = FastMCP("Factorio Server", dependencies=["httpx"])

# Configuration for the RCON backend 
BACKEND_URL = "http://factorio.towerhouse.london:8000"

@mcp.tool()
def execute_command(command: str) -> str:
    """
    Execute a Factorio console command via RCON
    
    Args:
        command: The Factorio console command to execute
        
    Returns:
        The response from the server
    """
    # Get API key from environment
    api_key = os.environ.get("API_KEY")
    if not api_key:
        return "Error: API_KEY environment variable not set"

    response = httpx.post(
        f"{BACKEND_URL}/execute_command",
        headers={"X-API-Key": api_key},
        json={"command": command}
    )
    
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"
        
    data = response.json()
    return data["result"]

@mcp.tool()
def get_player_count() -> str:
    """Get the current number of players on the server"""
    return execute_command("/players online")

@mcp.tool()
def send_message(message: str) -> str:
    """
    Send a message to all players on the server
    
    Args:
        message: The message to broadcast
    """
    return execute_command(f'/sc game.print("[MCP] {message}")')

@mcp.tool()
def run_lua(code: str, explanation: Optional[str] = None) -> str:
    """
    Run arbitrary Lua code on the Factorio server
    
    Args:
        code: The Lua code to execute
        explanation: Optional explanation of what the code does, will be announced to players
        
    Returns:
        The response from the server
    """
    # Clean up code to avoid command injection - strip any /sc prefix if provided
    code = code.strip()
    if code.startswith("/sc"):
        code = code[3:].strip()
    
    # If an explanation is provided, announce it first
    if explanation:
        send_message(f"Action: {explanation}")
    
    return execute_command(f"/sc {code}")

@mcp.tool()
def give_items(player: str, item: str, count: int = 1) -> str:
    """
    Give items to a player
    
    Args:
        player: Player name
        item: Item name (e.g., 'iron-plate', 'express-transport-belt')
        count: Number of items to give
    """
    return run_lua(
        f'game.players["{player}"].insert{{name="{item}", count={count}}}',
        f"Giving {count}x {item} to {player}"
    )

@mcp.tool()
def teleport_player(player: str, x: float, y: float) -> str:
    """
    Teleport a player to specific coordinates
    
    Args:
        player: Player name
        x: X coordinate
        y: Y coordinate
    """
    return run_lua(
        f'game.players["{player}"].teleport({{x={x}, y={y}}})',
        f"Teleporting {player} to ({x}, {y})"
    )

@mcp.tool()
def get_player_info(player: str) -> str:
    """
    Get information about a player
    
    Args:
        player: Player name
    """
    code = f'''
    local p = game.players["{player}"]
    return string.format(
        "Player %s:\\n" ..
        "Position: (%.1f, %.1f)\\n" ..
        "Surface: %s\\n" ..
        "Connected: %s\\n" ..
        "Admin: %s",
        p.name,
        p.position.x, p.position.y,
        p.surface.name,
        p.connected,
        p.admin
    )
    '''
    return run_lua(code, f"Getting info about {player}")

@mcp.tool()
def take_screenshot(player: Optional[str] = None, resolution: Optional[Dict[str, int]] = None) -> str:
    """
    Take a screenshot of the game
    
    Args:
        player: Optional player name to take screenshot from their perspective
        resolution: Optional dictionary with 'width' and 'height' for screenshot resolution
    """
    if resolution is None:
        resolution = {"width": 1920, "height": 1080}
    
    code = f'''
    game.take_screenshot{{
        player = game.players["{player}"] or nil,
        resolution = {{{resolution["width"]}, {resolution["height"]}}},
        zoom = 1,
        show_gui = true
    }}
    return "Screenshot taken"
    '''
    msg = f"Taking screenshot" + (f" from {player}'s perspective" if player else "")
    return run_lua(code, msg)

@mcp.prompt()
def help_prompt() -> str:
    """Get help about available Factorio commands"""
    return """I can help you manage your Factorio server. Here are the available tools:

1. Basic Commands:
   - get_player_count() - See who's playing
   - send_message(message) - Send a message to all players
   - run_lua(code, explanation) - Execute arbitrary Lua code with optional announcement

2. Player Management:
   - give_items(player, item, count) - Give items to a player
   - teleport_player(player, x, y) - Teleport a player
   - get_player_info(player) - Get detailed player information

3. Utilities:
   - take_screenshot(player=None, resolution=None) - Take a game screenshot
   - execute_command(command) - Execute any Factorio console command

What would you like to do?"""

if __name__ == "__main__":
    mcp.run()