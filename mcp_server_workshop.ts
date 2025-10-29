#!/usr/bin/env node
/**
 * TypeScript MCP Server with Streamable HTTP Transport
 * Following the official MCP SDK tutorial: https://github.com/modelcontextprotocol/typescript-sdk
 */

import "dotenv/config";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express from "express";
import cors from "cors";
import { z } from "zod";
import { getJson } from "serpapi";

// ---------------------------------------------------------
// ************************* SERVER *************************
// ---------------------------------------------------------

// Create MCP server using the official SDK
const server = new McpServer({
  name: "typescript-server",
  version: "0.1.0",
});

// ---------------------------------------------------------
// ************************* TOOLS *************************
// ---------------------------------------------------------

// Tool Example: Power Calculator
server.registerTool("power_calculator", {
  description: "Calculates the result of raising one number to the power of another (a^b)",
  inputSchema: {
    a: z.number(),
    b: z.number(),
  },
}, (args: { a: number; b: number }) => {
  const result = Math.pow(args.a, args.b);
  return {
    content: [
      {
        type: "text",
        text: `${args.a}^${args.b} = ${result}`,
      },
    ],
  };
});

// ---------------------------------------------------------
// *********************** Excerises ***********************
// ---------------------------------------------------------


// -------------------- Ex-1: Time Tool --------------------
server.registerTool("time", {
  description: "Get the current time in Israel (Asia/Jerusalem)",
  inputSchema: undefined,
}, () => {
  // TODO: Implement time tool
  return {
    content: [
      {
        type: "text",
        text: "TODO: Implement time tool",
      },
    ],
  };
});




// ------------------ Ex-2: Weather Tool -------------------
// TODO: Implement weather tool to get the weather of a city using the https library with the weather url
//const weatherUrl = `https://wttr.in/${encodeURIComponent(args.city)}?format=j1`;






// --------------- Ex-3: Flight Search Tool ----------------
// TODO: Implement flight search tool using SerpAPI using the SERPAPI_API_KEY environment variable
// https://serpapi.com/google-flights-api

server.registerTool("search_flights", {
  description: "Search for flights between two airports",
  inputSchema: {
    origin: z.string(),
    destination: z.string(),
    date: z.string(),
    return_date: z.string().optional(),
  },
}, async (args: { origin: string; destination: string; date: string; return_date?: string }) => {
  
  try {
    // TODO: Use the getJson function from 'serpapi' (already imported above) to call SerpAPI Google Flights API
    // Hint: For return_date argument - set type: 1 for round trip (when return_date is provided), type: 2 for one-way
    return { content: [{ type: "text", text: "TODO: Return the result as JSON string" }] };
  } 
  catch (err) {
    return { content: [{ type: "text", text: `Error: ${(err as Error).message}` }] };
  }
});



// ---------------------------------------------------------
// ********************* START SERVER **********************
// ---------------------------------------------------------

// Start the server with Streamable HTTP transport on port 8000
const PORT = 8000;
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

async function start() {
  console.log("Creating Typescript MCP server...");
  
  // Create the streamable HTTP transport with options
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined, // Stateless mode
    enableJsonResponse: true
  });
  
  // Connect the server to the transport
  await server.connect(transport);
  
  // Setup Express routes
  app.get("/health", (req, res) => {
    res.json({
      status: "ok",
      server: "typescript-server",
      version: "0.1.0",
    });
  });
  
  // MCP endpoint
  app.post("/mcp", async (req, res) => {
    try {
      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      console.error("Error handling MCP request:", error);
      res.status(500).json({
        jsonrpc: "2.0",
        error: {
          code: -32603,
          message: "Internal server error"
        },
        id: null
      });
    }
  });
  
  // Start Express server
  app.listen(PORT, () => {
    console.log(`Typescript MCP server listening on http://localhost:${PORT}`);
    console.log(`Typescript MCP endpoint: http://localhost:${PORT}/mcp`);
  });
}

start().catch(console.error);

export { server };