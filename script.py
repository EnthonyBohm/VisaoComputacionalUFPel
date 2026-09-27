import os


def get_extension (file_name:str):
    dot_position = file_name.rfind(".")
    return file_name[dot_position:]

root_directory = os.getcwd()

# Versão inicial com listdir. 
# Não implementava diretamente suporte a diretórios.
# directory_list = [f for f in os.listdir() if not os.path.isfile(os.path.join(root_directory,f))]

directory_list = [f for f in os.scandir() if f.is_dir()]
for directory in directory_list:
    path = directory.path
    print(path)
    os.chdir(path)
    
    image_class = path[2]
    images = os.listdir()
    count = 1
    for image in images:
        ext = get_extension(image)
        new_name = f'{image_class}_{count}{ext}'
        print (f"from: {image} -> to: {new_name}")
        os.rename(image, new_name)
        count+=1


    print()
    os.chdir(root_directory)
    
