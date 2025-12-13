# """
# Download & Convert All Datasets
# Chạy 1 lần, tự động tải về và convert!
# """

import json
import requests
from pathlib import Path
from datasets import load_dataset  # type: ignore
import time

def download_coedit():
    """Download CoEdIT Grammar Dataset"""
    print("\n📥 [1/2] Downloading CoEdIT (Grammar - 70K examples)...")
    
    dataset = load_dataset("grammarly/coedit", split="train[:10000]")  # Lấy 10K đầu (đủ dùng)
    
    grammar_data = []
    for idx, item in enumerate(dataset):
        grammar_data.append({
            "incorrect": item["src"],
            "correct": item["tgt"],
            "task": item["task"],
            "explanation": f"Grammar correction: {item['task']}"
        })
    
    # Save
    output = Path("../../data/grammar/coedit_grammar.json")  
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(grammar_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Saved {len(grammar_data)} grammar examples to {output}")
    return len(grammar_data)

def download_trivia():
    """Download OpenTriviaQA"""
    print("\n📥 [2/2] Downloading Trivia Questions (Exercises - 2.5K examples)...")
    
    exercises = []
    
    for i in range(50):  # 50 batches x 50 questions = 2500 questions
        url = f"https://opentdb.com/api.php?amount=50&type=multiple"
        try:
            response = requests.get(url)
            data = response.json()
            
            if data["response_code"] == 0:
                for item in data["results"]:
                    exercises.append({
                        "question": item["question"],
                        "correct_answer": item["correct_answer"],
                        "incorrect_answers": item["incorrect_answers"],
                        "category": item["category"],
                        "difficulty": item["difficulty"],
                        "type": item["type"]
                    })
            
            if (i + 1) % 10 == 0:
                print(f"   Downloaded {len(exercises)} questions...")
        except:
            continue
    
    # Save
    output = Path("../../data/exercise/trivia_exercises.json") 
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(exercises, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Saved {len(exercises)} exercises to {output}")
    return len(exercises)


if __name__ == "__main__":
    print("="*60)
    print("📚 DOWNLOADING ENGLISH LEARNING DATASETS")
    print("="*60)
    
    total = 0
    
    # Download all
    total += download_coedit()
    total += download_trivia()
    
    print("\n" + "="*60)
    print(f"✅ COMPLETE! Downloaded {total:,} total examples")
    print("="*60)
    print("\n📂 Files created:")
    print("   - data/grammar/coedit_grammar.json")
    print("   - data/exercise/trivia_exercises.json")
    print("\n🗑️  You can now delete:")
    print("   - data/exercise/train_exercise_dataset.json")
    print("\n🚀 Next: Restart advanced_app.py")