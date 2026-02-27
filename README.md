# NiFi MCP Server

Model Context Protocol server providing selectable read and write access to Apache NiFi.

- **CDP / Knox**: Use Apache Knox (JWT, cookie, passcode) for NiFi behind Cloudera Data Platform.
- **Open Source NiFi**: Use HTTP Basic auth (`NIFI_USER` / `NIFI_PASSWORD`) for standalone Apache NiFi.

**Requires NiFi 2.x** - older NiFi 1.x is not supported.

![](/screenshots/Nifi-meet-mcp.png)

## Features

- **NiFi 2.x required** - Version check on first API call; NiFi 1.x will be rejected with a clear error
- **Knox authentication** - Supports Bearer tokens, cookies, and passcode tokens for CDP deployments
- **Read-only by default** - Safe exploration of NiFi flows and configuration
- **Intelligent flow building** - Pattern recognition and requirements gathering for complex flows
- **24 read-only MCP tools** for exploring NiFi:
  - `get_nifi_version()` - Version and build information
  - `get_root_process_group()` - Root process group details
  - `list_processors(process_group_id)` - List processors in a process group
  - `list_connections(process_group_id)` - List connections in a process group
  - `get_bulletins(after_ms?)` - Recent bulletins and alerts
  - `list_parameter_contexts()` - Parameter contexts
  - `get_controller_services(process_group_id?)` - Controller services
  - `get_processor_types()` - Available processor types for flow building
  - `search_flow(query)` - Search for components in the flow
  - `get_connection_details(connection_id)` - Detailed connection information
  - `get_processor_details(processor_id)` - Detailed processor configuration
  - `list_input_ports(process_group_id)` - Input ports for a process group
  - `list_output_ports(process_group_id)` - Output ports for a process group
  - `get_processor_state(processor_id)` - Quick processor state check
  - `check_connection_queue(connection_id)` - Queue size (flowfiles + bytes)
  - `get_flow_summary(process_group_id)` - Flow statistics and health overview
  - `analyze_flow_build_request(user_request)` - Intelligent pattern recognition and requirements gathering
  - `get_parameter_context_details(context_id)` - Get parameter context with all parameters
  - `get_flow_health_status(process_group_id)` - Comprehensive flow health check (processors, services, connections, errors)
  - `find_controller_services_by_type(process_group_id, service_type)` - Search for existing controller services by type (prevents 409 conflicts)
  - `check_configuration()` - Validate current environment configuration
  - `get_setup_instructions()` - Interactive setup guidance for NiFi MCP Server
  - `get_best_practices_guide()` - Best practices for building NiFi flows
  - `get_recommended_workflow(flow_type)` - Step-by-step guidance for common flow patterns
- **42 write operations** (when `NIFI_READONLY=false`):
  - `start_processor(processor_id, version)` - Start a processor
  - `stop_processor(processor_id, version)` - Stop a processor
  - `create_processor(...)` - Create a new processor
  - `update_processor_config(...)` - Update processor configuration
  - `delete_processor(processor_id, version)` - Delete a processor
  - `create_connection(...)` - Connect components
  - `delete_connection(connection_id, version)` - Delete a connection
  - `empty_connection_queue(connection_id)` - Empty flowfiles from queue (⚠️ data loss)
  - `create_controller_service(pg_id, service_type, name)` - Create controller services (DBCPConnectionPool, RecordWriters, etc.)
  - `update_controller_service_properties(service_id, version, properties)` - Configure service properties
  - `get_controller_service_details(service_id)` - Get service configuration (read-only but listed here for context)
  - `delete_controller_service(service_id, version)` - Remove controller services
  - `enable_controller_service(service_id, version)` - Enable a controller service
  - `disable_controller_service(service_id, version)` - Disable a controller service
  - `create_process_group(parent_id, name, x, y)` - Create process groups (folders) for organizing flows
  - `update_process_group_name(pg_id, version, name)` - Rename process groups
  - `delete_process_group(pg_id, version)` - Remove empty process groups
  - `create_input_port(pg_id, name, x, y)` - Create input ports for inter-process-group communication
  - `create_output_port(pg_id, name, x, y)` - Create output ports for inter-process-group communication
  - `update_input_port(port_id, version, name)` - Rename input ports
  - `update_output_port(port_id, version, name)` - Rename output ports
  - `delete_input_port(port_id, version)` - Remove input ports
  - `delete_output_port(port_id, version)` - Remove output ports
  - `create_parameter_context(name, description, parameters)` - Create parameter contexts for environment-specific config
  - `update_parameter_context(context_id, version, ...)` - Update parameter contexts
  - `delete_parameter_context(context_id, version)` - Remove parameter contexts
  - `start_input_port(port_id, version)` - Start input port to enable data flow
  - `stop_input_port(port_id, version)` - Stop input port
  - `start_output_port(port_id, version)` - Start output port to enable data flow
  - `stop_output_port(port_id, version)` - Stop output port
  - `apply_parameter_context_to_process_group(pg_id, pg_version, context_id)` - Apply parameter context to enable #{param} usage
  - `start_all_processors_in_group(pg_id)` - Bulk start all processors at once (10-15x faster!)
  - `stop_all_processors_in_group(pg_id)` - Bulk stop all processors at once  
  - `enable_all_controller_services_in_group(pg_id)` - Bulk enable all services at once
  - `terminate_processor(processor_id, version)` - Force-terminate stuck processor (last resort)
  - `start_new_flow(flow_name, flow_description)` - Smart flow builder that automatically creates process groups and enforces best practices

