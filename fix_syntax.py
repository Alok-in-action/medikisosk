with open('backend/main.py', 'r') as f:
    content = f.read()

content = content.replace(
"""    if not user_id and (api_key or inference_key):
        
    return {""",
"""    if not user_id and (api_key or inference_key):
        return {""")

content = content.replace(
"""            callback_host = urlparse(callback_url).netloc if callback_url else None
            
            
    return {""",
"""            callback_host = urlparse(callback_url).netloc if callback_url else None
            
            return {""")

with open('backend/main.py', 'w') as f:
    f.write(content)
