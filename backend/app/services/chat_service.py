import asyncio
import logging
from typing import List, Dict, Any
import json
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai
from fastmcp import Client
from app.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        if settings.ai_provider == "gemini":
            genai.configure(api_key=settings.google_api_key)
            self.client_ai = genai.GenerativeModel(settings.google_model)
            self.model = settings.google_model
        elif settings.ai_provider == "claude":
            self.client_ai = Anthropic(api_key=settings.anthropic_api_key)
            self.model = settings.anthropic_model
        else:
            self.client_ai = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
            
        self.ai_provider = settings.ai_provider
        self.mcp_server_path = Path(__file__).parent.parent / "mcp" / "metrics_server.py"
    
    async def chat_with_metrics(self, message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Chat with LLM using FastMCP client for metrics access"""
        try:
            client = Client(str(self.mcp_server_path))
            
            async with client:
                tools = await client.list_tools()
                
                if self.ai_provider == "gemini":
                    return await self._chat_with_gemini(client, tools, message, conversation_history)
                elif self.ai_provider == "claude":
                    return await self._chat_with_claude(client, tools, message, conversation_history)
                else:
                    return await self._chat_with_openai(client, tools, message, conversation_history)
                    
        except Exception as e:
            logger.error(f"Error in chat_with_metrics: {e}")
            return f"Sorry, I encountered an error while analyzing your metrics: {str(e)}"
    
    async def _chat_with_gemini(self, mcp_client, tools, message: str, conversation_history: List[Dict[str, str]] = None):
        """Handle chat with Gemini"""
        # Convert MCP tools to Gemini format
        gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        # Build conversation for Gemini
        conversation = self._build_gemini_conversation(message, conversation_history)
        
        try:
            # First call to Gemini with function calling
            response = self.client_ai.generate_content(
                conversation,
                tools=gemini_tools,
                tool_config={'function_calling_config': {'mode': 'AUTO'}}
            )
            
            # Check if Gemini wants to call functions
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        # Extract function call details
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args)
                        
                        logger.info(f"Gemini calling tool: {function_name} with args: {function_args}")
                        
                        # Call MCP tool
                        tool_result = await mcp_client.call_tool(function_name, function_args)
                        
                        # Build function response for Gemini
                        function_response = genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={'result': str(tool_result.data)}
                            )
                        )
                        
                        # Continue conversation with function result
                        conversation.append({
                            'role': 'model',
                            'parts': [part]
                        })
                        conversation.append({
                            'role': 'user', 
                            'parts': [function_response]
                        })
                        
                        # Generate final response
                        final_response = self.client_ai.generate_content(conversation)
                        return final_response.text
                
                # No function calls, return direct response
                return response.text
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Sorry, I encountered an error with the Gemini API: {str(e)}"
    
    async def _chat_with_claude(self, mcp_client, tools, message: str, conversation_history: List[Dict[str, str]] = None):
        """Handle chat with Claude (existing implementation)"""
        # ... existing Claude implementation
        pass
    
    async def _chat_with_openai(self, mcp_client, tools, message: str, conversation_history: List[Dict[str, str]] = None):
        """Handle chat with OpenAI (existing implementation)"""
        # ... existing OpenAI implementation  
        pass
    
    def _convert_tools_to_gemini_format(self, mcp_tools) -> List[Any]:
        """Convert MCP tools to Gemini format"""
        gemini_tools = []
        
        for tool in mcp_tools:
            # Convert JSON schema to Gemini function declaration
            gemini_function = genai.protos.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        prop_name: genai.protos.Schema(
                            type=self._json_type_to_gemini_type(prop_info.get('type', 'string')),
                            description=prop_info.get('description', '')
                        )
                        for prop_name, prop_info in tool.inputSchema.get('properties', {}).items()
                    },
                    required=tool.inputSchema.get('required', [])
                )
            )
            
            gemini_tools.append(genai.protos.Tool(
                function_declarations=[gemini_function]
            ))
        
        return gemini_tools
    
    def _json_type_to_gemini_type(self, json_type: str):
        """Convert JSON schema type to Gemini type"""
        type_mapping = {
            'string': genai.protos.Type.STRING,
            'integer': genai.protos.Type.INTEGER,
            'number': genai.protos.Type.NUMBER,
            'boolean': genai.protos.Type.BOOLEAN,
            'array': genai.protos.Type.ARRAY,
            'object': genai.protos.Type.OBJECT
        }
        return type_mapping.get(json_type, genai.protos.Type.STRING)
    
    def _build_gemini_conversation(self, user_message: str, history: List[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Build conversation for Gemini"""
        conversation = []
        
        # Add system message as first user message
        conversation.append({
            'role': 'user',
            'parts': ["""You are AppPulse AI, an intelligent monitoring assistant for the AppPulse application monitoring platform.

Your role is to help developers understand their application's health and performance by analyzing real-time metrics data.

You have access to several tools for fetching current metrics:
- get_api_metrics_summary: API performance data (requests, response times, success rates)
- get_system_metrics_summary: System health data (CPU, memory, disk usage)
- get_error_analysis: Error tracking data (API errors, UI errors, error types)
- get_performance_trends: Performance trends and bottlenecks

Guidelines:
- Use the appropriate tools based on the user's question
- Call multiple tools if needed for comprehensive analysis
- Be conversational and provide actionable insights
- Use specific numbers from the metrics data
- Suggest improvements when issues are identified
- If metrics show good health, acknowledge that positively

Always base your responses on actual data from the tools."""]
        })
        
        conversation.append({
            'role': 'model',
            'parts': ["I'm AppPulse AI, ready to help you analyze your application metrics! What would you like to know about your system's health and performance?"]
        })
        
        # Add conversation history
        if history:
            for msg in history[-10:]:
                conversation.append({
                    'role': 'user' if msg['role'] == 'user' else 'model',
                    'parts': [msg['content']]
                })
        
        # Add current user message
        conversation.append({
            'role': 'user',
            'parts': [user_message]
        })
        
        return conversation
    
    def _convert_tools_to_claude_format(self, mcp_tools) -> List[Dict[str, Any]]:
        """Convert MCP tools to Claude format"""
        # ... existing Claude implementation
        pass
    
    def _convert_tools_to_openai_format(self, mcp_tools) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI format"""  
        # ... existing OpenAI implementation
        pass
    
    def _build_conversation_context(self, user_message: str, history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Build conversation context for OpenAI/Claude"""
        # ... existing implementation
        pass

# Global chat service instance
chat_service = ChatService()