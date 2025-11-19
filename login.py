import tkinter as tk
from tkinter import messagebox
from config import conectar
from home import mostrar_home
from register import mostrar_registro
from PIL import Image, ImageTk
import os
import re

def mostrar_login(ventana_anterior=None):
    if ventana_anterior:
        ventana_anterior.destroy()

    ventana = tk.Tk()
    ventana.title("InmoValor - Login")
    ventana.geometry("400x500")
    ventana.configure(bg="#fefcef")

    # Cargar logo
    try:
        ruta_logo = os.path.join(os.getcwd(), "assets", "logo.png")  # Ruta absoluta
        if os.path.exists(ruta_logo):
            imagen_original = Image.open(ruta_logo)
            imagen_redimensionada = imagen_original.resize((180, 60))
            logo = ImageTk.PhotoImage(imagen_redimensionada)
            label_logo = tk.Label(ventana, image=logo, bg="#fefcef")
            label_logo.image = logo  # Evita que la imagen se elimine por el recolector de basura
            label_logo.pack(pady=10)
        else:
            print("⚠️ No se encontró el archivo del logo en:", ruta_logo)
    except Exception as e:
        print("❌ Error al cargar el logo:", e)

    # Formulario
    tk.Label(ventana, text="Iniciar Sesión", font=("Arial", 20), bg="#fefcef", fg="#003035").pack(pady=20)

    tk.Label(ventana, text="Correo:", bg="#fefcef").pack()
    entry_correo = tk.Entry(ventana, width=30)
    entry_correo.pack(pady=5)

    tk.Label(ventana, text="Contraseña:", bg="#fefcef").pack()
    entry_contraseña = tk.Entry(ventana, show="*", width=30)
    entry_contraseña.pack(pady=5)

    def validar_login():
        correo = entry_correo.get()
        contraseña = entry_contraseña.get()

        if not correo or not contraseña:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
            messagebox.showerror("Error", "Correo inválido.")
            return

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre_usuario FROM usuarios WHERE correo=%s AND contraseña=%s", (correo, contraseña))
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                nombre_usuario = resultado[0]
                mostrar_home(nombre_usuario, ventana)
            else:
                messagebox.showerror("Error", "Correo o contraseña incorrectos.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{e}")

    tk.Button(ventana, text="Ingresar", bg="#00cccc", fg="white", width=20, command=validar_login).pack(pady=10)
    tk.Button(ventana, text="Registrarse", bg="#52b3c0", fg="white", width=20, command=lambda: mostrar_registro(ventana)).pack(pady=5)

    ventana.mainloop()
