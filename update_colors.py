import os
import re

replacements = {
    r'\bbg-slate-50\b': 'bg-[var(--background)]',
    r'\bbg-white\b': 'bg-[var(--color-card)]',
    r'\bborder-slate-200\b': 'border-[var(--color-border)]',
    r'\bbg-blue-700\b': 'bg-[var(--color-primary)]',
    r'\bbg-blue-600\b': 'bg-[var(--color-primary)]',
    r'\bbg-blue-100\b': 'bg-[var(--color-primary)] opacity-20',
    r'\btext-slate-900\b': 'text-[var(--foreground)]',
    r'\btext-slate-800\b': 'text-[var(--foreground)]',
    r'\btext-slate-700\b': 'text-[var(--foreground)]',
    r'\btext-slate-600\b': 'text-[var(--foreground)]',
    r'\btext-slate-500\b': 'text-[var(--color-muted-foreground)]',
    r'\btext-slate-400\b': 'text-[var(--color-muted-foreground)]',
    r'\btext-slate-300\b': 'text-[var(--color-muted-foreground)]',
    r'\btext-blue-600\b': 'text-[var(--color-primary)]',
    r'\btext-blue-500\b': 'text-[var(--color-primary)]',
    r'\btext-gray-900\b': 'text-[var(--foreground)]',
    r'\btext-gray-700\b': 'text-[var(--foreground)]',
    r'\bbg-gray-200\b': 'bg-[var(--color-muted)]',
    r'\btext-gray-400\b': 'text-[var(--color-muted-foreground)]',
}

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in replacements.items():
        new_content = re.sub(pattern, repl, new_content)
        
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            process_file(os.path.join(root, file))

