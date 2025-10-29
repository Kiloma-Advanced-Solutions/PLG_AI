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
import { google } from "googleapis";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";
import { getJson } from "serpapi";

// Helper function to get current time in Israel
function getIsraelTime(): string {
  return new Date().toLocaleString("en-GB", { timeZone: "Asia/Jerusalem" });
}

// // Helper function to get Google Calendar service
// async function getCalendarService() {
//   const tokenPath = resolve(process.cwd(), "token.json");
  
//   if (!existsSync(tokenPath)) {
//     throw new Error("token.json not found. Please run the OAuth authentication.");
//   }
  
//   const token = JSON.parse(readFileSync(tokenPath, "utf8"));
//   const oAuth2Client = new google.auth.OAuth2(token.client_id, token.client_secret, "https://localhost/8080/");
  
//   oAuth2Client.setCredentials({
//     access_token: token.token,
//     refresh_token: token.refresh_token,
//     expiry_date: new Date(token.expiry).getTime(),
//   });
  
//   return google.calendar({ version: "v3", auth: oAuth2Client });
// }

// Create MCP server using the official SDK
const server = new McpServer({
  name: "typescript-demo-server",
  version: "0.1.0",
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
        text: getIsraelTime(),
      },
    ],
  };
});

server.registerTool("get_weather", {
  description: "Get the current weather of a city",
  inputSchema: {
    city: z.string(),
  },
}, async (args: { city: string }) => {
    try {
      const https = await import('https');
      const url = encodeURIComponent(args.city);
      const weatherUrl = `https://wttr.in/${url}?format=j1`;
      
      return new Promise((resolve) => {
        https.get(weatherUrl, (res) => {
          let data = '';
          
          res.on('data', (chunk) => {
            data += chunk;
          });
          
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
              
              resolve({
                content: [
                  {
                    type: "text",
                    text: JSON.stringify(weatherData),
                  },
                ],
              });
            } catch (error) {
              resolve({
                content: [
                  {
                    type: "text",
                    text: `Error parsing weather data: ${error}`,
                  },
                ],
              });
            }
          });
        }).on('error', (error) => {
          resolve({
            content: [
              {
                type: "text",
                text: `Error fetching weather: ${error}`,
              },
            ],
          });
        });
      });
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error: ${error}`,
          },
        ],
      };
    }
  }
);

// server.registerTool("create_calendar_event", {
//   description: "Create a new Google Calendar event",
//   inputSchema: {
//     summary: z.string(),
//     start_time: z.string(),
//     end_time: z.string(),
//     description: z.string().optional(),
//   },
// }, async (args: { summary: string; start_time: string; end_time: string; description?: string }) => {
//   try {
//     const calendar = await getCalendarService();
    
//     const event = {
//       summary: args.summary,
//       description: args.description || "",
//       start: {
//         dateTime: args.start_time,
//         timeZone: "Asia/Jerusalem",
//       },
//       end: {
//         dateTime: args.end_time,
//         timeZone: "Asia/Jerusalem",
//       },
//     };

//     const response = await calendar.events.insert({
//       calendarId: "primary",
//       requestBody: event as any,
//     });

//     return {
//       content: [
//         {
//           type: "text",
//           text: `✅ האירוע '${args.summary}' נוצר בהצלחה!\nזמן: ${args.start_time} - ${args.end_time}\nID: ${response.data.id}`,
//         },
//       ],
//     };
//   } catch (error: any) {
//     return {
//       content: [
//         {
//           type: "text",
//           text: `❌ שגיאה ביצירת אירוע: ${error.message}`,
//         },
//       ],
//     };
//   }
// });







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
    return {
      content: [
        { type: "text", text: "Error: SERPAPI_API_KEY environment variable is not set." },
      ],
    };
  }

  try {
    const json = await new Promise((resolve, reject) => {
      getJson(
        {
          api_key: serpapiKey,
          engine: "google_flights",
          hl: "en",
          gl: "us",
          departure_id: args.origin,
          arrival_id: args.destination,
          outbound_date: args.date,
          // Only include return_date and type=1 if provided
          ...(args.return_date
            ? { return_date: args.return_date, type: 1 }
            : { type: 2 }),
          currency: "USD",
        },
        (json: unknown) => resolve(json),
      );
    });

    return {
      content: [
        { type: "text", text: JSON.stringify(json, null, 2) },
      ],
    };
  } catch (err) {
    console.error("Flight search error:", err);
    return {
      content: [
        { type: "text", text: `Error fetching flight data: ${(err as Error).message}` },
      ],
    };
  }
});


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
      server: "typescript-demo-server",
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