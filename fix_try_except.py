import re

with open('backend/main.py', 'r') as f:
    lines = f.readlines()

with open('backend/main.py', 'w') as f:
    for i, line in enumerate(lines):
        if line == "    return {\n":
            # look ahead to see if there's an except at 4 spaces
            j = i + 1
            has_except = False
            while j < len(lines):
                if lines[j].startswith("    except ") or lines[j].startswith("        else:"):
                    has_except = True
                    break
                if lines[j].strip() == "" or lines[j].startswith("            ") or lines[j].startswith("        \"") or lines[j].startswith("        }"):
                    j += 1
                else:
                    break
            
            if has_except:
                f.write("        return {\n")
            else:
                f.write(line)
        else:
            f.write(line)