## Quick Start

### For CDP NiFi deployments

Your NiFi API base URL will typically be:
```
https://<your-nifi-host>/nifi-2-dh/cdp-proxy/nifi-app/nifi-api
```

Get your Knox JWT token from the CDP UI and use it with the configurations below.

## Setup

### Option 1: Claude Desktop (Local)

1. **Clone and install:**
   ```bash
   git clone https://github.com/kevinbtalbert/nifi-mcp-server.git
   cd nifi-mcp-server
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Configure Claude Desktop** - Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
    {
      "mcpServers": {
        "nifi-mcp-server": {
          "command": "/FULL/PATH/TO/NiFi-MCP-Server/.venv/bin/python",
          "args": [
            "-m",
            "nifi_mcp_server.server"
          ],
          "env": {
            "MCP_TRANSPORT": "stdio",
            "NIFI_API_BASE": "https://nifi-2-dh-management0.yourshere.cloudera.site/nifi-2-dh/cdp-proxy/nifi-app/nifi-api",
            "KNOX_TOKEN": "<your_knox_bearer_token>",
            "NIFI_READONLY": "true"
          }
        }
      }
    }
   ```

3. **Restart Claude Desktop** and start asking questions about your NiFi flows!

### Option 2: Direct Installation (Cloudera Agent Studio)

For use with Cloudera Agent Studio, use the `uvx` command:

```json
{
  "mcpServers": {
    "nifi-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/kevinbtalbert/nifi-mcp-server@main",
        "run-server"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "NIFI_API_BASE": "https://nifi-2-dh-management0.yourshere.cloudera.site/nifi-2-dh/cdp-proxy/nifi-app/nifi-api",
        "KNOX_TOKEN": "<your_knox_bearer_token>",
        "NIFI_READONLY": "true"
      }
    }
  }
}
```

## Configuration Options

All configuration is done via environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `NIFI_API_BASE` | Yes* | Full NiFi API URL (see examples below for CDP vs Open Source) |
| `KNOX_TOKEN` | No** | Knox JWT token (CDP/Knox deployments) |
| `KNOX_GATEWAY_URL` | No | Knox gateway URL (alternative to `NIFI_API_BASE`) |
| `KNOX_COOKIE` | No | Alternative: full cookie string instead of token |
| `KNOX_PASSCODE_TOKEN` | No | Knox passcode token (auto-exchanged for JWT) |
| `NIFI_USER` | No** | NiFi username for **Open Source NiFi** (HTTP Basic auth) |
| `NIFI_PASSWORD` | No** | NiFi password for **Open Source NiFi** (HTTP Basic auth) |
| `NIFI_READONLY` | No | Read-only mode (default: `true`) |
| `NIFI_VERIFY_SSL` | No | Set to `false` or `0` to **disable SSL verification** (e.g. for self-signed NiFi); applies to all NiFi/Knox requests |
| `NIFI_CA_BUNDLE` | No | Path to **CA certificate file or directory** for NiFi (e.g. self-signed). If set, this is used instead of system CAs. |
| `KNOX_VERIFY_SSL` | No | Verify SSL certificates (default: `true`); overridden by `NIFI_VERIFY_SSL` when set |
| `KNOX_CA_BUNDLE` | No | Path to CA certificate bundle (Knox/CDP) |
| `LOG_LEVEL` | No | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |
| `MCP_TRANSPORT` | No | Transport: `stdio` (default), `http`, or `sse` |
| `FASTMCP_HOST` | No | For HTTP/SSE: bind address (default: `127.0.0.1`) |
| `FASTMCP_PORT` | No | For HTTP/SSE: port (default: `8000`) |

\* Either `NIFI_API_BASE` or `KNOX_GATEWAY_URL` is required.  
\** Use either Knox auth (`KNOX_TOKEN` etc.) **or** Open Source NiFi auth (`NIFI_USER` + `NIFI_PASSWORD`). If neither is set, requests are sent without auth (only works if NiFi allows anonymous access).


**CDP NiFi** – For `NIFI_API_BASE`, use the Knox URL (without `-token`) and add `/nifi-app/nifi-api`.  
Example: `https://nifi-2-dh-management0.yourdomain.cloudera.site/nifi-2-dh/cdp-proxy-token` → `https://nifi-2-dh-management0.yourdomain.cloudera.site/nifi-2-dh/cdp-proxy/nifi-app/nifi-api`

Get Knox Token from the Flow Management Datahub Knox instance:

