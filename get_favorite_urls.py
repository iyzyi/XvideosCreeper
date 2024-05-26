import re, sys, os

html_path = r'favorites_2024_4_24.html'
file_path = 'xvideos_urls.txt'

with open(html_path, 'r', encoding='utf-8') as f1:
    with open(file_path, 'w', encoding='utf-8') as f2:
        for line in f1:
            url = re.search(r'https?://www.xvideos.com/video\d+?.*?(?=")', line)
            if url:
               f2.write(url.group()+'\n')
            else:
                url = re.search(r'https?://www.xvideos.com/video\.[0-9a-zA-Z]+?.*?(?=")', line)
                if url:
                    f2.write(url.group() + '\n')
                
with open(file_path, 'r', encoding='utf-8') as f2:
    print(len(f2.readlines()))

path = '\\'.join(sys.argv[0].split('\\')[:-1])
print(os.path.join(path, file_path))
