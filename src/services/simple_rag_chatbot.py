from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent

import os
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory

load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')

GENERATION_CONFIG = {
    "temperature": 0.7,
    "max_output_tokens": 2048,
    "top_k": 40,
    "top_p": 0.95,
}

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    api_key=GEMINI_API_KEY,
    temperature=GENERATION_CONFIG["temperature"],
    max_tokens=GENERATION_CONFIG["max_output_tokens"],
    top_k=GENERATION_CONFIG["top_k"],
    top_p=GENERATION_CONFIG["top_p"],
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    }
)

@tool
def get_sensor_data(query: str = "") -> Dict[str, Any]:
    """
    Retrieve current sensor data from the smart room including temperature, humidity, and light readings.
    
    This tool provides real-time environmental data from IoT sensors in the room.
    Use this when users ask about:
    - Current temperature, humidity, or light levels
    - Room conditions or comfort analysis
    - Environmental status or sensor readings
    
    Args:
        query (str): User's specific query about sensor data (optional)
    
    Returns:
        Dict containing sensor readings with analysis and recommendations
    """
    print(f"🔍 Retrieving sensor data for query: {query}")
    
    try:
        # Get data from telemetry endpoint
        response = requests.get(f"{API_BASE_URL}/telemetry", timeout=5)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}",
                "message": "Unable to retrieve sensor data at this time"
            }
        
        data = response.json()
        
        if data.get("status") != "success":
            return {
                "success": False,
                "error": "API returned error status",
                "message": "Sensor data is currently unavailable"
            }
        
        sensor_data = data.get("data", {})
        source = data.get("source", "unknown")
        
        # Knowledge base for analysis
        knowledge_base = {
            "temperature": {
                "normal_range": (20, 25),
                "unit": "°C",
                "tips": {
                    "cold": "Consider turning on heating or closing windows",
                    "hot": "Consider turning on air conditioning or opening windows",
                    "normal": "Temperature is in the comfortable range"
                }
            },
            "humidity": {
                "normal_range": (40, 60),
                "unit": "%",
                "tips": {
                    "dry": "Consider using a humidifier or placing water bowls around",
                    "humid": "Consider using a dehumidifier or improving ventilation",
                    "normal": "Humidity is at a comfortable level"
                }
            },
            "light": {
                "normal_range": (200, 800),
                "unit": "lux",
                "tips": {
                    "dim": "Consider turning on lights or opening curtains",
                    "bright": "Consider dimming lights or closing curtains",
                    "normal": "Lighting is at a good level"
                }
            }
        }
        
        # Analyze sensor data
        analysis = {
            "readings": {},
            "recommendations": [],
            "overall_comfort": "unknown",
            "source": source,
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat())
        }
        
        comfort_score = 0
        total_metrics = 0
        
        # Analyze temperature
        if "temp" in sensor_data:
            temp_value = sensor_data["temp"]["value"]
            temp_range = knowledge_base["temperature"]["normal_range"]
            
            if temp_value < temp_range[0]:
                temp_status = "cold"
                analysis["recommendations"].append(knowledge_base["temperature"]["tips"]["cold"])
            elif temp_value > temp_range[1]:
                temp_status = "hot" 
                analysis["recommendations"].append(knowledge_base["temperature"]["tips"]["hot"])
            else:
                temp_status = "comfortable"
                analysis["recommendations"].append(knowledge_base["temperature"]["tips"]["normal"])
                comfort_score += 1
            
            analysis["readings"]["temperature"] = {
                "value": temp_value,
                "unit": "°C",
                "status": temp_status,
                "range": temp_range
            }
            total_metrics += 1
        
        # Analyze humidity
        if "humid" in sensor_data:
            humid_value = sensor_data["humid"]["value"]
            humid_range = knowledge_base["humidity"]["normal_range"]
            
            if humid_value < humid_range[0]:
                humid_status = "dry"
                analysis["recommendations"].append(knowledge_base["humidity"]["tips"]["dry"])
            elif humid_value > humid_range[1]:
                humid_status = "humid"
                analysis["recommendations"].append(knowledge_base["humidity"]["tips"]["humid"])
            else:
                humid_status = "comfortable"
                analysis["recommendations"].append(knowledge_base["humidity"]["tips"]["normal"])
                comfort_score += 1
            
            analysis["readings"]["humidity"] = {
                "value": humid_value,
                "unit": "%",
                "status": humid_status,
                "range": humid_range
            }
            total_metrics += 1
        
        # Analyze light
        if "light" in sensor_data:
            light_value = sensor_data["light"]["value"]
            light_range = knowledge_base["light"]["normal_range"]
            
            if light_value < light_range[0]:
                light_status = "dim"
                analysis["recommendations"].append(knowledge_base["light"]["tips"]["dim"])
            elif light_value > light_range[1]:
                light_status = "bright"
                analysis["recommendations"].append(knowledge_base["light"]["tips"]["bright"])
            else:
                light_status = "comfortable"
                analysis["recommendations"].append(knowledge_base["light"]["tips"]["normal"])
                comfort_score += 1
            
            analysis["readings"]["light"] = {
                "value": light_value,
                "unit": "lux",
                "status": light_status,
                "range": light_range
            }
            total_metrics += 1
        
        # Calculate overall comfort
        if total_metrics > 0:
            comfort_percentage = (comfort_score / total_metrics) * 100
            if comfort_percentage >= 80:
                analysis["overall_comfort"] = "very comfortable"
            elif comfort_percentage >= 60:
                analysis["overall_comfort"] = "comfortable"
            elif comfort_percentage >= 40:
                analysis["overall_comfort"] = "moderate"
            else:
                analysis["overall_comfort"] = "needs attention"
        
        return {
            "success": True,
            "analysis": analysis,
            "message": "Sensor data retrieved and analyzed successfully"
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "message": "Unable to connect to sensor API"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "message": "An error occurred while processing sensor data"
        }
    
