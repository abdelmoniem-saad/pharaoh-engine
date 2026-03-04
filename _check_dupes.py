import re
from collections import Counter
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('src/utils/localization.py', 'r', encoding='utf-8') as f:
    content = f.read()

results = []
keys = re.findall(r'"(\w+)":', content)
dupes = {k: v for k, v in Counter(keys).items() if v > 2}
if dupes:
    results.append("DUPLICATES FOUND:")
    for k, v in sorted(dupes.items()):
        results.append(f"  {k}: {v} occurrences")
else:
    results.append("NO EXCESSIVE DUPLICATES")

try:
    import ast
    ast.parse(content)
    results.append("SYNTAX: OK")
except SyntaxError as e:
    results.append(f"SYNTAX ERROR: {e}")

with open('_check_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))