### Open Source NiFi (standalone Apache NiFi)

No Knox – point directly at the NiFi API. The server uses **token login** (same as nipyapi): it calls **POST /access/token** with your credentials to get a JWT, then uses **Bearer** token for all API requests.

1. **NiFi API URL**: `https://<host>:8443/nifi-api` (or your NiFi base URL + `/nifi-api`).
2. **Auth**: Set `NIFI_USER` and `NIFI_PASSWORD` to a NiFi user that can log in (single-user, LDAP, etc.). The server obtains a token at startup and uses it for all requests.
3. **Self-signed / SSL**: NiFi often uses self-signed certificates. Either set `NIFI_VERIFY_SSL=false` to disable verification, or set `NIFI_CA_BUNDLE` to the path of your CA or server certificate file (e.g. `NIFI_CA_BUNDLE=/path/to/ca.pem`).

Example for Claude Desktop:

```json
"env": {
  "MCP_TRANSPORT": "stdio",
  "NIFI_API_BASE": "https://nifi.example.com:8443/nifi-api",
  "NIFI_USER": "nifi_admin",
  "NIFI_PASSWORD": "your_password",
  "NIFI_READONLY": "true"
}
```

### HTTP / SSE transport (run server without MCP client spawning it)

By default the server uses **stdio** (the MCP client starts the process and talks via stdin/stdout). To run the server as an HTTP process and connect clients (e.g. **Cursor**) to it:

1. Set **`MCP_TRANSPORT=http`** (or `sse`). `http` is implemented as **SSE** so that clients like Cursor find the `/sse` endpoint.
2. Optionally set **`FASTMCP_HOST`** and **`FASTMCP_PORT`** (default: `127.0.0.1:8000`).

Example – start server and listen on port 3030:

```bash
MCP_TRANSPORT=http FASTMCP_PORT=3030 \
NIFI_API_BASE=https://nifi:8443/nifi-api NIFI_USER=nifi NIFI_PASSWORD=secret \
uv run run-server
```

Then point your MCP client at the **SSE URL**, e.g. **`http://127.0.0.1:3030/sse`** (Cursor and similar clients use the `/sse` endpoint). The `GET /.well-known/oauth-authorization-server` 404 is normal when no OAuth is configured.

```json
{
  "mcpServers": {
    "nifi-mcp-server": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/NiFi-MCP-Server", "run-server"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "NIFI_API_BASE": "https://nifi-host:8443/nifi-api",
        "NIFI_USER": "nifi",
        "NIFI_PASSWORD": "ordix-sandbox",
        "NIFI_READONLY": "true",
        "NIFI_VERIFY_SSL": "false"
      }
    }
  }
}
```

Use the same user/password as in your NiFi setup (e.g. `docker-compose` or `authorizers.xml`). Restart the MCP server / IDE after changing the config.

![](/screenshots/knox-token-generation.png)


## Example Usage

### Read-Only Operations (Default)

Once configured, you can ask Claude questions like:

- "What version of NiFi am I running?"
- "List all processors in the root process group"
- "Show me recent bulletins"
- "What parameter contexts are configured?"
- "Tell me about the controller services"
- "What processor types are available for building flows?"
- "Search for processors containing 'kafka'"
- "Show me the details of connection abc-123"

### Write Operations (when NIFI_READONLY=false)

**⚠️ WARNING: Write operations modify your NiFi flows. Use with caution!**

To enable write operations, set `NIFI_READONLY=false` in your configuration. Then you can:

- **Build flows**: "Create a LogAttribute processor named 'MyLogger' in the root process group"
- **Manage processors**: "Start processor with ID abc-123", "Stop all processors in group xyz"
- **Connect components**: "Create a connection from processor A to processor B for the 'success' relationship"
- **Configure**: "Update the scheduling period of processor abc-123 to 30 seconds"
- **Control services**: "Enable the DBCPConnectionPool controller service"

**Examples:**
```
"Create a GenerateFlowFile processor in process group abc-123"
"Connect processor source-123 to processor dest-456 for success relationship"
"Start processor xyz-789"
"Check the queue status for connection conn-456"
"Empty the queue for connection conn-456 before deletion"  (⚠️ deletes flowfiles permanently)
"Delete connection conn-456"
```

**Important Notes:**
- **Version Tracking:** NiFi uses optimistic locking. Always fetch current versions before updates:
  ```python
  processor = get_processor_details(processor_id)
  current_version = processor['revision']['version']
  stop_processor(processor_id, current_version)
  ```
- **Queue Management:** Connections with flowfiles cannot be deleted. Use `get_connection_details()` to check queue status, then `empty_connection_queue()` if needed before deletion.


**Using the example `"List all processors in the root process group"`, we see the following for the example NiFi Canvas:**

![](/screenshots/nifi-canvas-1.png)

![](/screenshots/nifi-readcanvas-1.png)


**Using the example, `"What version of NiFi am I running?"`, we see the following:**

![](/screenshots/nifi-version-check.png)


## License

Apache License 2.0