@tool
def get_sensor_data_with_forecast(query: str = "") -> Dict[str, Any]:
    """
    Retrieve current sensor data and provide intelligent forecasts based on patterns and trends.
    
    This tool provides:
    - Real-time environmental data from IoT sensors
    - Intelligent forecasts for the next few hours
    - Trend analysis and predictions
    
    Use this when users ask about:
    - Current temperature, humidity, or light levels
    - Room conditions or comfort analysis
    - Environmental forecasts and predictions
    - Future trends based on current data
    
    Args:
        query (str): User's specific query about sensor data or forecasts
    
    Returns:
        Dict containing sensor readings, analysis, and forecasts
    """
    print(f"🔍 Retrieving sensor data and generating forecast for query: {query}")
    
    try:
        # Get current data from telemetry endpoint
        response = requests.get(f"{API_BASE_URL}/telemetry", timeout=5)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}",
                "message": "Unable to retrieve sensor data at this time"
            }
        
        data = response.json()
        
        if data.get("status") != "success":
            return {
                "success": False,
                "error": "API returned error status",
                "message": "Sensor data is currently unavailable"
            }
        
        sensor_data = data.get("data", {})
        source = data.get("source", "unknown")
        current_time = datetime.now()
        
        # Knowledge base for analysis and forecasting
        knowledge_base = {
            "temperature": {
                "normal_range": (20, 25),
                "unit": "°C",
                "tips": {
                    "cold": "Consider turning on heating or closing windows",
                    "hot": "Consider turning on air conditioning or opening windows",
                    "normal": "Temperature is in the comfortable range"
                }
            },
            "humidity": {
                "normal_range": (40, 60),
                "unit": "%",
                "tips": {
                    "dry": "Consider using a humidifier or placing water bowls around",
                    "humid": "Consider using a dehumidifier or improving ventilation",
                    "normal": "Humidity is at a comfortable level"
                }
            },
            "light": {
                "normal_range": (200, 800),
                "unit": "lux",
                "tips": {
                    "dim": "Consider turning on lights or opening curtains",
                    "bright": "Consider dimming lights or closing curtains",
                    "normal": "Lighting is at a good level"
                }
            }
        }
        
        # Analyze current sensor data
        analysis = {
            "readings": {},
            "recommendations": [],
            "overall_comfort": "unknown",
            "source": source,
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "forecasts": {}
        }
        
        comfort_score = 0
        total_metrics = 0
        
        # Generate intelligent forecasts based on current conditions
        def generate_forecast(sensor_type, current_value, current_hour):
            """Generate forecast based on sensor type and current conditions"""
            forecasts = []
            
            if sensor_type == "temperature":
                # Simple temperature forecasting logic
                if current_hour < 6:  # Early morning - expect warming
                    trend = "rising"
                    next_2h = min(current_value + 1.5, 26)
                    next_4h = min(current_value + 3, 28)
                    reasoning = "Early morning - expect gradual warming as day progresses"
                elif current_hour < 12:  # Morning - continued warming
                    trend = "rising"
                    next_2h = min(current_value + 1, 27)
                    next_4h = min(current_value + 2.5, 29)
                    reasoning = "Morning hours - temperature typically rises until afternoon"
                elif current_hour < 18:  # Afternoon - peak/stable
                    trend = "stable"
                    next_2h = current_value + 0.5
                    next_4h = max(current_value - 1, 18)
                    reasoning = "Afternoon peak - temperature may remain stable or start cooling"
                else:  # Evening/night - cooling
                    trend = "falling"
                    next_2h = max(current_value - 1, 18)
                    next_4h = max(current_value - 2.5, 16)
                    reasoning = "Evening/night - expect cooling as heat dissipates"
                
                return {
                    "trend": trend,
                    "next_2_hours": round(next_2h, 1),
                    "next_4_hours": round(next_4h, 1),
                    "reasoning": reasoning
                }
            
            elif sensor_type == "humidity":
                # Humidity forecasting based on temperature trends
                if current_value > 65:  # High humidity
                    trend = "falling"
                    next_2h = max(current_value - 3, 40)
                    next_4h = max(current_value - 6, 35)
                    reasoning = "High humidity tends to decrease with air circulation and heating"
                elif current_value < 35:  # Low humidity
                    trend = "rising"
                    next_2h = min(current_value + 2, 45)
                    next_4h = min(current_value + 4, 50)
                    reasoning = "Low humidity may increase with reduced heating/air circulation"
                else:  # Normal humidity
                    trend = "stable"
                    next_2h = current_value + (-1 if current_hour > 12 else 1)
                    next_4h = current_value + (-2 if current_hour > 15 else 1)
                    reasoning = "Humidity in normal range - expect minor fluctuations"
                
                return {
                    "trend": trend,
                    "next_2_hours": round(max(min(next_2h, 80), 20), 1),
                    "next_4_hours": round(max(min(next_4h, 80), 20), 1),
                    "reasoning": reasoning
                }
            
            elif sensor_type == "light":
                # Light forecasting based on time of day
                if 6 <= current_hour <= 8:  # Dawn
                    trend = "rising"
                    next_2h = min(current_value * 1.5, 900)
                    next_4h = min(current_value * 2.5, 1200)
                    reasoning = "Dawn period - natural light increasing rapidly"
                elif 9 <= current_hour <= 15:  # Day
                    trend = "stable"
                    next_2h = current_value + 50
                    next_4h = current_value + 100
                    reasoning = "Daytime - light levels remain high with minor variations"
                elif 16 <= current_hour <= 19:  # Sunset
                    trend = "falling"
                    next_2h = max(current_value * 0.7, 100)
                    next_4h = max(current_value * 0.4, 50)
                    reasoning = "Sunset period - natural light decreasing"
                else:  # Night
                    trend = "stable"
                    next_2h = max(current_value, 50)
                    next_4h = max(current_value, 30)
                    reasoning = "Nighttime - light levels depend on artificial lighting"
                
                return {
                    "trend": trend,
                    "next_2_hours": round(next_2h, 1),
                    "next_4_hours": round(next_4h, 1),
                    "reasoning": reasoning
                }
        
        current_hour = current_time.hour
        
        # Analyze temperature
        if "temp" in sensor_data:
            temp_value = sensor_data["temp"]["value"]
            temp_range = knowledge_base["temperature"]["normal_range"]
            
            if temp_value < temp_range[0]:
                temp_status = "cold"
                analysis["recommendations"].append(knowledge_base["temperature"]["tips"]["cold"])
            elif temp_value > temp_range[1]:
                temp_status = "hot" 
                analysis["recommendations"].append(knowledge_base["temperature"]["tips"]["hot"])
            else:
                temp_status = "comfortable"
                analysis["recommendations"].append(knowledge_base["temperature"]["tips"]["normal"])
                comfort_score += 1
            
            analysis["readings"]["temperature"] = {
                "value": temp_value,
                "unit": "°C",
                "status": temp_status,
                "range": temp_range
            }
            
            # Generate temperature forecast
            analysis["forecasts"]["temperature"] = generate_forecast("temperature", temp_value, current_hour)
            total_metrics += 1
        
        # Analyze humidity
        if "humid" in sensor_data:
            humid_value = sensor_data["humid"]["value"]
            humid_range = knowledge_base["humidity"]["normal_range"]
            
            if humid_value < humid_range[0]:
                humid_status = "dry"
                analysis["recommendations"].append(knowledge_base["humidity"]["tips"]["dry"])
            elif humid_value > humid_range[1]:
                humid_status = "humid"
                analysis["recommendations"].append(knowledge_base["humidity"]["tips"]["humid"])
            else:
                humid_status = "comfortable"
                analysis["recommendations"].append(knowledge_base["humidity"]["tips"]["normal"])
                comfort_score += 1
            
            analysis["readings"]["humidity"] = {
                "value": humid_value,
                "unit": "%",
                "status": humid_status,
                "range": humid_range
            }
            
            # Generate humidity forecast
            analysis["forecasts"]["humidity"] = generate_forecast("humidity", humid_value, current_hour)
            total_metrics += 1
        
        # Analyze light
        if "light" in sensor_data:
            light_value = sensor_data["light"]["value"]
            light_range = knowledge_base["light"]["normal_range"]
            
            if light_value < light_range[0]:
                light_status = "dim"
                analysis["recommendations"].append(knowledge_base["light"]["tips"]["dim"])
            elif light_value > light_range[1]:
                light_status = "bright"
                analysis["recommendations"].append(knowledge_base["light"]["tips"]["bright"])
            else:
                light_status = "comfortable"
                analysis["recommendations"].append(knowledge_base["light"]["tips"]["normal"])
                comfort_score += 1
            
            analysis["readings"]["light"] = {
                "value": light_value,
                "unit": "lux",
                "status": light_status,
                "range": light_range
            }
            
            # Generate light forecast
            analysis["forecasts"]["light"] = generate_forecast("light", light_value, current_hour)
            total_metrics += 1
        
        # Calculate overall comfort
        if total_metrics > 0:
            comfort_percentage = (comfort_score / total_metrics) * 100
            if comfort_percentage >= 80:
                analysis["overall_comfort"] = "very comfortable"
            elif comfort_percentage >= 60:
                analysis["overall_comfort"] = "comfortable"
            elif comfort_percentage >= 40:
                analysis["overall_comfort"] = "moderate"
            else:
                analysis["overall_comfort"] = "needs attention"
        
        return {
            "success": True,
            "analysis": analysis,
            "message": "Sensor data retrieved and forecast generated successfully"
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "message": "Unable to connect to sensor API"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "message": "An error occurred while processing sensor data"
        }

