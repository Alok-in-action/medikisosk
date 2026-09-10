with open('backend/main.py', 'r') as f:
    lines = f.readlines()

with open('backend/main.py', 'w') as f:
    for i, line in enumerate(lines):
        if line == '    return {\n' and i + 1 < len(lines) and '"status": "error",' in lines[i+1]:
            f.write('        return {\n')
        elif line == '    return {\n' and i + 1 < len(lines) and '"message": "Bhashini User ID' in lines[i+1]:
            f.write('        return {\n')
        else:
            f.write(line)

