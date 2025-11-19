import tkinter as tk
from tkinter import messagebox
from config import conectar
import re

def mostrar_registro(ventana_anterior=None):
    if ventana_anterior:
        ventana_anterior.destroy()

    ventana = tk.Tk()
    ventana.title("InmoValor - Registro")
    ventana.geometry("400x600")
    ventana.configure(bg="#fefcef")

    def registrar_usuario():
        nombre = entry_nombre.get()
        nombre_usuario = entry_usuario.get()
        correo = entry_correo.get()
        contraseña = entry_contraseña.get()
        confirmar = entry_confirmar.get()

        if not (nombre and nombre_usuario and correo and contraseña and confirmar):
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
            messagebox.showerror("Error", "Correo inválido.")
            return

        if contraseña != confirmar:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nombre, nombre_usuario, correo, contraseña) VALUES (%s, %s, %s, %s)",
                           (nombre, nombre_usuario, correo, contraseña))
            conn.commit()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
            from login import mostrar_login  # 👈 Importación dentro de función
            mostrar_login(ventana)
        except:
            messagebox.showerror("Error", "Correo o usuario ya registrados.")
        finally:
            conn.close()

    tk.Label(ventana, text="Registro de Usuario", font=("Arial", 20), bg="#fefcef").pack(pady=20)

    campos = [("Nombre", "nombre"), ("Usuario", "usuario"), ("Correo", "correo"), ("Contraseña", "contraseña"), ("Confirmar Contraseña", "confirmar")]
    entries = {}

    for label, var in campos:
        tk.Label(ventana, text=label + ":", bg="#fefcef").pack()
        entry = tk.Entry(ventana, show="*" if "Contraseña" in label else "")
        entry.pack()
        entries[var] = entry

    entry_nombre = entries["nombre"]
    entry_usuario = entries["usuario"]
    entry_correo = entries["correo"]
    entry_contraseña = entries["contraseña"]
    entry_confirmar = entries["confirmar"]

    tk.Button(ventana, text="Registrarse", bg="#008a8a", fg="white", command=registrar_usuario).pack(pady=10)
    tk.Button(ventana, text="Volver al Login", command=lambda: __import__('login').mostrar_login(ventana)).pack()

    ventana.mainloop()
