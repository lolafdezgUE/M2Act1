from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import requests
import base64


#DEFINICIÓN DE CLASES
#Clase para el registro de las canciones
class song(BaseModel):
    song : str
    author : str
    album : str

#Clase para el registro de los usuarios
class user(BaseModel):
    usrName : str
    name : str
    email : str
    password : str
    songs : Optional[list[song]] = None

#LISTADO DE USUARIOS REGISTRADOS
usersRegistry = []

#GENERACIÓN DE AUTENTICACIÓN CON CODIFICACIÓN BASE64
clientID = "2e930761e8384742a15e9cc12aca7c51"
clientSecret = "a76393c5c0e9443fb01a0416d54de022"
credentials = f"{clientID}:{clientSecret}"
authCodif = base64.b64encode(credentials.encode('ascii')).decode('ascii')

#API PARA LA GESTIÓN DE USUARIOS
users = FastAPI()

#Acceder al listado de usuarios registrados
@users.get("/users")
def getUsersRegistry():
    if usersRegistry == []:
        return {"message": "No hay usuarios registrados en el sistema"}
    else:
        return {"usuarios": usersRegistry}

#Acceder a la información de un usuario en concreto
@users.get("/users/{usrName}")
def getUser(usrName: str):
    for u in usersRegistry:
        if u["usrName"] == usrName:
            return {"usuario" : u}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
#Registrar un nuevo usuario
@users.post("/users/newUser")
def newUser(user : user):
    if any (u["usrName"] == user.usrName for u in usersRegistry):
        raise HTTPException(status_code=404, detail="Nombre de usuario no disponible.")
    else:
        if any (u["email"] == user.email for u in usersRegistry):
            raise HTTPException(status_code=404, detail="Ya existe una cuenta asociada a este correo.")
        else:
            new_user = {
                "usrName" : user.usrName,
                "name": user.name,
                "email" : user.email,
                "password" : user.password,
                "songs" : []
            }
            usersRegistry.append(new_user)
            return {"message": "Usuario registrado con éxito", "user": new_user}
        
#Editar la información de un usuario existente
@users.put("/users/editUser")
def editUser(user: user):
    userEdit = next((u for u in usersRegistry if u["usrName"] == user.usrName), None)
    if userEdit:
        userEmail = next((u for u in usersRegistry if u["email"] == user.email and u["usrName"] != user.usrName), None)
        if userEmail:
            raise HTTPException(status_code=404, detail="Ya existe una cuenta asociada a este correo.")
        else:
            userEdit["name"] = user.name
            userEdit["email"] = user.email
            userEdit["password"] = user.password
            return {"message": f"Usuario {user.usrName} editado con éxito", "user": userEdit}
    else:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

#Eliminar un usuario del registro
@users.delete("/users/{usrName}")
def deleteUser(usrName : str):
    userDelete = next((u for u in usersRegistry if u["usrName"] == usrName), None)
    if userDelete:
        usersRegistry.remove(userDelete)
        return {"message": f"Usuario {usrName} eliminado con éxito"}
    else:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")


#Añadir una canción a un usuario
class newSongRequest(BaseModel):
    usrName: str
    newSong: str
@users.post("/users/newSong")
def newSong(request: newSongRequest):

    url_token = "https://accounts.spotify.com/api/token"
    payload_token = 'grant_type=client_credentials'
    headers_token = {
        'Authorization': f"Basic {authCodif}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }   
    response = requests.request("POST", url_token, headers=headers_token, data=payload_token)
    token = json.loads(response.text)["access_token"]

    url_song = f"https://api.spotify.com/v1/search?q={request.newSong}&type=track&limit=1"
    headers_song = {'Authorization': f"Bearer {token}"}
    response = requests.request("GET", url_song, headers=headers_song)
    author = json.loads(response.text)["tracks"]["items"][0]["album"]["artists"][0]["name"]
    album = json.loads(response.text)["tracks"]["items"][0]["album"]["name"]
    if album == "":
        album = "No hay album. Es un single."

    new_song = {
        "song" : request.newSong,
        "author" : author,
        "album" : album
    }

    for u in usersRegistry:
        if u["usrName"] == request.usrName:
            listSongs = u["songs"]
            if any (s == new_song for s in listSongs):
                raise HTTPException(status_code=404, detail="La canción ya existe en la lista del usuario")
            else:
                listSongs.append(new_song)
            break
    return {"usuarios": usersRegistry}