def create_smart_room_agent():
    """Create a ReAct-style agent for smart room assistance"""
    
    tools = [get_sensor_data, get_sensor_data_with_forecast]
    
    # Create the agent with sensor data tool
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt="""
        You are a Smart Room Assistant, an AI helper for monitoring and managing an IoT-enabled room environment.
        Your primary role is to help users understand their room's environmental conditions and provide actionable recommendations.
        
        CAPABILITIES:
        - Monitor real-time temperature, humidity, and light levels
        - Analyze room comfort and environmental conditions  
        - Provide intelligent forecasts and predictions for the next few hours
        - Provide recommendations for improving room comfort
        - Answer questions about sensor data and environmental trends
        
        INSTRUCTIONS:
        
        When users ask about environmental conditions:
        1. ALWAYS use the get_sensor_data tool to retrieve current readings
        2. Analyze the data and provide clear, actionable insights
        3. Include specific recommendations based on the sensor readings
        4. Explain what the readings mean in terms of comfort and health

        When users ask about forecasts or predictions:
        1. Use the get_sensor_data_with_forecast tool to get both current data and forecasts
        2. Present the forecast information clearly with reasoning
        3. Explain the trends and what might cause them
        4. Provide proactive recommendations based on predicted changes
        5. Make it clear these are intelligent guesses based on patterns
        
        When users ask general questions:
        1. If the question relates to room conditions, temperature, humidity, lighting, or comfort - use the sensor tool
        2. Provide helpful context about optimal environmental ranges
        3. Suggest actions they can take to improve their environment
        
        RESPONSE STYLE:
        - Be friendly, helpful, and conversational
        - Provide specific numbers and recommendations
        - Explain the "why" behind your recommendations
        - Be concise but informative
        
        IMPORTANT:
        - Always check sensor data when environmental questions are asked
        - Provide both current readings AND context about what they mean
        - Give actionable advice for improving comfort
        - Mention if data is from test/simulated sources
        - Use natural language, avoid technical jargon
        """
    )
    
    return agent

