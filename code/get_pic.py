from machine import Timer
from Maix import GPIO 
from fpioa_manager import fm

import sensor, lcd
import uos,sys

def create_dir(dir,chdir='/sd'):
    try:
        if(uos.stat(dir)):
            print("PATH existed")
    except:
            uos.mkdir(dir)
# 函数整个字典读取,文件默认名字是index.txt
def read_pic_index(file_path='/sd/pic'):
    uos.chdir('/sd/pic')
    file = open('index.txt','r+',encoding='utf-8')
    index= eval(file.read())   #读取的str转换为字典
    file.close()
    return index
# 添加一个字典,第一次创建，写key=='none'
def add_pic_index(key,dict_value,file_path='/sd/pic'):
    if(key!='none' ):
        index = read_pic_index(file_path)
        file = open('index.txt',"w+",encoding='utf-8')
        index[key]=dict_value
        file.write(str(index))      #把字典转化为str
        file.close()
    else:# 第一次创建
        create_dir('pic',file_path)
        uos.chdir(file_path)
        #print(uos.getcwd())
        file = open('index.txt',"w+",encoding='utf-8')
        file.write(str(dict_value))      #把字典转化为str
        file.close()
        
# 删除一个字典
def del_pic_index(key,file_path='/sd/pic'):
    import sys
    global index   # 声明全局索引
    
    index = read_pic_index('index.txt')
    file = open('index.txt','w+')
    
    try:
        del index[str(key)]
    except KeyError:
        print('key :'+key +' have been del or without this key')   
        #file.close()
    else:
        pass
    file.write(str(index))      #把字典转化为str
    file.close()

# 打印所有的索引
def print_pic_index(file_path='sd/pic'):
    cat_index=read_pic_index('index.txt')
    for key in cat_index:
        print("key:%s value:%s"%(key,str(cat_index[key])))

# 获取key的索引
def get_pic_key_index(key,file_path='sd/pic'):
    cat_index=read_pic_index('index.txt')
    for fkey in cat_index:
        if fkey==key:
            return cat_index[key];
# 设置某一个key的index
def set_pic_key_index(key,dict_value,file_path='sd/pic'):
    add_pic_index(key,dict_value,file_path)
# 清楚所有的index
def clear_pic_index(file_path='sd/pic'):
    cat_index=read_pic_index(file_path)
    for key in cat_index:
        del_pic_index(key,file_path)


# 这里解释以下，init()创建一个索引文件，保存标签图片
# 比如，/sd/pic/index.txt中的数据就是dictx的数据，使用前需要先调用init()
# 存放图片也跟这个有关系，存放图片的路径会是，/sd/pic/sit/right或者
# /sd/pic/sit/error
# 这里有一个bug，如果原先已经创建index文件，但是由于某些原因，index并没有数据，运行就会出错
# 需要先把pic目录删除重新调用，或者调用add_pic_index('key',dictx)自己重新写入字典数据
def index_init():
    # init()执行一次就行了，之后屏蔽掉就OK
    dictx={'sit': {'right': 0, 'error': 0}, 'object': {'portable_battery': 0, 'book': 0,
                                                        'mouse': 0}}
    try:
        if uos.stat('/sd/pic'):
            print("PATH existed")
    except:
        uos.mkdir('/sd/pic')
        add_pic_index('none',dictx)
        index=read_pic_index()

# 清楚index数据
def de_index():
    index_init()
    dictx={'sit': {'right': 0, 'error': 0}, 'object': {'portable_battery': 0, 'book': 0,
                                                        'mouse': 0}}    
    add_pic_index('none',dictx)
    index=read_pic_index()
    print(index)    
    
# 初始化摄像头
def sensor_init():
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.run(1)
    sensor.skip_frames()

# 获取一帧图片
def get_frame_pic():
    img = sensor.snapshot()
    return img

# 获取获取图片计数和图片设置路径
pic_num=1
save_path=''

# 保存图片设置
def save_pic(timer):
    global pic_num
    global save_path
    img=get_frame_pic()
    lcd.display(img)
    file_name=save_path+'/'+str(pic_num)+'.jpg'
    print(file_name)
    img.save(file_name, quality=95)
    pic_num+=1


def find_object(object_list,iikey):
    for key in object_list:
        if object_list[key]==iikey:
            return 1
    return 0

#开发板上RST的按键IO
KEY=16 

# 保存图片,保存的数量，1张图片拍摄的时间间隔（ms），这里使用计时器的方式
# 参数：ikey是字典类标签，iikey是某一个标签
# 参数：num是保存图片数量，file_index_path就是标签保存途径
# 参数：interval是’period‘获取一张图片间隔,推荐300~500ms
# 参数：mode是模式，按键’key‘，模式’period‘
# 注意：使用按键的方式，interval将不再起作用
def start_obtain(ikey,iikey,file_index_path='/sd/pic/index.txt',num=100,interval=300,mode='period'):
    global pic_num
    global save_path
    print('sensor_init & lcd')
    pic_index=get_pic_key_index(ikey,file_index_path)
    print(pic_index)
    sensor_init()
    lcd.init()
    if mode=='period':
        if interval < 150:
            interval = 150
        # 配置定时器
        print('init irq')
        tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=interval, unit=Timer.UNIT_MS, callback=save_pic, arg=save_pic, start=False, priority=1, div=0)
    elif mode=='key':
        # 配置按键外部中断
        fm.register(KEY, fm.fpioa.GPIOHS0)
        key = GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_NONE)
        key.irq(save_pic, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT,1)    
    else:
        print('input mode error please input mode = period or key')
        return 0
    # 获取索引
    pic_index=get_pic_key_index(ikey,file_index_path)
    # 判断是否存在
    if find_object(pic_index,iikey):      
        print(iikey+' is not in obejct')
        return 
    print(ikey+' : ',end='')
    print(pic_index)
    
    # 根据索引的进行处理
    for pkey in pic_index:
        if iikey==pkey:
            save_path='/sd/pic/'+ikey+'/'+pkey # 保存文件目录
            print(save_path)   
            create_dir('/sd/pic/'+ikey) # 创建相应路径的文件夹
            create_dir(save_path) # 创建相应路径的文件夹
            last_num=pic_index[pkey] #获取上次已经保存到的数量
            pic_num=last_num #设置当前数量
            while(pic_num<num+last_num): # 等待获取图片信息完成
                print(save_path+' now has get pic_num %d'%(pic_num))
                if mode=='period':
                    tim.start() #启动
                # 更新索引
                print("have done = %f"%((pic_num-last_num)/num))
                pic_index[pkey]=pic_num
                set_pic_key_index(ikey,pic_index) # 更新key index
    if mode=='period':    
        tim.stop()
        tim.deinit()
    elif mode=='key':
        key.disirq() # 
        fm.unregister(KEY)
    else :
        return 0
    print(pkey +  ' have right all')

index_init()
start_obtain(ikey='object',iikey='book',file_index_path='/sd/pic/index.txt',num=500,interval=200,mode='period')