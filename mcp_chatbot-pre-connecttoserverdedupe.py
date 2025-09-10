from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import json
import asyncio
import nest_asyncio

nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        # Tools list required for Anthropic API
        self.available_tools = []
        # Prompts list for quick display 
        self.available_prompts = []
        # Sessions dict maps tool/prompt names or resource URIs to MCP client sessions
        self.sessions = {}

    async def connect_to_server(self, server_name, server_config):
        try:
            print(f"Connecting to {server_name} server...")
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            
            # Only try to list tools if the server supports it
            try:
                if hasattr(session, 'list_tools'):
                    response = await session.list_tools()
                    if hasattr(response, 'tools'):
                        for tool in response.tools:
                            self.sessions[tool.name] = session
                            self.available_tools.append({
                                "name": tool.name,
                                "description": getattr(tool, 'description', ''),
                                "input_schema": getattr(tool, 'inputSchema', {})
                            })
                        print(f"  ✓ Found {len(response.tools)} tools")
            except Exception as e:
                print(f"  ⚠️ Could not list tools: {str(e)}")
            
            # Only try to list prompts if the server supports it
            try:
                if hasattr(session, 'list_prompts'):
                    prompts_response = await session.list_prompts()
                    if hasattr(prompts_response, 'prompts') and prompts_response.prompts:
                        for prompt in prompts_response.prompts:
                            self.sessions[prompt.name] = session
                            self.available_prompts.append({
                                "name": prompt.name,
                                "description": getattr(prompt, 'description', ''),
                                "arguments": getattr(prompt, 'arguments', {})
                            })
                        print(f"  ✓ Found {len(prompts_response.prompts)} prompts")
            except Exception as e:
                print(f"  ⚠️ Could not list prompts: {str(e)}")
                
            # Only try to list resources if the server supports it
            try:
                if hasattr(session, 'list_resources'):
                    resources_response = await session.list_resources()
                    if hasattr(resources_response, 'resources') and resources_response.resources:
                        for resource in resources_response.resources:
                            resource_uri = str(resource.uri)
                            self.sessions[resource_uri] = session
                        print(f"  ✓ Found {len(resources_response.resources)} resources")
            except Exception as e:
                print(f"  ⚠️ Could not list resources: {str(e)}")
                
            print(f"  ✓ Successfully connected to {server_name}")
            return True
                
        except Exception as e:
            print(f"  ✗ Error connecting to {server_name}: {str(e)}")
            return False

    async def connect_to_servers(self):
        print("\nInitializing MCP servers...")
        try:
            print("Loading server configuration...")
            with open('server_config.json') as f:
                config = json.load(f)
            
            servers = config.get('mcpServers', {})
            print(f"Found {len(servers)} server(s) in config")
            
            if not servers:
                print("No servers found in configuration")
                return False
                
            for server_name, server_config in servers.items():
                print(f"\nAttempting to connect to {server_name}...")
                print(f"Command: {server_config.get('command')} {' '.join(server_config.get('args', []))}")
                if await self.connect_to_server(server_name, server_config):
                    print(f"  ✓ Successfully connected to {server_name}")
                else:
                    print(f"  ✗ Error connecting to {server_name}")
            
            if not self.available_tools:
                print("\nWarning: No tools were loaded from any server")
            else:
                print(f"\nSuccessfully loaded {len(self.available_tools)} tools from all servers")
                
            return True
            
        except FileNotFoundError:
            print("Error: server_config.json not found in current directory")
            print("  ✗ Error: server_config.json not found")
            return False
        except json.JSONDecodeError:
            print("  ✗ Error: server_config.json contains invalid JSON")
            return False
        except Exception as e:
            print(f"  ✗ Error loading server config: {str(e)}")
            return False
    
    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        
        while True:
            response = self.anthropic.messages.create(
                max_tokens = 2024,
                model = 'claude-3-7-sonnet-20250219', 
                tools = self.available_tools,
                messages = messages
            )
            
            assistant_content = []
            has_tool_use = False
            
            for content in response.content:
                if content.type == 'text':
                    print(content.text)
                    assistant_content.append(content)
                elif content.type == 'tool_use':
                    has_tool_use = True
                    assistant_content.append(content)
                    messages.append({'role':'assistant', 'content':assistant_content})
                    
                    # Get session and call tool
                    session = self.sessions.get(content.name)
                    if not session:
                        print(f"Tool '{content.name}' not found.")
                        break
                        
                    result = await session.call_tool(content.name, arguments=content.input)
                    messages.append({
                        "role": "user", 
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": result.content
                            }
                        ]
                    })
            
            # Exit loop if no tool was used
            if not has_tool_use:
                break

    async def get_resource(self, resource_uri):
        session = self.sessions.get(resource_uri)
        
        # Fallback for papers URIs - try any papers resource session
        if not session and resource_uri.startswith("papers://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("papers://"):
                    session = sess
                    break
            
        if not session:
            print(f"Resource '{resource_uri}' not found.")
            return
        
        try:
            result = await session.read_resource(uri=resource_uri)
            if result and result.contents:
                print(f"\nResource: {resource_uri}")
                print("Content:")
                print(result.contents[0].text)
            else:
                print("No content available.")
        except Exception as e:
            print(f"Error: {e}")
    
    async def list_prompts(self):
        """List all available prompts."""
        if not self.available_prompts:
            print("No prompts available.")
            return
        
        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt['arguments']:
                print(f"  Arguments:")
                for arg in prompt['arguments']:
                    arg_name = arg.name if hasattr(arg, 'name') else arg.get('name', '')
                    print(f"    - {arg_name}")
    
    async def execute_prompt(self, prompt_name, args):
        """Execute a prompt with the given arguments."""
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return
        
        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            if result and result.messages:
                prompt_content = result.messages[0].content
                
                # Extract text from content (handles different formats)
                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, 'text'):
                    text = prompt_content.text
                else:
                    # Handle list of content items
                    text = " ".join(item.text if hasattr(item, 'text') else str(item) 
                                  for item in prompt_content)
                
                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text)
        except Exception as e:
            print(f"Error: {e}")
    
    async def chat_loop(self):
        import readline
        import os
        import atexit
        
        # Set up command history
        histfile = os.path.join(os.path.expanduser("~"), ".mcp_chatbot_history")
        try:
            readline.read_history_file(histfile)
            # Limit history to 1000 entries
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
            
        # Save history on exit
        atexit.register(readline.write_history_file, histfile)
        
        # Enable tab completion
        readline.parse_and_bind("tab: complete")
        
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        print("Use @folders to see available topics")
        print("Use @<topic> to search papers in that topic")
        print("Use /prompts to list available prompts")
        print("Use /prompt <name> <arg1=value1> to execute a prompt")
        print("Use Up/Down arrows to navigate command history")
        print("Press Ctrl+C to cancel input\n")
        
        while True:
            try:
                # Use readline for better input handling
                try:
                    query = input("\nQuery: ").strip()
                except EOFError:
                    print("\nUse 'quit' to exit.")
                    continue
                except KeyboardInterrupt:
                    print("\n(To exit, type 'quit' or press Ctrl+D)")
                    continue
                    
                if not query:
                    continue
        
                if query.lower() == 'quit':
                    break
                
                # Check for @resource syntax first
                if query.startswith('@'):
                    # Remove @ sign  
                    topic = query[1:]
                    if topic == "folders":
                        resource_uri = "papers://folders"
                    else:
                        resource_uri = f"papers://{topic}"
                    await self.get_resource(resource_uri)
                    continue
                
                # Check for /command syntax
                if query.startswith('/'):
                    parts = query.split()
                    command = parts[0].lower()
                    
                    if command == '/prompts':
                        await self.list_prompts()
                    elif command == '/prompt':
                        if len(parts) < 2:
                            print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
                            continue
                        
                        prompt_name = parts[1]
                        args = {}
                        
                        # Parse arguments
                        for arg in parts[2:]:
                            if '=' in arg:
                                key, value = arg.split('=', 1)
                                args[key] = value
                        
                        await self.execute_prompt(prompt_name, args)
                    else:
                        print(f"Unknown command: {command}")
                    continue
                
                await self.process_query(query)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
            except KeyboardInterrupt:
                print("\n(To exit, type 'quit' or press Ctrl+D)")
                continue
    
    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    print("\n=== MCP ChatBot ===")
    chatbot = MCP_ChatBot()
    try:
        if not await chatbot.connect_to_servers():
            print("\nFailed to initialize required servers. Exiting.")
            return
            
        print("\nMCP ChatBot Started!")
        print("Type your queries or 'quit' to exit.")
        print("Use @folders to see available topics")
        print("Use @<topic> to search papers in that topic")
        print("Use /prompts to list available prompts")
        print("Use /prompt <name> <arg1=value1> to execute a prompt\n")
        
        await chatbot.chat_loop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    print("Starting MCP ChatBot...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error in main: {str(e)}")
        import traceback
        traceback.print_exc()
    print("MCP ChatBot has stopped.")