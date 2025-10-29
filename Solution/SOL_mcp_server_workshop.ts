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


// Register tools using registerTool method
server.registerTool("time", {
  description: "Get the current time in Israel (Asia/Jerusalem)",
  inputSchema: undefined,
}, async () => {
  return {
    content: [
      {
        type: "text",
        text: new Date().toLocaleString("en-GB", { timeZone: "Asia/Jerusalem" })
      },
    ],
  };
});


server.registerTool("get_weather", {
  description: "Get the current weather of a city",
  inputSchema: { city: z.string() },
}, async (args: { city: string }) => {
  try {
    const https = await import('https');
    const weatherUrl = `https://wttr.in/${encodeURIComponent(args.city)}?format=j1`;
    
    return new Promise((resolve) => {
      https.get(weatherUrl, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try {
            const weather = JSON.parse(data);
            const current = weather["current_condition"][0];
            const weatherData = {
              temp_C: current["temp_C"],
              FeelsLikeC: current["FeelsLikeC"],
              humidity: current["humidity"],
              uvIndex: current["uvIndex"],
              weatherDesc: current["weatherDesc"]?.[0]?.["value"] || "N/A",
              windspeedKmph: current["windspeedKmph"],
            };
            resolve({ content: [{ type: "text", text: JSON.stringify(weatherData) }] });
          } catch (error) {
            resolve({ content: [{ type: "text", text: `Error parsing weather data: ${error}` }] });
          }
        });
      }).on('error', (error) => {
        resolve({ content: [{ type: "text", text: `Error fetching weather: ${error}` }] });
      });
    });
  } catch (error) {
    return { content: [{ type: "text", text: `Error: ${error}` }] };
  }
});

server.registerTool("search_flights", {
  description: "Search for flights between two airports",
  inputSchema: {
    origin: z.string(),
    destination: z.string(),
    date: z.string(),
    return_date: z.string().optional(),
  },
}, async (args: { origin: string; destination: string; date: string; return_date?: string }) => {
  const serpapiKey = process.env.SERPAPI_API_KEY;
  if (!serpapiKey) {
    return { content: [{ type: "text", text: "Error: SERPAPI_API_KEY not set" }] };
  }

  try {
    const json = await new Promise((resolve) => {
      getJson({
        api_key: serpapiKey,
        engine: "google_flights",
        hl: "en",
        gl: "us",
        departure_id: args.origin,
        arrival_id: args.destination,
        outbound_date: args.date,
        ...(args.return_date ? { return_date: args.return_date, type: 1 } : { type: 2 }),
        currency: "USD",
      }, (result: unknown) => resolve(result));
    });

    return { content: [{ type: "text", text: JSON.stringify(json, null, 2) }] };
  } catch (err) {
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