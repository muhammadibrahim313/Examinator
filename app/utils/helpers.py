import json
import os
from typing import List, Dict, Any, Optional

def load_exam_data(exam: str, subject: str, year: str) -> List[Dict[str, Any]]:
    """
    Load exam questions from JSON file
    """
    file_path = os.path.join('app', 'data', exam.lower(), f'{subject}-{year}.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('questions', [])
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}")
        return []
    except Exception as e:
        print(f"Error loading file {file_path}: {str(e)}")
        return []

def get_available_exams() -> List[str]:
    """
    Get list of available exams based on directory structure
    """
    data_path = os.path.join('app', 'data')
    
    if not os.path.exists(data_path):
        return []
    
    try:
        return [name for name in os.listdir(data_path) 
                if os.path.isdir(os.path.join(data_path, name))]
    except Exception as e:
        print(f"Error getting available exams: {str(e)}")
        return []

def get_available_subjects(exam: str) -> List[str]:
    """
    Get list of available subjects for a specific exam
    """
    exam_path = os.path.join('app', 'data', exam.lower())
    
    if not os.path.exists(exam_path):
        return []
    
    try:
        subjects = set()
        for filename in os.listdir(exam_path):
            if filename.endswith('.json'):
                # Extract subject from filename (format: Subject-Year.json)
                parts = filename.replace('.json', '').split('-')
                if len(parts) >= 2:
                    subject = '-'.join(parts[:-1])  # Everything except the last part (year)
                    subjects.add(subject)
        
        return sorted(list(subjects))
    except Exception as e:
        print(f"Error getting available subjects for {exam}: {str(e)}")
        return []

def get_available_years(exam: str, subject: str) -> List[str]:
    """
    Get list of available years for a specific exam and subject
    """
    exam_path = os.path.join('app', 'data', exam.lower())
    
    if not os.path.exists(exam_path):
        return []
    
    try:
        years = []
        for filename in os.listdir(exam_path):
            if filename.endswith('.json') and filename.startswith(f'{subject}-'):
                # Extract year from filename (format: Subject-Year.json)
                year = filename.replace(f'{subject}-', '').replace('.json', '')
                years.append(year)
        
        return sorted(years, reverse=True)  # Most recent first
    except Exception as e:
        print(f"Error getting available years for {exam} {subject}: {str(e)}")
        return []

def validate_phone_number(phone: str) -> bool:
    """
    Basic phone number validation
    """
    # Remove common prefixes and formatting
    cleaned = phone.replace('whatsapp:', '').replace('+', '').replace('-', '').replace(' ', '')
    
    # Check if it's all digits and reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15

def sanitize_input(text: str) -> str:
    """
    Sanitize user input
    """
    if not text:
        return ""
    
    return text.strip().lower()