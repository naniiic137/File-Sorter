import os,shutil

name_folder='ALL IN ONE'

path=os.path.dirname(__file__)
items=os.listdir(path)
folder_names=['Music','Picture','Compressed','Apps','Files','Random']

if not(os.path.exists(path+'\\'+name_folder)):
    os.mkdir(path+'\\'+name_folder)
    for x in folder_names:
        os.mkdir(path+'\\'+name_folder+'\\'+x)
    print('folder is created')
else:
    print("this folder is already here !!")


music=['m4a','mp4','mp3']
picture=['jpg','gif','png','jpeg']
compress=['zip','rar','7z','jar']
app=['exe','apk','vpk']
files=['html','txt','pdf','js','CT','log']
dont_touch=['Compressed','desktop.ini','Documents', 'Localisation', 'main.py', 'Music', 'MyFlow', 'Programs', 'Video','ALL IN ONE']

for c in items:
    if (c.rfind('.')!=-1) and c[c.rfind('.')+1:] in music:
        shutil.move(path+'\\'+c , path+'\\'+name_folder+'\\'+'Music'+'\\'+c)
    elif (c.rfind('.')!=-1) and c[c.rfind('.')+1:] in picture:
        shutil.move(path+'\\'+c , path+'\\'+name_folder+'\\'+'Picture'+'\\'+c)
    elif (c.rfind('.')!=-1) and c[c.rfind('.')+1:] in compress:
        shutil.move(path+'\\'+c , path+'\\'+name_folder+'\\'+'Compressed'+'\\'+c)
    elif (c.rfind('.')!=-1) and c[c.rfind('.')+1:] in app:
        shutil.move(path+'\\'+c , path+'\\'+name_folder+'\\'+'Apps'+'\\'+c)
    elif (c.rfind('.')!=-1) and c[c.rfind('.')+1:] in files:
        shutil.move(path+'\\'+c , path+'\\'+name_folder+'\\'+'Files'+'\\'+c)
    elif not(c in dont_touch):
        shutil.move(path+'\\'+c , path+'\\'+name_folder+'\\'+'Random'+'\\'+c)



input ()