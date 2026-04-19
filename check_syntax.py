import ast, sys
with open('app.py', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
    print('app.py Syntax OK')
except SyntaxError as e:
    print(f'Syntax Error: {e}')
    sys.exit(1)
