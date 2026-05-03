import re

with open('app.py', 'r') as f:
    content = f.read()

# Fix the specific python syntax error
content = content.replace('while start << text text_len:', 'while start < text_len:')

# Fix the JS syntax error
content = content.replace('<<Math Math.min', '< Math.min')

# Fix HTML tags
replacements = {
    '<<htmlhtml': '<html',
    '<<headhead': '<head',
    '<<metameta': '<meta',
    '<<titletitle': '<title',
    '<<scriptscript': '<script',
    '<<stylestyle': '<style',
    '<<bodybody': '<body',
    '<<divdiv': '<div',
    '<<hh1': '<h1',
    '<<hh2': '<h2',
    '<<hh3': '<h3',
    '<<pp ': '<p ',
    '<<labellabel': '<label',
    '<<inputinput': '<input',
    '<<buttonbutton': '<button',
    '<<spanspan': '<span'
}

for bad, good in replacements.items():
    content = content.replace(bad, good)

# Check if there are other occurrences of '<<' that are not expected
print("Remaining '<<':")
for line in content.split('\n'):
    if '<<' in line:
        print(line)

with open('app.py', 'w') as f:
    f.write(content)
print("Fixed app.py")
