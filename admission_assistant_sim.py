#!/usr/bin/env python3
"""
Admission Assistant - Python Simulation
This script simulates the admission assistant system for testing purposes.
"""

import json
import pandas as pd
import re
from datetime import datetime

class AdmissionAssistant:
    def __init__(self):
        self.faq_data = self.load_faq_data()
        self.conversation_log = []
        
    def load_faq_data(self):
        """Load FAQ data from JSON file"""
        try:
            with open('../database/faq.json', 'r') as f:
                data = json.load(f)
                return data['faqs']
        except FileNotFoundError:
            print("FAQ database not found. Using basic responses.")
            return []
    
    def process_query(self, user_input):
        """Process user query and find best matching response"""
        user_input = user_input.lower().strip()
        
        # Log the conversation
        self.conversation_log.append({
            'timestamp': datetime.now().isoformat(),
            'user_query': user_input,
            'response': None
        })
        
        # Simple keyword matching
        best_match = None
        max_matches = 0
        
        for faq in self.faq_data:
            matches = 0
            for keyword in faq['keywords']:
                if keyword.lower() in user_input:
                    matches += 1
            
            if matches > max_matches:
                max_matches = matches
                best_match = faq
        
        if best_match and max_matches > 0:
            response = best_match['answer']
        else:
            response = self.get_default_response(user_input)
        
        # Update conversation log
        self.conversation_log[-1]['response'] = response
        return response
    
    def get_default_response(self, user_input):
        """Provide default responses for unmatched queries"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        
        if any(greeting in user_input for greeting in greetings):
            return "Hello! I'm your admission assistant. I can help you with information about admission requirements, deadlines, fees, application process, and required documents. What would you like to know?"
        
        return "I'm sorry, I didn't find specific information about that. Please ask about admission requirements, deadlines, application fees, application process, or required documents."
    
    def start_conversation(self):
        """Start interactive conversation"""
        print("🎓 Admission Assistant Started")
        print("=" * 50)
        print("Hello! I'm here to help with your admission queries.")
        print("You can ask about:")
        print("• Admission requirements")
        print("• Application deadlines") 
        print("• Application fees")
        print("• Application process")
        print("• Required documents")
        print("• Financial aid")
        print("\nType 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("🎤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("🔊 Assistant: Thank you for using Admission Assistant. Good luck with your application!")
                    break
                
                if not user_input:
                    print("🔊 Assistant: Please ask me something about admissions.")
                    continue
                
                response = self.process_query(user_input)
                print(f"🔊 Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
    
    def save_conversation_log(self, filename="conversation_log.json"):
        """Save conversation history"""
        with open(filename, 'w') as f:
            json.dump(self.conversation_log, f, indent=2)
        print(f"Conversation log saved to {filename}")

def main():
    assistant = AdmissionAssistant()
    assistant.start_conversation()
    
    # Save conversation log
    if assistant.conversation_log:
        assistant.save_conversation_log()

if __name__ == "__main__":
    main()
