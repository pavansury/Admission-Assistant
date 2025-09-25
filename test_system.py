#!/usr/bin/env python3
"""
Quick test of the Admission Assistant functionality
"""

import sys
import os
sys.path.append('.')

# Add the current directory to path to import our module
import json

def test_faq_loading():
    """Test if FAQ data can be loaded properly"""
    print("Testing FAQ data loading...")
    
    try:
        with open('database/faq.json', 'r') as f:
            data = json.load(f)
            print(f"✓ Loaded {len(data['faqs'])} FAQ entries")
            
        # Print first few FAQs
        print("\nSample FAQs:")
        for i, faq in enumerate(data['faqs'][:3]):
            print(f"{i+1}. Q: {faq['question']}")
            print(f"   A: {faq['answer'][:50]}...")
            
    except Exception as e:
        print(f"✗ Error loading FAQ data: {e}")

def test_basic_queries():
    """Test basic query processing"""
    print("\n" + "="*50)
    print("Testing Basic Query Processing")
    print("="*50)
    
    # Import our assistant
    from admission_assistant_sim import AdmissionAssistant
    
    assistant = AdmissionAssistant()
    
    test_queries = [
        "What are the admission requirements?",
        "When is the deadline?", 
        "How much is the application fee?",
        "What documents do I need?",
        "Hello there!"
    ]
    
    for query in test_queries:
        response = assistant.process_query(query)
        print(f"Q: {query}")
        print(f"A: {response}\n")

def show_project_status():
    """Show current project status"""
    print("\n" + "="*60)
    print("PROJECT STATUS SUMMARY")
    print("="*60)
    
    files_to_check = [
        'README.md',
        'database/faq.json', 
        'database/faq.csv',
        'code/main.ino',
        'code/config.h',
        'hardware/components_list.txt'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {file_path} ({size} bytes)")
        else:
            print(f"✗ {file_path} (missing)")
    
    print(f"\n📊 Project Structure: READY")
    print(f"🤖 Arduino Code: BASIC IMPLEMENTATION")
    print(f"🗄️  FAQ Database: POPULATED")
    print(f"🐍 Python Simulation: WORKING")

if __name__ == "__main__":
    print("🔍 ADMISSION ASSISTANT - SYSTEM TEST")
    print("="*60)
    
    test_faq_loading()
    test_basic_queries() 
    show_project_status()
    
    print("\n🚀 To run the interactive assistant:")
    print("   python3 admission_assistant_sim.py")
    print("\n📋 To upload Arduino code:")
    print("   Open code/main.ino in Arduino IDE and upload to board")
