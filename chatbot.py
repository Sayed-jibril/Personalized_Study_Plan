import json
from datetime import datetime
from typing import Optional, List, Dict
from rapidfuzz import process, fuzz  # For fuzzy matching
from textblob import TextBlob  # For spell checking
import re  # For text preprocessing

class Chatbot:
    def __init__(self, knowledge_base_file: str):
        self.knowledge_base_file = knowledge_base_file
        self.knowledge_base = self.load_knowledge_base()
        self.is_in_teach_mode = False  # Flag to track teaching mode
        self.last_question = None  # Store the last question for when teaching mode is activated

    def load_knowledge_base(self) -> List[Dict[str, str]]:
        """Load the knowledge base from a JSON file."""
        try:
            with open(self.knowledge_base_file, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            return []  # Return an empty list if the file doesn't exist

    def save_knowledge_base(self) -> None:
        """Save the current state of the knowledge base to a JSON file."""
        with open(self.knowledge_base_file, 'w') as file:
            json.dump(self.knowledge_base, file, indent=2)

    def preprocess_text(self, text: str) -> str:
        """Normalize text by lowercasing and removing punctuation."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return text

    def correct_spelling(self, text: str) -> str:
        """Correct spelling mistakes in the input text using TextBlob."""
        blob = TextBlob(text)
        return str(blob.correct())

    def find_best_match(self, user_question: str) -> Optional[str]:
        """Find the best matching question in the knowledge base using fuzzy matching."""
        questions = [q["question"] for q in self.knowledge_base]
        if not questions:
            return None

        # Preprocess the user's question
        user_question = self.preprocess_text(user_question)

        # Use fuzzy matching to find the best match
        result = process.extractOne(
            user_question,
            [self.preprocess_text(q) for q in questions],
            scorer=fuzz.token_sort_ratio  # Use token-based matching for better flexibility
        )

        # Extract the best match and score from the result
        best_match, score, _ = result  # Unpack all three values

        # Debugging: Print the best match and score
        print(f"Best match: {best_match}, Score: {score}")

        # Lower the threshold for fuzzy matching (e.g., 60%)
        if score > 60:
            return questions[[self.preprocess_text(q) for q in questions].index(best_match)]
        return None

    def get_answer_for_question(self, question: str) -> Optional[str]:
        """Retrieve the answer for a given question from the knowledge base."""
        for q in self.knowledge_base:
            if q["question"] == question:
                return q["answer"]
        return None

    def add_new_knowledge(self, question: str, answer: str) -> None:
        """Add a new question-answer pair to the knowledge base."""
        new_entry = {
            "question": question,
            "answer": answer,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.knowledge_base.append(new_entry)
        self.save_knowledge_base()
        self.print_knowledge_base()  # Debugging: Print the updated knowledge base

    def get_response(self, user_input: str) -> str:
        """Generate a response to the user's input."""
        if self.is_in_teach_mode:
            # If in teaching mode, treat the user's input as the answer
            self.add_new_knowledge(self.last_question, user_input)
            self.is_in_teach_mode = False
            self.last_question = None  # Clear the last question
            return "Thank you for teaching me! I've updated my knowledge base."

        # Correct spelling and find the best match
        corrected_input = self.correct_spelling(user_input)
        best_match = self.find_best_match(corrected_input)

        if best_match:
            return self.get_answer_for_question(best_match)
        else:
            # If no match is found, return a generic response
            self.last_question = user_input  # Store the last question for teaching mode
            return "I don't know the answer. Can you teach me?"

    def print_knowledge_base(self) -> None:
        """Print the entire knowledge base for debugging."""
        print("Knowledge Base:")
        for entry in self.knowledge_base:
            print(f"Q: {entry['question']}, A: {entry['answer']}")

    def list_knowledge_base(self) -> List[Dict[str, str]]:
        """Return the entire knowledge base."""
        return self.knowledge_base

    def clear_knowledge_base(self) -> None:
        """Clear the entire knowledge base."""
        self.knowledge_base = []
        self.save_knowledge_base()