def build_smart_room_graph() -> StateGraph:
    """Build a state graph for the smart room assistant"""
    
    # Create the agent
    agent = create_smart_room_agent()
    
    # Create graph builder
    graph_builder = StateGraph(MessagesState)
    
    # Add nodes
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", ToolNode([get_sensor_data, get_sensor_data_with_forecast],))
    
    # Set entry point and edges
    graph_builder.set_entry_point("agent")
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
        {
            END: END,
            "tools": "tools"
        }
    )
    graph_builder.add_edge("tools", "agent")
    
    return graph_builder

class ChatbotPreprocessor:
    """Simple preprocessor for text input"""
    
    def __init__(self):
        pass
    
    def process_input(self, user_input):
        """Process user input - for now just text, but extensible for images"""
        if isinstance(user_input, str):
            return user_input
        elif isinstance(user_input, dict) and 'text' in user_input:
            return user_input['text']
        else:
            return str(user_input)

def initialize_smart_room_chatbot():
    """Initialize the smart room chatbot with LangGraph"""
    
    print("🏠 Initializing Smart Room Assistant...")
    
    # Build the graph
    graph_builder = build_smart_room_graph()
    
    # Create preprocessor
    preprocessor = ChatbotPreprocessor()
    
    # Add memory for conversation continuity
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
    
    print("✅ Smart Room Assistant initialized successfully!")
    
    return preprocessor, graph

class SimpleRAGChatbot:
    """LangChain-powered Smart Room Assistant"""
    
    def __init__(self):
        self.preprocessor, self.graph = initialize_smart_room_chatbot()
        self.conversation_history = []
        self.config = {
            "configurable": {
                "thread_id": "smart_room_thread",
                "user_id": "smart_room_user"
            }
        }
    
    def process_message(self, message: str) -> str:
        """Process user message using LangGraph agent"""
        try:
            # Store user message
            self.conversation_history.append({"role": "user", "content": message})
            
            # Process input
            processed_input = self.preprocessor.process_input(message)
            
            # Get response from agent
            response = self.graph.invoke(
                {"messages": [HumanMessage(content=processed_input)]},
                config=self.config
            )
            
            # Extract response message
            bot_response = response["messages"][-1].content
            
            # Store bot response
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def get_history(self):
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        # Reset the thread ID to start fresh
        self.config["configurable"]["thread_id"] = f"smart_room_thread_{datetime.now().timestamp()}"