🧰 Functions
🚀 What Are Functions?
Functions are like plugins for Open WebUI. They help you extend its capabilities—whether it’s adding support for new AI model providers like Anthropic or Vertex AI, tweaking how messages are processed, or introducing custom buttons to the interface for better usability.

Unlike external tools that may require complex integrations, Functions are built-in and run within the Open WebUI environment. That means they are fast, modular, and don’t rely on external dependencies.

Think of Functions as modular building blocks that let you enhance how the WebUI works, tailored exactly to what you need. They’re lightweight, highly customizable, and written in pure Python, so you have the freedom to create anything—from new AI-powered workflows to integrations with anything you use, like Google Search or Home Assistant.

🏗️ Types of Functions
There are three types of Functions in Open WebUI, each with a specific purpose. Let’s break them down and explain exactly what they do:

1. Pipe Function – Create Custom "Agents/Models" 
A Pipe Function is how you create custom agents/models or integrations, which then appear in the interface as if they were standalone models.

What does it do?

Pipes let you define complex workflows. For instance, you could create a Pipe that sends data to Model A and Model B, processes their outputs, and combines the results into one finalized answer.
Pipes don’t even have to use AI! They can be setups for search APIs, weather data, or even systems like Home Assistant. Basically, anything you’d like to interact with can become part of Open WebUI.
Use case example:
Imagine you want to query Google Search directly from Open WebUI. You can create a Pipe Function that:

Takes your message as the search query.
Sends the query to Google Search’s API.
Processes the response and returns it to you inside the WebUI like a normal "model" response.
When enabled, Pipe Functions show up as their own selectable model. Use Pipes whenever you need custom functionality that works like a model in the interface.

For a detailed guide, see Pipe Functions.

2. Filter Function – Modify Inputs and Outputs
A Filter Function is like a tool for tweaking data before it gets sent to the AI or after it comes back.

What does it do?
Filters act as "hooks" in the workflow and have two main parts:

Inlet: Adjust the input that is sent to the model. For example, adding additional instructions, keywords, or formatting tweaks.
Outlet: Modify the output that you receive from the model. For instance, cleaning up the response, adjusting tone, or formatting data into a specific style.
Use case example:
Suppose you’re working on a project that needs precise formatting. You can use a Filter to ensure:

Your input is always transformed into the required format.
The output from the model is cleaned up before being displayed.
Filters are linked to specific models or can be enabled for all models globally, depending on your needs.

Check out the full guide for more examples and instructions: Filter Functions.

3. Action Function – Add Custom Buttons
An Action Function is used to add custom buttons to the chat interface.

What does it do?
Actions allow you to define interactive shortcuts that trigger specific functionality directly from the chat. These buttons appear underneath individual chat messages, giving you convenient, one-click access to the actions you define.

Use case example:
Let’s say you often need to summarize long messages or generate specific outputs like translations. You can create an Action Function to:

Add a “Summarize” button under every incoming message.
When clicked, it triggers your custom function to process that message and return the summary.
Buttons provide a clean and user-friendly way to interact with extended functionality you define.

Learn how to set them up in the Action Functions Guide.

🛠️ How to Use Functions
Here's how to put Functions to work in Open WebUI:

1. Install Functions
You can install Functions via the Open WebUI interface or by importing them manually. You can find community-created functions on the Open WebUI Community Site.

⚠️ Be cautious. Only install Functions from trusted sources. Running unknown code poses security risks.

2. Enable Functions
Functions must be explicitly enabled after installation:

When you enable a Pipe Function, it becomes available as its own model in the interface.
For Filter and Action Functions, enabling them isn’t enough—you also need to assign them to specific models or enable them globally for all models.
3. Assign Filters or Actions to Models
Navigate to Workspace => Models and assign your Filter or Action to the relevant model there.
Alternatively, enable Functions for all models globally by going to Workspace => Functions, selecting the "..." menu, and toggling the Global switch.
Quick Summary
Pipes appear as standalone models you can interact with.
Filters modify inputs/outputs for smoother AI interactions.
Actions add clickable buttons to individual chat messages.
Once you’ve followed the setup process, Functions will seamlessly enhance your workflows.

✅ Why Use Functions?
Functions are designed for anyone who wants to unlock new possibilities with Open WebUI:

Extend: Add new models or integrate with non-AI tools like APIs, databases, or smart devices.
Optimize: Tweak inputs and outputs to fit your use case perfectly.
Simplify: Add buttons or shortcuts to make the interface intuitive and efficient.
Whether you’re customizing workflows for specific projects, integrating external data, or just making Open WebUI easier to use, Functions are the key to taking control of your instance.

📝 Final Notes:
Always install Functions from trusted sources only.
Make sure you understand the difference between Pipe, Filter, and Action Functions to use them effectively.
Explore the official guides:
Pipe Functions Guide
Filter Functions Guide
Action Functions Guide
By leveraging Functions, you’ll bring entirely new capabilities to your Open WebUI setup. Start experimenting today! 🚀

🚰 Pipe Function: Create Custom "Agents/Models"
Welcome to this guide on creating Pipes in Open WebUI! Think of Pipes as a way to adding a new model to Open WebUI. In this document, we'll break down what a Pipe is, how it works, and how you can create your own to add custom logic and processing to your Open WebUI models. We'll use clear metaphors and go through every detail to ensure you have a comprehensive understanding.

Introduction to Pipes
Imagine Open WebUI as a plumbing system where data flows through pipes and valves. In this analogy:

Pipes are like plugins that let you introduce new pathways for data to flow, allowing you to inject custom logic and processing.
Valves are the configurable parts of your pipe that control how data flows through it.
By creating a Pipe, you're essentially crafting a custom model with the specific behavior you want, all within the Open WebUI framework.

Understanding the Pipe Structure
Let's start with a basic, barebones version of a Pipe to understand its structure:

from pydantic import BaseModel, Field

class Pipe:
    class Valves(BaseModel):
        MODEL_ID: str = Field(default="")

    def __init__(self):
        self.valves = self.Valves()

    def pipe(self, body: dict):
        # Logic goes here
        print(self.valves, body)  # This will print the configuration options and the input body
        return "Hello, World!"


The Pipe Class
Definition: The Pipe class is where you define your custom logic.
Purpose: Acts as the blueprint for your plugin, determining how it behaves within Open WebUI.
Valves: Configuring Your Pipe
Definition: Valves is a nested class within Pipe, inheriting from BaseModel.
Purpose: It contains the configuration options (parameters) that persist across the use of your Pipe.
Example: In the above code, MODEL_ID is a configuration option with a default empty string.
Metaphor: Think of Valves as the knobs on a real-world pipe system that control the flow of water. In your Pipe, Valves allow users to adjust settings that influence how the data flows and is processed.

