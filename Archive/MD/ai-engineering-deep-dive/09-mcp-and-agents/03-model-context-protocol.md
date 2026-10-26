# 09.03 — Model Context Protocol (MCP)

> **One sentence:** MCP is an open standard that provides a universal way for AI models to connect to external data sources and tools — like USB for AI, letting any model work with any tool through a standardized interface.

---

## The Problem MCP Solves

```
Before MCP:
─────────────
App A + Tool 1: Custom integration A-1
App A + Tool 2: Custom integration A-2
App A + Tool 3: Custom integration A-3
App B + Tool 1: Custom integration B-1  ← Different from A-1!
App B + Tool 2: Custom integration B-2
App B + Tool 3: Custom integration B-3
= 6 custom integrations (N × M problem)

After MCP:
──────────
App A → MCP → Tool 1
App A → MCP → Tool 2
App A → MCP → Tool 3
App B → MCP → Tool 1  ← Same interface!
App B → MCP → Tool 2
App B → MCP → Tool 3
= 3 server implementations + 2 client implementations (N + M)
```

```mermaid
graph TB
    subgraph "MCP Clients (AI Apps)"
        C1[Cursor]
        C2[Claude Desktop]
        C3[Your Custom App]
    end
    
    subgraph "MCP Protocol"
        P[Standard JSON-RPC Interface]
    end
    
    subgraph "MCP Servers (Tools & Data)"
        S1[GitHub Server]
        S2[Slack Server]
        S3[Database Server]
        S4[File System Server]
        S5[Your Custom Server]
    end
    
    C1 & C2 & C3 --> P
    P --> S1 & S2 & S3 & S4 & S5
```

---

## MCP Architecture

```mermaid
graph LR
    subgraph "MCP Client"
        A[AI Application] --> B[MCP Client SDK]
    end
    
    subgraph "Transport"
        C["JSON-RPC over<br/>stdio / SSE / HTTP"]
    end
    
    subgraph "MCP Server"
        D[MCP Server SDK] --> E["Resources<br/>(data)"]
        D --> F["Tools<br/>(actions)"]
        D --> G["Prompts<br/>(templates)"]
    end
    
    B --> C --> D
```

### Three Primitives

| Primitive | What | Direction | Example |
|-----------|------|-----------|---------|
| **Resources** | Data the model can read | Server → Client | Files, database records, API responses |
| **Tools** | Actions the model can perform | Client → Server | Search, create, update, delete |
| **Prompts** | Pre-built prompt templates | Server → Client | "Summarize this repo", "Debug this error" |

---

## Building an MCP Server

```python
"""
Example: A simple MCP server that provides weather data.
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
import json

# Create the server
server = Server("weather-server")

# ─── TOOLS: Actions the model can take ───────────────────

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_weather",
            description="Get current weather for a city. Returns temperature, "
                        "condition, humidity, and wind speed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., 'Tokyo', 'New York')"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_forecast",
            description="Get 5-day weather forecast for a city.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "days": {"type": "integer", "default": 5, "maximum": 7}
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_weather":
        # In production: call actual weather API
        city = arguments["city"]
        units = arguments.get("units", "celsius")
        
        weather_data = {
            "city": city,
            "temperature": 22 if units == "celsius" else 72,
            "units": units,
            "condition": "sunny",
            "humidity": 45,
            "wind_speed": 12
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(weather_data, indent=2)
        )]
    
    elif name == "get_forecast":
        city = arguments["city"]
        days = arguments.get("days", 5)
        
        forecast = [
            {"day": f"Day {i+1}", "high": 20 + i, "low": 12 + i, "condition": "sunny"}
            for i in range(days)
        ]
        
        return [TextContent(
            type="text",
            text=json.dumps(forecast, indent=2)
        )]

# ─── RESOURCES: Data the model can read ──────────────────

@server.list_resources()
async def list_resources():
    return [
        Resource(
            uri="weather://cities",
            name="Available Cities",
            description="List of cities with weather data",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    if uri == "weather://cities":
        cities = ["Tokyo", "New York", "London", "Paris", "Sydney"]
        return json.dumps(cities)

# ─── Run the server ──────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Configuring MCP in Your App

```json
// ~/.cursor/mcp.json (or claude_desktop_config.json)
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["weather_server.py"],
      "env": {
        "WEATHER_API_KEY": "your-key-here"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_..."
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost/db"
      }
    }
  }
}
```

---

## Building an MCP Client

```python
"""
Example: Using an MCP server from your application.
"""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_weather_server():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["weather_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            
            # Call a tool
            result = await session.call_tool(
                "get_weather",
                arguments={"city": "Tokyo", "units": "celsius"}
            )
            print(f"Weather: {result.content[0].text}")
            
            # Read a resource
            resource = await session.read_resource("weather://cities")
            print(f"Cities: {resource.contents[0].text}")

import asyncio
asyncio.run(use_weather_server())
```

---

## MCP + LLM Integration

```python
async def agent_with_mcp(user_query: str):
    """
    Connect an LLM to MCP tools for a complete agent.
    """
    # 1. Connect to MCP servers
    mcp_tools = await discover_mcp_tools()  # Get all available tools
    
    # 2. Convert MCP tools to OpenAI function format
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        }
        for tool in mcp_tools
    ]
    
    # 3. Standard agent loop
    messages = [
        {"role": "system", "content": "You have access to various tools via MCP."},
        {"role": "user", "content": user_query}
    ]
    
    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=openai_tools
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        if not message.tool_calls:
            return message.content
        
        # Execute MCP tool calls
        for call in message.tool_calls:
            result = await mcp_session.call_tool(
                call.function.name,
                arguments=json.loads(call.function.arguments)
            )
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result.content[0].text
            })
```

---

## Popular MCP Servers

| Server | What it does | Use case |
|--------|-------------|----------|
| **GitHub** | Read repos, create PRs, manage issues | Dev agents |
| **PostgreSQL** | Query databases | Data analysis |
| **Slack** | Send messages, read channels | Communication |
| **Google Drive** | Read/write documents | Knowledge management |
| **Brave Search** | Web search | Research agents |
| **File System** | Read/write local files | Local automation |
| **Puppeteer** | Control a browser | Web testing |

---

## Key Takeaways

1. **MCP = USB for AI** — standardized protocol for connecting models to tools
2. **Three primitives:** Resources (data), Tools (actions), Prompts (templates)
3. **Server-client architecture** — servers wrap external services, clients consume them
4. **JSON-RPC transport** — stdio for local, SSE for remote
5. **Growing ecosystem** — dozens of pre-built servers for common services

---

## 💼 FAANG Interview Questions

1. *"Why do we need a protocol like MCP instead of just custom API integrations?"*
2. *"Design an MCP server for a company's internal documentation system."*
3. *"How would you secure an MCP server that has access to production databases?"*
