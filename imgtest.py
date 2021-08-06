from PIL import Image, ImageDraw
 
# Создаем белый квадрат
img = Image.new('RGBA', (1024, 1024), 'white')    
idraw = ImageDraw.Draw(img)
idraw.rectangle((10, 10, 100, 100), fill='blue')
test = Image.new('RGBA', (1280, 1024), 'black')
test.paste(img)
test.show()

"""
k = 18
x=0; y=0

for i in range(k):
    for j in range(k):
        idraw.rectangle((10, 10, 100, 100), fill='blue')
 """
#img.save('rectangle.png')