The __init__ Method
Definition: The constructor method for the Pipe class.
Purpose: Initializes the Pipe's state and sets up any necessary components.
Best Practice: Keep it simple; primarily initialize self.valves here.
def __init__(self):
    self.valves = self.Valves()

The pipe Function
Definition: The core function where your custom logic resides.
Parameters:
body: A dictionary containing the input data.
Purpose: Processes the input data using your custom logic and returns the result.
def pipe(self, body: dict):
    # Logic goes here
    print(self.valves, body)  # This will print the configuration options and the input body
    return "Hello, World!"


Note: Always place Valves at the top of your Pipe class, followed by __init__, and then the pipe function. This structure ensures clarity and consistency.

Creating Multiple Models with Pipes
What if you want your Pipe to create multiple models within Open WebUI? You can achieve this by defining a pipes function or variable inside your Pipe class. This setup, informally called a manifold, allows your Pipe to represent multiple models.

Here's how you can do it:

from pydantic import BaseModel, Field

class Pipe:
    class Valves(BaseModel):
        MODEL_ID: str = Field(default="")

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self):
        return [
            {"id": "model_id_1", "name": "model_1"},
            {"id": "model_id_2", "name": "model_2"},
            {"id": "model_id_3", "name": "model_3"},
        ]

    def pipe(self, body: dict):
        # Logic goes here
        print(self.valves, body)  # Prints the configuration options and the input body
        model = body.get("model", "")
        return f"{model}: Hello, World!"


Explanation
pipes Function:

Returns a list of dictionaries.
Each dictionary represents a model with unique id and name keys.
These models will show up individually in the Open WebUI model selector.
Updated pipe Function:

Processes input based on the selected model.
In this example, it includes the model name in the returned string.
Example: OpenAI Proxy Pipe
Let's dive into a practical example where we'll create a Pipe that proxies requests to the OpenAI API. This Pipe will fetch available models from OpenAI and allow users to interact with them through Open WebUI.

from pydantic import BaseModel, Field
import requests

class Pipe:
    class Valves(BaseModel):
        NAME_PREFIX: str = Field(
            default="OPENAI/",
            description="Prefix to be added before model names.",
        )
        OPENAI_API_BASE_URL: str = Field(
            default="https://api.openai.com/v1",
            description="Base URL for accessing OpenAI API endpoints.",
        )
        OPENAI_API_KEY: str = Field(
            default="",
            description="API key for authenticating requests to the OpenAI API.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self):
        if self.valves.OPENAI_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                }

                r = requests.get(
                    f"{self.valves.OPENAI_API_BASE_URL}/models", headers=headers
                )
                models = r.json()
                return [
                    {
                        "id": model["id"],
                        "name": f'{self.valves.NAME_PREFIX}{model.get("name", model["id"])}',
                    }
                    for model in models["data"]
                    if "gpt" in model["id"]
                ]

            except Exception as e:
                return [
                    {
                        "id": "error",
                        "name": "Error fetching models. Please check your API Key.",
                    },
                ]
        else:
            return [
                {
                    "id": "error",
                    "name": "API Key not provided.",
                },
            ]

    def pipe(self, body: dict, __user__: dict):
        print(f"pipe:{__name__}")
        headers = {
            "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        # Extract model id from the model name
        model_id = body["model"][body["model"].find(".") + 1 :]

        # Update the model id in the body
        payload = {**body, "model": model_id}
        try:
            r = requests.post(
                url=f"{self.valves.OPENAI_API_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
            )

            r.raise_for_status()

            if body.get("stream", False):
                return r.iter_lines()
            else:
                return r.json()
        except Exception as e:
            return f"Error: {e}"


Detailed Breakdown
Valves Configuration
NAME_PREFIX:
Adds a prefix to the model names displayed in Open WebUI.
Default: "OPENAI/".
OPENAI_API_BASE_URL:
Specifies the base URL for the OpenAI API.
Default: "https://api.openai.com/v1".
OPENAI_API_KEY:
Your OpenAI API key for authentication.
Default: "" (empty string; must be provided).
The pipes Function
Purpose: Fetches available OpenAI models and makes them accessible in Open WebUI.

Process:

Check for API Key: Ensures that an API key is provided.
Fetch Models: Makes a GET request to the OpenAI API to retrieve available models.
Filter Models: Returns models that have "gpt" in their id.
Error Handling: If there's an issue, returns an error message.
Return Format: A list of dictionaries with id and name for each model.

The pipe Function
Purpose: Handles the request to the selected OpenAI model and returns the response.

Parameters:

body: Contains the request data.
__user__: Contains user information (not used in this example but can be useful for authentication or logging).
Process:

Prepare Headers: Sets up the headers with the API key and content type.
Extract Model ID: Extracts the actual model ID from the selected model name.
Prepare Payload: Updates the body with the correct model ID.
Make API Request: Sends a POST request to the OpenAI API's chat completions endpoint.
Handle Streaming: If stream is True, returns an iterable of lines.
Error Handling: Catches exceptions and returns an error message.
Extending the Proxy Pipe
You can modify this proxy Pipe to support additional service providers like Anthropic, Perplexity, and more by adjusting the API endpoints, headers, and logic within the pipes and pipe functions.

Using Internal Open WebUI Functions
Sometimes, you may want to leverage the internal functions of Open WebUI within your Pipe. You can import these functions directly from the open_webui package. Keep in mind that while unlikely, internal functions may change for optimization purposes, so always refer to the latest documentation.

Here's how you can use internal Open WebUI functions:

from pydantic import BaseModel, Field
from fastapi import Request

from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion

class Pipe:
    def __init__(self):
        pass

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __request__: Request,
    ) -> str:
        # Use the unified endpoint with the updated signature
        user = Users.get_user_by_id(__user__["id"])
        body["model"] = "llama3.2:latest"
        return await generate_chat_completion(__request__, body, user)


Explanation
Imports:

Users from open_webui.models.users: To fetch user information.
generate_chat_completion from open_webui.utils.chat: To generate chat completions using internal logic.
Asynchronous pipe Function:

Parameters:
body: Input data for the model.
__user__: Dictionary containing user information.
__request__: The request object from FastAPI (required by generate_chat_completion).
Process:
Fetch User Object: Retrieves the user object using their ID.
Set Model: Specifies the model to be used.
Generate Completion: Calls generate_chat_completion to process the input and produce an output.
Important Notes
Function Signatures: Refer to the latest Open WebUI codebase or documentation for the most accurate function signatures and parameters.
Best Practices: Always handle exceptions and errors gracefully to ensure a smooth user experience.
Frequently Asked Questions
Q1: Why should I use Pipes in Open WebUI?
A: Pipes allow you to add new "model" with custom logic and processing to Open WebUI. It's a flexible plugin system that lets you integrate external APIs, customize model behaviors, and create innovative features without altering the core codebase.

