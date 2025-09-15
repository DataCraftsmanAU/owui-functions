Add vision capabilities to reasoning models such as gpt-oss-120b!

No APIs required. Just local models.

This function creates a pipeline model which you can name and edit how you like. The model will work on multiple messages, with multiple images and you can swap between vision models and this model in the same conversation.

QuickStart:
1. Press Get below. Follow the prompts and save the function.
2. Setup a vision model and a reasoning model to use.
3. Configure the valves for the pipe, untick default for the main and ocr model ids, add your model ids and hit save.
4. Enable the function.
5. You will find a new model in your chat called "gpt-oss-20b (vision)". You can customise the model name in valves.
6. Start a conversation and ask a question with images!
 
The first model in the pipeline is a visual model that runs a text extraction query and then describes what is in the image so there is context about the text. I recommend using Mistral-Small-3.2 or Gemma 3 27b if you have the VRAM. Gemma 3 12b works too. 

The next model in the pipeline should be a reasoning model such as gpt-oss, qwen3 or deep seek. This will enable reasoning on the image data.

You can customise the following with valves:
 - Max Chars for OCR.
 - Max Chars for Description.
 - Model ID
 - Model Name
 - Toggle OCR Results (Kind of ugly, I recommend leaving off)
 - OCR System Prompt
 - OCR Multi-Image System Prompt

Limitations:
 - The image capabilities won't work in API calls. At least it didn't work in my tests with Cline.
 -  If you use this model as a base model for a custom model, the RAG query will ignore the OCR as Open WebUI runs the query before the pipeline runs. If someone knows how to get around this please message me!
