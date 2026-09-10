with open('backend/main.py', 'r') as f:
    lines = f.readlines()

with open('backend/main.py', 'w') as f:
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.strip() == "":
            pass # preserve blank lines
            
        # check if it's "return {" and the previous non-empty line ends with ":"
        if line.lstrip().startswith("return {"):
            # find previous non-empty line
            prev_idx = i - 1
            while prev_idx >= 0 and lines[prev_idx].strip() == "":
                prev_idx -= 1
            if prev_idx >= 0 and lines[prev_idx].rstrip().endswith(":"):
                # indent should be prev line + 4 spaces
                prev_indent = len(lines[prev_idx]) - len(lines[prev_idx].lstrip())
                new_indent = " " * (prev_indent + 4)
                line = new_indent + line.lstrip()
        f.write(line)
        i += 1