Q2: What are Valves, and why are they important?
A: Valves are the configurable parameters of your Pipe. They function like settings or controls that determine how your Pipe operates. By adjusting Valves, you can change the behavior of your Pipe without modifying the underlying code.

Q3: Can I create a Pipe without Valves?
A: Yes, you can create a simple Pipe without defining a Valves class if your Pipe doesn't require any persistent configuration options. However, including Valves is a good practice for flexibility and future scalability.

Q4: How do I ensure my Pipe is secure when using API keys?
A: Never hard-code sensitive information like API keys into your Pipe. Instead, use Valves to input and store API keys securely. Ensure that your code handles these keys appropriately and avoids logging or exposing them.

Q5: What is the difference between the pipe and pipes functions?
A:

pipe Function: The primary function where you process the input data and generate an output. It handles the logic for a single model.

pipes Function: Allows your Pipe to represent multiple models by returning a list of model definitions. Each model will appear individually in Open WebUI.

Q6: How can I handle errors in my Pipe?
A: Use try-except blocks within your pipe and pipes functions to catch exceptions. Return meaningful error messages or handle the errors gracefully to ensure the user is informed about what went wrong.

Q7: Can I use external libraries in my Pipe?
A: Yes, you can import and use external libraries as needed. Ensure that any dependencies are properly installed and managed within your environment.

Q8: How do I test my Pipe?
A: Test your Pipe by running Open WebUI in a development environment and selecting your custom model from the interface. Validate that your Pipe behaves as expected with various inputs and configurations.

Q9: Are there any best practices for organizing my Pipe's code?
A: Yes, follow these guidelines:

Keep Valves at the top of your Pipe class.
Initialize variables in the __init__ method, primarily self.valves.
Place the pipe function after the __init__ method.
Use clear and descriptive variable names.
Comment your code for clarity.
Q10: Where can I find the latest Open WebUI documentation?
A: Visit the official Open WebUI repository or documentation site for the most up-to-date information, including function signatures, examples, and migration guides if any changes occur.

Conclusion
By now, you should have a thorough understanding of how to create and use Pipes in Open WebUI. Pipes offer a powerful way to extend and customize the capabilities of Open WebUI to suit your specific needs. Whether you're integrating external APIs, adding new models, or injecting complex logic, Pipes provide the flexibility to make it happen.

Remember to:

Use clear and consistent structure in your Pipe classes.
Leverage Valves for configurable options.
Handle errors gracefully to improve the user experience.
Consult the latest documentation for any updates or changes.
Happy coding, and enjoy extending your Open WebUI with Pipes!


🪄 Filter Function: Modify Inputs and Outputs
Welcome to the comprehensive guide on Filter Functions in Open WebUI! Filters are a flexible and powerful plugin system for modifying data before it's sent to the Large Language Model (LLM) (input) or after it’s returned from the LLM (output). Whether you’re transforming inputs for better context or cleaning up outputs for improved readability, Filter Functions let you do it all.

This guide will break down what Filters are, how they work, their structure, and everything you need to know to build powerful and user-friendly filters of your own. Let’s dig in, and don’t worry—I’ll use metaphors, examples, and tips to make everything crystal clear! 🌟

🌊 What Are Filters in Open WebUI?
Imagine Open WebUI as a stream of water flowing through pipes:

User inputs and LLM outputs are the water.
Filters are the water treatment stages that clean, modify, and adapt the water before it reaches the final destination.
Filters sit in the middle of the flow—like checkpoints—where you decide what needs to be adjusted.

Here’s a quick summary of what Filters do:

Modify User Inputs (Inlet Function): Tweak the input data before it reaches the AI model. This is where you enhance clarity, add context, sanitize text, or reformat messages to match specific requirements.
Intercept Model Outputs (Stream Function): Capture and adjust the AI’s responses as they’re generated by the model. This is useful for real-time modifications, like filtering out sensitive information or formatting the output for better readability.
Modify Model Outputs (Outlet Function): Adjust the AI's response after it’s processed, before showing it to the user. This can help refine, log, or adapt the data for a cleaner user experience.
Key Concept: Filters are not standalone models but tools that enhance or transform the data traveling to and from models.

Filters are like translators or editors in the AI workflow: you can intercept and change the conversation without interrupting the flow.

🗺️ Structure of a Filter Function: The Skeleton
Let's start with the simplest representation of a Filter Function. Don't worry if some parts feel technical at first—we’ll break it all down step by step!

🦴 Basic Skeleton of a Filter
from pydantic import BaseModel
from typing import Optional

class Filter:
    # Valves: Configuration options for the filter
    class Valves(BaseModel):  
        pass

    def __init__(self):
        # Initialize valves (optional configuration for the Filter)
        self.valves = self.Valves()

    def inlet(self, body: dict) -> dict:
        # This is where you manipulate user inputs.
        print(f"inlet called: {body}")
        return body  

    def stream(self, event: dict) -> dict:
        # This is where you modify streamed chunks of model output.
        print(f"stream event: {event}")
        return event

    def outlet(self, body: dict) -> None:
        # This is where you manipulate model outputs.
        print(f"outlet called: {body}")

🆕 🧲 Toggle Filter Example: Adding Interactivity and Icons (New in Open WebUI 0.6.10)
Filters can do more than simply modify text—they can expose UI toggles and display custom icons. For instance, you might want a filter that can be turned on/off with a user interface button, and displays a special icon in Open WebUI’s message input UI.

Here’s how you could create such a toggle filter:

from pydantic import BaseModel, Field
from typing import Optional

class Filter:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()
        self.toggle = True # IMPORTANT: This creates a switch UI in Open WebUI
        # TIP: Use SVG Data URI!
        self.icon = """data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGZpbGw9Im5vbmUiIHZpZXdCb3g9IjAgMCAyNCAyNCIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZT0iY3VycmVudENvbG9yIiBjbGFzcz0ic2l6ZS02Ij4KICA8cGF0aCBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGQ9Ik0xMiAxOHYtNS4yNW0wIDBhNi4wMSA2LjAxIDAgMCAwIDEuNS0uMTg5bS0xLjUuMTg5YTYuMDEgNi4wMSAwIDAgMS0xLjUtLjE4OW0zLjc1IDcuNDc4YTEyLjA2IDEyLjA2IDAgMCAxLTQuNSAwbTMuNzUgMi4zODNhMTQuNDA2IDE0LjQwNiAwIDAgMS0zIDBNMTQuMjUgMTh2LS4xOTJjMC0uOTgzLjY1OC0xLjgyMyAxLjUwOC0yLjMxNmE3LjUgNy41IDAgMSAwLTcuNTE3IDBjLjg1LjQ5MyAxLjUwOSAxLjMzMyAxLjUwOSAyLjMxNlYxOCIgLz4KPC9zdmc+Cg=="""
        pass

    async def inlet(
        self, body: dict, __event_emitter__, __user__: Optional[dict] = None
    ) -> dict:
        await __event_emitter__(
            {
                "type": "status",
                "data": {
                    "description": "Toggled!",
                    "done": True,
                    "hidden": False,
                },
            }
        )
        return body


