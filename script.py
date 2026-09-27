import os

root_directory = os.getcwd()

def get_extension (file_name:str):
    dot_position = file_name.rfind(".")
    return file_name[dot_position:]

def update_dir (directory_list):
    for directory in directory_list:
        path = directory.path
        print(path)
        os.chdir(path)
        
        image_class = path[2]
        images = os.listdir()
        count = 0
        for image in images:
            ext = get_extension(image)
            new_name = f'{image_class}_{count}{ext}'
            print (f"from: {image} -> to: {new_name}")
            os.rename(image, new_name)
            count+=1


        print()
        os.chdir(root_directory)


def update_files (files_list, initial_tag):
    count = 0
    for file in files_list:
        file_path = file.path
        print(file_path)
        ext = get_extension(file_path)
        new_file_name = f'{initial_tag}_c{count}{ext}'
        os.rename(file_path, new_file_name)
        count+=1


# Versão inicial com listdir. 
# Não implementava diretamente suporte a diretórios.
# directory_list = [f for f in os.listdir() if not os.path.isfile(os.path.join(root_directory,f))]

file_list = [f for f in os.scandir() if f.is_file() and get_extension(f.path) != ".py"]
directory_list = [f for f in os.scandir() if f.is_dir()]



update_files(file_list, 1)