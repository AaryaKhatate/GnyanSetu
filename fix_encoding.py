import codecs

# Try different encodings
encodings_to_try = ['utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']

content = None
used_encoding = None

for encoding in encodings_to_try:
    try:
        with codecs.open('virtual_teacher_project/UI/Dashboard/Dashboard/src/components/ProfileMenu.jsx', 'r', encoding=encoding) as f:
            content = f.read()
        used_encoding = encoding
        print(f'✅ Successfully read with encoding: {encoding}')
        break
    except:
        continue

if content:
    # Write back as clean UTF-8
    with codecs.open('virtual_teacher_project/UI/Dashboard/Dashboard/src/components/ProfileMenu.jsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ Fixed ProfileMenu.jsx encoding (converted to UTF-8)')
else:
    print('❌ Could not read file with any known encoding')