🖼️ What’s happening?
toggle = True creates a switch UI in Open WebUI—users can manually enable or disable the filter in real time.
icon (with a Data URI) will show up as a little image next to the filter’s name. You can use any SVG as long as it’s Data URI encoded!
The inlet function uses the __event_emitter__ special argument to broadcast feedback/status to the UI, such as a little toast/notification that reads "Toggled!"
Toggle Filter

You can use these mechanisms to make your filters dynamic, interactive, and visually unique within Open WebUI’s plugin ecosystem.

🎯 Key Components Explained
1️⃣ Valves Class (Optional Settings)
Think of Valves as the knobs and sliders for your filter. If you want to give users configurable options to adjust your Filter’s behavior, you define those here.

class Valves(BaseModel):
    OPTION_NAME: str = "Default Value"

For example:
If you're creating a filter that converts responses into uppercase, you might allow users to configure whether every output gets totally capitalized via a valve like TRANSFORM_UPPERCASE: bool = True/False.

Configuring Valves with Dropdown Menus (Enums)
You can enhance the user experience for your filter's settings by providing dropdown menus instead of free-form text inputs for certain Valves. This is achieved using json_schema_extra with the enum keyword in your Pydantic Field definitions.

The enum keyword allows you to specify a list of predefined values that the UI should present as options in a dropdown.

Example: Creating a dropdown for color themes in a filter.

from pydantic import BaseModel, Field
from typing import Optional

# Define your available options (e.g., color themes)
COLOR_THEMES = {
    "Plain (No Color)": [],
    "Monochromatic Blue": ["blue", "RoyalBlue", "SteelBlue", "LightSteelBlue"],
    "Warm & Energetic": ["orange", "red", "magenta", "DarkOrange"],
    "Cool & Calm": ["cyan", "blue", "green", "Teal", "CadetBlue"],
    "Forest & Earth": ["green", "DarkGreen", "LimeGreen", "OliveGreen"],
    "Mystical Purple": ["purple", "DarkOrchid", "MediumPurple", "Lavender"],
    "Grayscale": ["gray", "DarkGray", "LightGray"],
    "Rainbow Fun": [
        "red",
        "orange",
        "yellow",
        "green",
        "blue",
        "indigo",
        "violet",
    ],
    "Ocean Breeze": ["blue", "cyan", "LightCyan", "DarkTurquoise"],
    "Sunset Glow": ["DarkRed", "DarkOrange", "Orange", "gold"],
    "Custom Sequence (See Code)": [],
}

class Filter:
    class Valves(BaseModel):
        selected_theme: str = Field(
            "Monochromatic Blue",
            description="Choose a predefined color theme for LLM responses. 'Plain (No Color)' disables coloring.",
            json_schema_extra={"enum": list(COLOR_THEMES.keys())}, # KEY: This creates the dropdown
        )
        custom_colors_csv: str = Field(
            "",
            description="CSV of colors for 'Custom Sequence' theme (e.g., 'red,blue,green'). Uses xcolor names.",
        )
        strip_existing_latex: bool = Field(
            True,
            description="If true, attempts to remove existing LaTeX color commands. Recommended to avoid nested rendering issues.",
        )
        colorize_type: str = Field(
            "sequential_word",
            description="How to apply colors: 'sequential_word' (word by word), 'sequential_line' (line by line), 'per_letter' (letter by letter), 'full_message' (entire message).",
            json_schema_extra={
                "enum": [
                    "sequential_word",
                    "sequential_line",
                    "per_letter",
                    "full_message",
                ]
            }, # Another example of an enum dropdown
        )
        color_cycle_reset_per_message: bool = Field(
            True,
            description="If true, the color sequence restarts for each new LLM response message. If false, it continues across messages.",
        )
        debug_logging: bool = Field(
            False,
            description="Enable verbose logging to the console for debugging filter operations.",
        )

    def __init__(self):
        self.valves = self.Valves()
        # ... rest of your __init__ logic ...


What's happening?

json_schema_extra: This argument in Field allows you to inject arbitrary JSON Schema properties that Pydantic doesn't explicitly support but can be used by downstream tools (like Open WebUI's UI renderer).
"enum": list(COLOR_THEMES.keys()): This tells Open WebUI that the selected_theme field should present a selection of values, specifically the keys from our COLOR_THEMES dictionary. The UI will then render a dropdown menu with "Plain (No Color)", "Monochromatic Blue", "Warm & Energetic", etc., as selectable options.
The colorize_type field also demonstrates another enum dropdown for different coloring methods.
Using enum for your Valves options makes your filters more user-friendly and prevents invalid inputs, leading to a smoother configuration experience.

2️⃣ inlet Function (Input Pre-Processing)
The inlet function is like prepping food before cooking. Imagine you’re a chef: before the ingredients go into the recipe (the LLM in this case), you might wash vegetables, chop onions, or season the meat. Without this step, your final dish could lack flavor, have unwashed produce, or simply be inconsistent.

In the world of Open WebUI, the inlet function does this important prep work on the user input before it’s sent to the model. It ensures the input is as clean, contextual, and helpful as possible for the AI to handle.

📥 Input:

