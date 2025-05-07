import gradio as gr
import json
import csv
import re
import os
from datetime import datetime
import spacy
from textblob import TextBlob

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# Function to identify sentiment-related keywords
def identify_issue(message):
    # Process the message with spaCy
    doc = nlp(message.lower())
    
    # Analyze sentiment using TextBlob
    blob = TextBlob(message)
    polarity = blob.sentiment.polarity  # -1 (negative) to 1 (positive)
    
    # Determine sentiment category
    if polarity < -0.1:
        sentiment = "Negative"
    elif polarity > 0.1:
        sentiment = "Positive"
    else:
        sentiment = "Neutral"
    
    # Extract sentiment-related keywords (adjectives, adverbs, specific nouns/verbs)
    keywords = []
    for token in doc:
        # Focus on adjectives, adverbs, and sentiment-laden nouns/verbs
        if token.pos_ in ["ADJ", "ADV"] and not token.is_stop and not token.is_punct:
            keywords.append(token.text)
        # Include specific nouns/verbs that carry sentiment
        elif token.pos_ in ["NOUN", "VERB"] and not token.is_stop and not token.is_punct:
            # Common sentiment-related terms
            if token.text in ["issue", "problem", "error", "crash", "great", "awesome", "bad", "poor", "help", "fail"]:
                keywords.append(token.text)
    
    # If no keywords are found, return sentiment category alone
    if not keywords:
        return sentiment
    
    # Return unique keywords with sentiment prefix
    return f"{sentiment}: {', '.join(set(keywords))}"

# Function to parse WhatsApp chat text
def parse_whatsapp_chat(chat_text):
    messages = []
    # Regex to match WhatsApp chat format: dd/mm/yy, hh:mm am/pm - sender: message
    pattern = r'(\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}\s*(?:am|pm)) - ([^:]+): (.*?)(?=\n\d{2}/\d{2}/\d{2},|$|\n\n)'
    
    matches = re.finditer(pattern, chat_text, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        date_time = match.group(1)
        sender = match.group(2).strip()
        message = match.group(3).strip()
        
        # Skip messages that are "<Media omitted>"
        if message == "<Media omitted>":
            continue
        
        # Parse date and time
        try:
            dt = datetime.strptime(date_time, '%d/%m/%y, %I:%M %p')
            formatted_date = dt.strftime('%Y-%m-%d')
            formatted_time = dt.strftime('%H:%M:%S')
        except ValueError:
            formatted_date = date_time.split(',')[0]
            formatted_time = date_time.split(',')[1].strip()
        
        # Identify sentiment-related keywords
        issue_keywords = identify_issue(message)
        
        messages.append({
            'date': formatted_date,
            'time': formatted_time,
            'sender': sender,
            'message': message,
            'issue_related': issue_keywords
        })
    
    return messages

# Function to convert parsed messages to JSON
def messages_to_json(messages):
    return json.dumps(messages, indent=2, ensure_ascii=False)

# Function to convert parsed messages to CSV
def messages_to_csv(messages):
    output_file = "whatsapp_chat.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Time', 'Sender', 'Message', 'Issue Related'])
        writer.writeheader()
        for msg in messages:
            writer.writerow({
                'Date': msg['date'],
                'Time': msg['time'],
                'Sender': msg['sender'],
                'Message': msg['message'],
                'Issue Related': msg['issue_related']
            })
    return output_file

# Gradio function to handle file upload and processing
def process_whatsapp_chat(file):
    if not file:
        return "Please upload a WhatsApp chat text file.", "", "", None
    
    try:
        # Read the uploaded file
        with open(file.name, 'r', encoding='utf-8') as f:
            chat_text = f.read()
        
        # Parse the chat
        messages = parse_whatsapp_chat(chat_text)
        
        if not messages:
            return "No valid messages found in the chat file.", "", "", None
        
        # Convert to JSON
        json_output = messages_to_json(messages)
        
        # Convert to CSV and get file path
        csv_file = messages_to_csv(messages)
        
        # Read CSV content for display
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        return (
            f"Successfully processed {len(messages)} messages.",
            json_output,
            csv_content,
            csv_file
        )
    
    except Exception as e:
        return f"Error processing file: {str(e)}", "", "", None

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# WhatsApp Chat Analyzer")
    gr.Markdown("Upload a WhatsApp chat export (.txt) to convert it to JSON and CSV formats.")
    
    with gr.Row():
        file_input = gr.File(label="Upload WhatsApp Chat (.txt)")
    
    with gr.Row():
        process_button = gr.Button("Process Chat")
    
    with gr.Row():
        status_output = gr.Textbox(label="Status")
    
    with gr.Row():
        json_output = gr.Textbox(label="JSON Output", lines=10)
        csv_output = gr.Textbox(label="CSV Output", lines=10)
    
    with gr.Row():
        csv_download = gr.File(label="Download CSV File")
    
    process_button.click(
        fn=process_whatsapp_chat,
        inputs=file_input,
        outputs=[status_output, json_output, csv_output, csv_download]
    )

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch()
