from fastapi import FastAPI, File, Form, Depends
from fastapi.responses import FileResponse
import tempfile
import bpy
import glob
import os
import sys
import requests
import time
from MergeFullFbxRequestBody import MergeFullFbxRequestBody

def add_system_path_fbx_utils():
    sys.path.insert(0, os.path.join(os.getcwd(), 'fbx_utils'))

def get_temp_dir():
    dir = tempfile.TemporaryDirectory()
    try:
        yield dir.name
    finally:
        del dir

add_system_path_fbx_utils()
from fbx_utils.mergebody import main as mergebody
from fbx_utils.mergehair import main as mergehair

app = FastAPI()

def obj2fbx(avatar_path):
    avatar_list = glob.glob(avatar_path+"*.obj")

    for filename in avatar_list:

        if "detail" in filename:
            continue

        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        
        bpy.ops.import_scene.obj(filepath=filename)
        bpy.ops.export_scene.fbx(filepath=filename.replace("obj", "fbx"))

@app.post('/obj2fbx')
async def obj_to_fbx(
    dir=Depends(get_temp_dir),
    mtl : bytes = File(), obj : bytes = File(), png : bytes = File(), normal : bytes = File(), name : str = Form()
):
    mtl_dir = dir + '/{}.mtl'.format(name)
    obj_dir = dir + '/{}.obj'.format(name)
    png_dir = dir + '/{}.png'.format(name)
    normal_dir = dir + '/{}_normals.png'.format(name)
    fbx_dir = dir + '/{}.fbx'.format(name)
    for file, tdir in zip([mtl, obj, png, normal], [mtl_dir, obj_dir, png_dir, normal_dir]):
        with open(tdir, 'wb') as f:
            f.write(file)
    
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    
    try :
        bpy.ops.import_scene.obj(filepath=obj_dir)
        bpy.ops.export_scene.fbx(filepath=fbx_dir, embed_textures=True, path_mode='COPY')
        return FileResponse(fbx_dir)
    except:
        pass
    return None

@app.post('test')
async def test(mtl : bytes = File()):
    with open('./file.png', 'wb') as f:
        f.write(mtl)
        
@app.post('/merge-full-fbx')
async def merge_full_fbx(item : MergeFullFbxRequestBody, dir=Depends(get_temp_dir)):
    print(item)
    head_fbx_dir = dir + "/head.fbx"
    body_fbx_dir = dir + "/body.fbx"
    hair_fbx_dir = dir + "/hair.fbx"
    with open(head_fbx_dir, "wb") as file:
        reponse = requests.get(item.head_url)
        file.write(reponse.content)
    with open(body_fbx_dir, "wb") as file:
        response = requests.get(item.body_url)
        file.write(response.content)
    with open(hair_fbx_dir, "wb") as file:
        response = requests.get(item.hair_url)
        file.write(response.content)
    mergehair(head = head_fbx_dir, hair = hair_fbx_dir, config=item.hair_config.dict(), out=dir+"/avatar-head.fbx")
    print(os.listdir(dir))
    mergebody(head = dir+"/avatar-head.fbx", body = body_fbx_dir, config=item.body_config.dict(), out=dir+"/avatar.fbx")
    return FileResponse(dir + '/avatar.fbx')