body: The raw input from Open WebUI to the model. It is in the format of a chat-completion request (usually a dictionary that includes fields like the conversation's messages, model settings, and other metadata). Think of this as your recipe ingredients.
🚀 Your Task:
Modify and return the body. The modified version of the body is what the LLM works with, so this is your chance to bring clarity, structure, and context to the input.

🍳 Why Would You Use the inlet?
Adding Context: Automatically append crucial information to the user’s input, especially if their text is vague or incomplete. For example, you might add "You are a friendly assistant" or "Help this user troubleshoot a software bug."

Formatting Data: If the input requires a specific format, like JSON or Markdown, you can transform it before sending it to the model.

Sanitizing Input: Remove unwanted characters, strip potentially harmful or confusing symbols (like excessive whitespace or emojis), or replace sensitive information.

Streamlining User Input: If your model’s output improves with additional guidance, you can use the inlet to inject clarifying instructions automatically!

💡 Example Use Cases: Build on Food Prep
🥗 Example 1: Adding System Context
Let’s say the LLM is a chef preparing a dish for Italian cuisine, but the user hasn’t mentioned "This is for Italian cooking." You can ensure the message is clear by appending this context before sending the data to the model.

def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
    # Add system message for Italian context in the conversation
    context_message = {
        "role": "system",
        "content": "You are helping the user prepare an Italian meal."
    }
    # Insert the context at the beginning of the chat history
    body.setdefault("messages", []).insert(0, context_message)
    return body


📖 What Happens?

Any user input like "What are some good dinner ideas?" now carries the Italian theme because we’ve set the system context! Cheesecake might not show up as an answer, but pasta sure will.
🔪 Example 2: Cleaning Input (Remove Odd Characters)
Suppose the input from the user looks messy or includes unwanted symbols like !!!, making the conversation inefficient or harder for the model to parse. You can clean it up while preserving the core content.

def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
    # Clean the last user input (from the end of the 'messages' list)
    last_message = body["messages"][-1]["content"]
    body["messages"][-1]["content"] = last_message.replace("!!!", "").strip()
    return body


📖 What Happens?

Before: "How can I debug this issue!!!" ➡️ Sent to the model as "How can I debug this issue"
Note: The user feels the same, but the model processes a cleaner and easier-to-understand query.

📊 How inlet Helps Optimize Input for the LLM:
Improves accuracy by clarifying ambiguous queries.
Makes the AI more efficient by removing unnecessary noise like emojis, HTML tags, or extra punctuation.
Ensures consistency by formatting user input to match the model’s expected patterns or schemas (like, say, JSON for a specific use case).
💭 Think of inlet as the sous-chef in your kitchen—ensuring everything that goes into the model (your AI "recipe") has been prepped, cleaned, and seasoned to perfection. The better the input, the better the output!

🆕 3️⃣ stream Hook (New in Open WebUI 0.5.17)
🔄 What is the stream Hook?
The stream function is a new feature introduced in Open WebUI 0.5.17 that allows you to intercept and modify streamed model responses in real time.

Unlike outlet, which processes an entire completed response, stream operates on individual chunks as they are received from the model.

🛠️ When to Use the Stream Hook?
Modify streaming responses before they are displayed to users.
Implement real-time censorship or cleanup.
Monitor streamed data for logging/debugging.
📜 Example: Logging Streaming Chunks
Here’s how you can inspect and modify streamed LLM responses:

def stream(self, event: dict) -> dict:
    print(event)  # Print each incoming chunk for inspection
    return event

Example Streamed Events:

{"id": "chatcmpl-B4l99MMaP3QLGU5uV7BaBM0eDS0jb","choices": [{"delta": {"content": "Hi"}}]}
{"id": "chatcmpl-B4l99MMaP3QLGU5uV7BaBM0eDS0jb","choices": [{"delta": {"content": "!"}}]}
{"id": "chatcmpl-B4l99MMaP3QLGU5uV7BaBM0eDS0jb","choices": [{"delta": {"content": " 😊"}}]}


📖 What Happens?

Each line represents a small fragment of the model's streamed response.
The delta.content field contains the progressively generated text.
🔄 Example: Filtering Out Emojis from Streamed Data
def stream(self, event: dict) -> dict:
    for choice in event.get("choices", []):
        delta = choice.get("delta", {})
        if "content" in delta:
            delta["content"] = delta["content"].replace("😊", "")  # Strip emojis
    return event


📖 Before: "Hi 😊"
📖 After: "Hi"

4️⃣ outlet Function (Output Post-Processing)
The outlet function is like a proofreader: tidy up the AI's response (or make final changes) after it’s processed by the LLM.

📤 Input:

body: This contains all current messages in the chat (user history + LLM replies).
🚀 Your Task: Modify this body. You can clean, append, or log changes, but be mindful of how each adjustment impacts the user experience.

💡 Best Practices:

Prefer logging over direct edits in the outlet (e.g., for debugging or analytics).
If heavy modifications are needed (like formatting outputs), consider using the pipe function instead.
💡 Example Use Case: Strip out sensitive API responses you don't want the user to see:

def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
    for message in body["messages"]:
        message["content"] = message["content"].replace("<API_KEY>", "[REDACTED]")
    return body 


🌟 Filters in Action: Building Practical Examples
Let’s build some real-world examples to see how you’d use Filters!

📚 Example #1: Add Context to Every User Input
Want the LLM to always know it's assisting a customer in troubleshooting software bugs? You can add instructions like "You're a software troubleshooting assistant" to every user query.

class Filter:
    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        context_message = {
            "role": "system", 
            "content": "You're a software troubleshooting assistant."
        }
        body.setdefault("messages", []).insert(0, context_message)
        return body


📚 Example #2: Highlight Outputs for Easy Reading
Returning output in Markdown or another formatted style? Use the outlet function!

class Filter:
    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # Add "highlight" markdown for every response
        for message in body["messages"]:
            if message["role"] == "assistant":  # Target model response
                message["content"] = f"**{message['content']}**"  # Highlight with Markdown
        return body


🚧 Potential Confusion: Clear FAQ 🛑
Q: How Are Filters Different From Pipe Functions?
Filters modify data going to and coming from models but do not significantly interact with logic outside of these phases. Pipes, on the other hand:

Can integrate external APIs or significantly transform how the backend handles operations.
Expose custom logic as entirely new "models."
Q: Can I Do Heavy Post-Processing Inside outlet?
You can, but it’s not the best practice.:

Filters are designed to make lightweight changes or apply logging.
If heavy modifications are required, consider a Pipe Function instead.
🎉 Recap: Why Build Filter Functions?
By now, you’ve learned:

Inlet manipulates user inputs (pre-processing).
Stream intercepts and modifies streamed model outputs (real-time).
Outlet tweaks AI outputs (post-processing).
Filters are best for lightweight, real-time alterations to the data flow.
With Valves, you empower users to configure Filters dynamically for tailored behavior.
🚀 Your Turn: Start experimenting! What small tweak or context addition could elevate your Open WebUI experience? Filters are fun to build, flexible to use, and can take your models to the next level!

Happy coding! ✨



🎬 Action Function
Action functions allow you to write custom buttons that appear in the message toolbar for end users to interact with. This feature enables more interactive messaging, allowing users to grant permission before a task is performed, generate visualizations of structured data, download an audio snippet of chats, and many other use cases.

Actions are admin-managed functions that extend the chat interface with custom interactive capabilities. When a message is generated by a model that has actions configured, these actions appear as clickable buttons beneath the message.

A scaffold of Action code can be found in the community section. For more Action Function examples built by the community, visit https://openwebui.com/functions.

An example of a graph visualization Action can be seen in the video below.

Graph Visualization Action

Action Function Architecture
Actions are Python-based functions that integrate directly into the chat message toolbar. They execute server-side and can interact with users through real-time events, modify message content, and access the full Open WebUI context.

Function Structure
Actions follow a specific class structure with an action method as the main entry point:

class Action:
    def __init__(self):
        self.valves = self.Valves()
    
    class Valves(BaseModel):
        # Configuration parameters
        parameter_name: str = "default_value"
    
    async def action(self, body: dict, __user__=None, __event_emitter__=None, __event_call__=None):
        # Action implementation
        return {"content": "Modified message content"}


Action Method Parameters
The action method receives several parameters that provide access to the execution context:

body - Dictionary containing the message data and context
__user__ - Current user object with permissions and settings
__event_emitter__ - Function to send real-time updates to the frontend
__event_call__ - Function for bidirectional communication (confirmations, inputs)
__model__ - Model information that triggered the action
__request__ - FastAPI request object for accessing headers, etc.
__id__ - Action ID (useful for multi-action functions)
Event System Integration
Actions can utilize Open WebUI's real-time event system for interactive experiences:

Event Emitter (__event_emitter__)
For more information about Events and Event emitters, see here.

Send real-time updates to the frontend during action execution:

async def action(self, body: dict, __event_emitter__=None):
    # Send status updates
    await __event_emitter__({
        "type": "status", 
        "data": {"description": "Processing request..."}
    })
    
    # Send notifications
    await __event_emitter__({
        "type": "notification",
        "data": {"type": "info", "content": "Action completed successfully"}
    })


Event Call (__event_call__)
Request user input or confirmation during execution:

async def action(self, body: dict, __event_call__=None):
    # Request user confirmation
    response = await __event_call__({
        "type": "confirmation",
        "data": {
            "title": "Confirm Action",
            "message": "Are you sure you want to proceed?"
        }
    })
    
    # Request user input
    user_input = await __event_call__({
        "type": "input",
        "data": {
            "title": "Enter Value",
            "message": "Please provide additional information:",
            "placeholder": "Type your input here..."
        }
    })

Action Types and Configurations
Single Actions
Standard actions with one action method:

async def action(self, body: dict, **kwargs):
    # Single action implementation
    return {"content": "Action result"}

Multi-Actions
Functions can define multiple sub-actions through an actions array:

actions = [
    {
        "id": "summarize",
        "name": "Summarize",
        "icon_url": "data:image/svg+xml;base64,..."
    },
    {
        "id": "translate",
        "name": "Translate", 
        "icon_url": "data:image/svg+xml;base64,..."
    }
]

async def action(self, body: dict, __id__=None, **kwargs):
    if __id__ == "summarize":
        # Summarization logic
        return {"content": "Summary: ..."}
    elif __id__ == "translate":
        # Translation logic  
        return {"content": "Translation: ..."}

Global vs Model-Specific Actions
Global Actions - Turn on the toggle in the Action's settings, to globally enable it for all users and all models.
Model-Specific Actions - Configure enabled actions for specific models in the model settings.
Advanced Capabilities
Background Task Execution
For long-running operations, actions can integrate with the task system:

async def action(self, body: dict, __event_emitter__=None):
    # Start long-running process
    await __event_emitter__({
        "type": "status",
        "data": {"description": "Starting background processing..."}
    })
    
    # Perform time-consuming operation
    result = await some_long_running_function()
    
    return {"content": f"Processing completed: {result}"}

File and Media Handling
Actions can work with uploaded files and generate new media:

async def action(self, body: dict):
    message = body
    
    # Access uploaded files
    if message.get("files"):
        for file in message["files"]:
            # Process file based on type
            if file["type"] == "image":
                # Image processing logic
                pass
    
    # Return new files
    return {
        "content": "Analysis complete",
        "files": [
            {
                "type": "image",
                "url": "generated_chart.png",
                "name": "Analysis Chart"
            }
        ]
    }

User Context and Permissions
Actions can access user information and respect permissions:

async def action(self, body: dict, __user__=None):
    if __user__["role"] != "admin":
        return {"content": "This action requires admin privileges"}
    
    user_name = __user__["name"]
    return {"content": f"Hello {user_name}, admin action completed"}

Example - Specifying Action Frontmatter
Each Action function can include a docstring at the top to define metadata for the button. This helps customize the display and behavior of your Action in Open WebUI.

Example of supported frontmatter fields:

title: Display name of the Action.
author: Name of the creator.
version: Version number of the Action.
required_open_webui_version: Minimum compatible version of Open WebUI.
icon_url (optional): URL or Base64 string for a custom icon.
Base64-Encoded Example:

Example
Best Practices
Error Handling
Always implement proper error handling in your actions:

async def action(self, body: dict, __event_emitter__=None):
    try:
        # Action logic here
        result = perform_operation()
        return {"content": f"Success: {result}"}
    except Exception as e:
        await __event_emitter__({
            "type": "notification",
            "data": {"type": "error", "content": f"Action failed: {str(e)}"}
        })
        return {"content": "Action encountered an error"}


Performance Considerations
Use async/await for I/O operations
Implement timeouts for external API calls
Provide progress updates for long-running operations
Consider using background tasks for heavy processing
User Experience
Always provide clear feedback through event emitters
Use confirmation dialogs for destructive actions
Include helpful error messages
Integration with Open WebUI Features
Actions integrate seamlessly with other Open WebUI features:

Models - Actions can be model-specific or global
Tools - Actions can invoke external tools and APIs
Files - Actions can process uploaded files and generate new ones
Memory - Actions can access conversation history and context
Permissions - Actions respect user roles and access controls
For more examples and community-contributed actions, visit https://openwebui.com/functions where you can discover, download, and explore custom functions built by the Open WebUI community.


example of a good event emitter:
"""
title: Prompt Enhancer
author: Haervwe
author_url: https://github.com/Haervwe
funding_url: https://github.com/Haervwe/open-webui-tools
version: 0.6.0
important note: if you are going to sue this filter with custom pipes, do not use the show enhanced prompt valve setting
"""

import logging
import re
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Any, Optional
import json
from dataclasses import dataclass
from fastapi import Request
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.misc import get_last_user_message
from open_webui.models.models import Models
from open_webui.models.users import User
from open_webui.routers.models import get_models
from open_webui.constants import TASKS

name = "enhancer"


def setup_logger():
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.set_name(name)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger()


def remove_tagged_content(text: str) -> str:

    pattern = re.compile(
        r"<(think|thinking|reason|reasoning|thought|Thought)>.*?</\1>"
        r"|"
        r"\|begin_of_thought\|.*?\|end_of_thought\|",
        re.DOTALL,
    )

    return re.sub(pattern, "", text).strip()


class Filter:
    class Valves(BaseModel):
        user_customizable_template: str = Field(
            default="""\
You are an expert prompt engineer. Your task is to enhance the given prompt by making it more detailed, specific, and effective. Consider the context and the user's intent.

Response Format:
- Provide only the enhanced prompt.
- No additional text, markdown, or titles.
- The enhanced prompt should start immediately without any introductory phrases.

Example:
Given Prompt: Write a poem about flowers.
Enhanced Prompt: Craft a vivid and imaginative poem that explores the beauty and diversity of flowers, using rich imagery and metaphors to bring each bloom to life.

Now, enhance the following prompt:
""",
            description="Prompt to use in the Prompt enhancer System Message",
        )
        show_status: bool = Field(
            default=False,
            description="Show status indicators",
        )
        show_enhanced_prompt: bool = Field(
            default=False,
            description="Show Enahcend Prompt in chat",
        )
        model_id: Optional[str] = Field(
            default=None,
            description="Model to use for the prompt enhancement, leave empty to use the same as selected for the main response.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.__current_event_emitter__ = None
        self.__user__ = None
        self.__model__ = None
        self.__request__ = None

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
        __task__=None,
        __request__: Optional[Request] = None,
    ) -> dict:
        self.__current_event_emitter__ = __event_emitter__
        self.__request__ = __request__
        self.__model__ = __model__
        self.__user__ = User(**__user__) if isinstance(__user__, dict) else __user__
        if __task__ and __task__ != TASKS.DEFAULT:
            return body
        # Fetch available models and log their relevant details
        available_models = await get_models(self.__request__, self.__user__)
        logger.debug("Available Models (truncated image data):")
        for model in available_models:
            truncated_model = model.model_dump()  # Convert to dict for modification
            if "meta" in truncated_model:
                if isinstance(truncated_model["meta"], dict):
                    if "profile_image_url" in truncated_model["meta"]:
                        truncated_model["meta"]["profile_image_url"] = (
                            truncated_model["meta"]["profile_image_url"][:50] + "..."
                            if isinstance(
                                truncated_model["meta"]["profile_image_url"], str
                            )
                            else None
                        )
                    if "profile_image_url" in truncated_model["user"]:
                        truncated_model["user"]["profile_image_url"] = (
                            truncated_model["user"]["profile_image_url"][:50] + "..."
                            if isinstance(
                                truncated_model["user"]["profile_image_url"], str
                            )
                            else None
                        )
                else:
                    logger.warning(
                        f"Unexpected type for model.meta: {type(truncated_model['meta'])}"
                    )
            else:
                logger.warning("Model missing 'meta' key: %s", model)

            # Truncate files information
            if "knowledge" in truncated_model and isinstance(
                truncated_model["knowledge"], list
            ):
                for knowledge_item in truncated_model["knowledge"]:
                    if isinstance(knowledge_item, dict) and "files" in knowledge_item:
                        knowledge_item["files"] = "List of files (truncated)"

            logger.debug(json.dumps(truncated_model, indent=2))

        messages = body["messages"]
        user_message = get_last_user_message(messages)

        if self.valves.show_status:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Enhancing the prompt...",
                        "done": False,
                    },
                }
            )

        # Prepare context from chat history, excluding the last user message
        context_messages = [
            msg
            for msg in messages
            if msg["role"] != "user" or msg["content"] != user_message
        ]
        context = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in context_messages]
        )

        # Build context block
        context_str = f'\n\nContext:\n"""{context}"""\n\n' if context else ""

        # Construct the system prompt with clear delimiters
        system_prompt = self.valves.user_customizable_template
        user_prompt = (
            f"Context: {context_str}" f'Prompt to enhance:\n"""{user_message}"""\n\n'
        )

        # Log the system prompt before sending to LLM

        logger.debug("System Prompt: %s", system_prompt)  # Fixed string formatting

        # Determine the model to use
        # model_to_use = self.valves.model_id if self.valves.model_id else (body["model"])
        model_to_use = None
        if self.valves.model_id:
            model_to_use = self.valves.model_id
        else:
            model_to_use = body["model"]

        # Check if the selected model has "-pipe" or "pipe" in its name.
        is_pipeline_model = False
        if "-pipe" in model_to_use.lower() or "pipe" in model_to_use.lower():
            is_pipeline_model = True
            logger.warning(
                f"Selected model '{model_to_use}' appears to be a pipeline model.  Consider using the base model."
            )

        # If a pipeline model is *explicitly* chosen, use it. Otherwise, fall back to the main model.
        if not self.valves.model_id and is_pipeline_model:
            logger.warning(
                f"Pipeline model '{model_to_use}' selected without explicit model_id.  Using main model instead."
            )
            model_to_use = body["model"]  # Fallback to main model
            is_pipeline_model = False

        # Construct payload for LLM request
        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Enhance the given user prompt based on context: {user_prompt}",
                },
            ],
            "stream": False,
        }

        try:
            # Use the User object directly, as done in other scripts
            logger.debug(
                "API CALL:\n Request: %s\n Form_data: %s\n User: %s",
                str(self.__request__),
                json.dumps(payload),
                self.__user__,
            )

            response = await generate_chat_completion(
                self.__request__, payload, user=self.__user__, bypass_filter=True
            )

            message = response["choices"][0]["message"]["content"]
            enhanced_prompt = remove_tagged_content(message)
            logger.debug("Enhanced prompt: %s", enhanced_prompt)

            # Update the messages with the enhanced prompt
            messages[-1]["content"] = enhanced_prompt
            body["messages"] = messages

            if self.valves.show_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Prompt successfully enhanced.",
                            "done": True,
                        },
                    }
                )
            if self.valves.show_enhanced_prompt:
                enhanced_prompt_message = f"<details>\n<summary>Enhanced Prompt</summary>\n{enhanced_prompt}\n\n---\n\n</details>"
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {
                            "content": enhanced_prompt_message,
                        },
                    }
                )

        except ValueError as ve:
            logger.error("Value Error: %s", str(ve))
            if self.valves.show_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Error: {str(ve)}",
                            "done": True,
                        },
                    }
                )
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            if self.valves.show_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "An unexpected error occurred.",
                            "done": True,
                        },
                    }
                )

        return body

    async def outlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
        __request__: Optional[Request] = None,
    ) -> dict:
        self.__current_event_emitter__ = __event_emitter__
        self.__request__ = __request__
        self.__model__ = __model__
        self.__user__ = User(**__user__) if isinstance(__user__, dict) else __user__
        print(body)
        return body


