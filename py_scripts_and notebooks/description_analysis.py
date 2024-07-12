from openai import OpenAI
import traceback
import datetime
from pandas import isnull
import os



def get_prev_dir(dir:str):
    '''Returns previous directory path relatively to dir path'''
    prev_dir = dir[:dir.rfind("\\")+1]
    return prev_dir

def load_system_promt(file_name):
    """Loads a system prompt from a file."""
    with open(file_name, 'r') as f:
        promt = f.read()
        return promt
    
def create_conversation_history(promt_file_name):
    """Creates an initial conversation history with a system prompt."""
    conversation_history = [{'role': 'system', 'content': load_system_promt(promt_file_name)}]
    return conversation_history

def create_clent():
    """Creates and returns an OpenAI client."""
    client = OpenAI()
    return client

def chat_with_gpt(client, user_input:str, conversation_history:list):
    """Sends a message to the GPT model and returns the response."""
    # Call the OpenAI API with the conversation history
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history + [{"role": "user", "content": user_input}]
    )
    
    assistant_response = response.choices[0].message.content
    return assistant_response



def parse_chat_output(output:str):
    """Parses the output from the GPT model to extract key-value pairs."""
    res = {}
    chars = '''" `' .;,!?\n\t_-+=()[]{<>/\}_-+=|\xa0\'''' # Characters to be stripped from the output
    # Check if the output contains code blocks denoted by triple backticks
    if output.count("```") == 2:
        i1 = output.find("```")
        i2 = output.find("```", i1+4)
        output = output[i1:i2] # Extract the content within the code block

    output = output.strip(chars) # Strip unwanted characters from the start and end
    # Split the output by semicolons to process each key-value pair
    for string in output.split(';'):
        key, value = string.split(":") # Split each pair by colon
        key = key.replace("plaintext\n", "").strip(chars) # Clean up the key
        value = value.strip(chars).replace("'", "").replace('"', "") # Clean up the value
        # Truncate the value if the key is 'position'
        if key == 'position':
            value = value[:30]
        res[key] = value
    # Return None if only one key-value pair is found
    # It means that the output is in an inappropriate format
    if len(res) == 1:
        return None
    return res

def get_current_date():
    """Returns the current date as a string."""
    return str(datetime.date.today())

def analyze_descriptions(df):
    """Analyzes job descriptions using the GPT model."""
    client = create_clent()
    cur_date = get_current_date()
    
    try:
        for i in df.index:
            description, position = df.loc[i, ['description', 'position']]
            if isnull(description):
                continue
            if isnull(position): # if position wasn't retrieved while scraping, then include it in promt 
                file_name = get_prev_dir(os.getcwd())+r'promts\full_promt.txt'
            else:
                # if position was retrieved while scraping, then load promt file without position included
                file_name = get_prev_dir(os.getcwd()) +r'promts\promt_without_position.txt'

            conversation_history = create_conversation_history(file_name) 
            # Sometimes ChatGPT's output is in an inappropriate format.
            # If this happens, the same prompt may be sent up to three times.
            # If ChatGPT does not generate an appropriate response after three attempts,
            # then skip this description.
            for attempt in range(3):
                output = chat_with_gpt(client, description, conversation_history)
                try:
                    res_dict = parse_chat_output(output)
                except ValueError: 
                    continue
                if not res_dict:
                    continue
                break
            keys = list(res_dict.keys())
            values = list(res_dict.values())
            df.loc[i, keys] = values
    except Exception as e: # If an error occurs, write it to exceptions_log.txt.
         with open('exceptions_log.txt', 'a') as f:
            f.write(f'analyzing_date:{cur_date}, exception:{traceback.format_exc()}\n')
            