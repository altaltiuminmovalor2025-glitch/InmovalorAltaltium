import tkinter as tk
from tkinter import messagebox

def mostrar_home(username, ventana_anterior=None):
    if ventana_anterior:
        ventana_anterior.destroy()

    ventana = tk.Tk()
    ventana.title("InmoValor - Inicio")
    ventana.geometry("500x400")
    ventana.configure(bg="#fefcef")

    tk.Label(ventana, text=f"Bienvenido {username} a InmoValor", font=("Arial", 18), bg="#fefcef", fg="#003035").pack(pady=30)

    def cerrar_sesion():
        if messagebox.askyesno("Confirmación", "¿Estás seguro de cerrar sesión?"):
            from login import mostrar_login  # 👈 Importación diferida para evitar ciclo
            mostrar_login(ventana)

    tk.Button(ventana, text="Cerrar Sesión", bg="#52b3c0", fg="white", command=cerrar_sesion).pack(pady=20)

    ventana.mainloop()