Example rate limiter filter:
"""
title: Rate Limit Filter
author: justinh-rahb with improvements by Yanyutin753
author_url: https://github.com/justinh-rahb
funding_url: https://github.com/open-webui
version: 0.2.1
license: MIT
"""

import time
from typing import Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timedelta


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )
        requests_per_minute: Optional[int] = Field(
            default=10, description="Maximum number of requests allowed per minute."
        )
        requests_per_hour: Optional[int] = Field(
            default=50, description="Maximum number of requests allowed per hour."
        )
        sliding_window_limit: Optional[int] = Field(
            default=100,
            description="Maximum number of requests allowed within the sliding window.",
        )
        sliding_window_minutes: Optional[int] = Field(
            default=180, description="Duration of the sliding window in minutes."
        )
        global_limit: bool = Field(
            default=True,
            description="Whether to apply the limits globally to all models.",
        )
        enabled_for_admins: bool = Field(
            default=True,
            description="Whether rate limiting is enabled for admin users.",
        )

    def __init__(self):
        self.file_handler = False
        self.valves = self.Valves()
        self.user_requests = {}

    def prune_requests(self, user_id: str, model_id: str):
        now = time.time()

        if user_id not in self.user_requests:
            self.user_requests[user_id] = {}  # This remains a dict of model requests

        if self.valves.global_limit:
            # Clear all request timestamps for the user.
            self.user_requests[user_id] = {
                k: [
                    req
                    for req in v
                    if (
                        (self.valves.requests_per_minute is not None and now - req < 60)
                        or (
                            self.valves.requests_per_hour is not None
                            and now - req < 3600
                        )
                        or (now - req < self.valves.sliding_window_minutes * 60)
                    )
                ]
                for k, v in self.user_requests[user_id].items()
            }
        else:
            # Clear request timestamps for the specified model only.
            if model_id not in self.user_requests[user_id]:
                return

            self.user_requests[user_id][model_id] = [
                req
                for req in self.user_requests[user_id][model_id]
                if (
                    (self.valves.requests_per_minute is not None and now - req < 60)
                    or (self.valves.requests_per_hour is not None and now - req < 3600)
                    or (now - req < self.valves.sliding_window_minutes * 60)
                )
            ]

    def rate_limited(
        self, user_id: str, model_id: str
    ) -> Tuple[bool, Optional[int], int]:
        self.prune_requests(user_id, model_id)

        if self.valves.global_limit:
            user_reqs = self.user_requests.get(user_id, {})
            requests_last_minute = sum(
                1
                for reqs in user_reqs.values()
                for req in reqs
                if time.time() - req < 60
            )
            if requests_last_minute >= self.valves.requests_per_minute:
                earliest_request = min(
                    req
                    for reqs in user_reqs.values()
                    for req in reqs
                    if time.time() - req < 60
                )
                return (
                    True,
                    int(60 - (time.time() - earliest_request)),
                    requests_last_minute,
                )

            requests_last_hour = sum(
                1
                for reqs in user_reqs.values()
                for req in reqs
                if time.time() - req < 3600
            )
            if requests_last_hour >= self.valves.requests_per_hour:
                earliest_request = min(
                    req
                    for reqs in user_reqs.values()
                    for req in reqs
                    if time.time() - req < 3600
                )
                return (
                    True,
                    int(3600 - (time.time() - earliest_request)),
                    requests_last_hour,
                )

            sliding_window_seconds = self.valves.sliding_window_minutes * 60
            requests_in_window = sum(
                1
                for reqs in user_reqs.values()
                for req in reqs
                if time.time() - req < sliding_window_seconds
            )
            if requests_in_window >= self.valves.sliding_window_limit:
                earliest_request = min(
                    req
                    for reqs in user_reqs.values()
                    for req in reqs
                    if time.time() - req < sliding_window_seconds
                )
                return (
                    True,
                    int(sliding_window_seconds - (time.time() - earliest_request)),
                    requests_in_window,
                )

        # Process requests for a specific model.
        if (
            user_id not in self.user_requests
            or model_id not in self.user_requests[user_id]
        ):
            return False, None, 0

        user_reqs = self.user_requests[user_id][model_id]
        requests_last_minute = sum(1 for req in user_reqs if time.time() - req < 60)
        if requests_last_minute >= self.valves.requests_per_minute:
            earliest_request = min(req for req in user_reqs if time.time() - req < 60)
            return (
                True,
                int(60 - (time.time() - earliest_request)),
                requests_last_minute,
            )

        requests_last_hour = sum(1 for req in user_reqs if time.time() - req < 3600)
        if requests_last_hour >= self.valves.requests_per_hour:
            earliest_request = min(req for req in user_reqs if time.time() - req < 3600)
            return (
                True,
                int(3600 - (time.time() - earliest_request)),
                requests_last_hour,
            )

        sliding_window_seconds = self.valves.sliding_window_minutes * 60
        requests_in_window = sum(
            1 for req in user_reqs if time.time() - req < sliding_window_seconds
        )
        if requests_in_window >= self.valves.sliding_window_limit:
            earliest_request = min(
                req for req in user_reqs if time.time() - req < sliding_window_seconds
            )
            return (
                True,
                int(sliding_window_seconds - (time.time() - earliest_request)),
                requests_in_window,
            )

        return False, None, len(user_reqs)

    def log_request(self, user_id: str, model_id: str):
        if user_id not in self.user_requests:
            self.user_requests[user_id] = {}
        if model_id not in self.user_requests[user_id]:
            self.user_requests[user_id][model_id] = []
        self.user_requests[user_id][model_id].append(time.time())

    def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        print(f"inlet:{__name__}")
        print(f"inlet:body:{body}")
        print(f"inlet:user:{__user__}")

        if __user__ is not None and (
            __user__.get("role") != "admin" or self.valves.enabled_for_admins
        ):
            user_id = __user__["id"]
            model_id = __model__["id"] if __model__ is not None else "default_model"
            rate_limited, wait_time, request_count = self.rate_limited(
                user_id, model_id
            )
            if rate_limited:
                current_time = datetime.now()
                future_time = current_time + timedelta(seconds=wait_time)
                future_time_str = future_time.strftime("%I:%M %p")

                raise Exception(
                    f"Rate limit exceeded. You have made {request_count} requests to model '{model_id}'. Please try again at {future_time_str}."
                )

            self.log_request(user_id, model_id)
        return body
