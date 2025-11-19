from django.db.models import Avg, Count
from django.urls import reverse
from fpdf import FPDF
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import IntegrityError, connection
from django.http import Http404, JsonResponse, HttpResponse
from .models import Estados, Municipios, Colonias, CodigosPostales, AlcaldiaVistas, Propiedades, GraficaAlcaldia, Usuarios
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.cache import never_cache
import json
import matplotlib
matplotlib.use('Agg')  # Usa un backend que no requiere interfaz gráfica
import matplotlib.pyplot as plt
import os
import base64
from io import BytesIO

# Decorador para verificar si es admin
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('signin')
        usuario = Usuarios.objects.filter(id=request.session['usuario_id']).first()
        if not usuario or not (usuario.is_staff or usuario.is_superuser):
            return redirect('signin')
        return view_func(request, *args, **kwargs)
    return wrapper

# Decorador para verificar autenticación
def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('signin')
        return view_func(request, *args, **kwargs)
    return wrapper

# Registro de usuarios
@never_cache
def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html')
    else:
        if request.POST["password1"] == request.POST["password2"]:
            try:
                nuevo_usuario = Usuarios(
                    username=request.POST["username"],
                    email=request.POST["email"],
                    first_name=request.POST["nombre"],
                    last_name=request.POST.get("apellido", ""),
                    password=request.POST["password1"],  # Contraseña en texto plano
                    is_staff=0,
                    is_superuser=0,
                    is_active=1
                )
                nuevo_usuario.save()
                request.session['usuario_id'] = nuevo_usuario.id
                return redirect('welcome')
            except IntegrityError:
                return render(request, 'signup.html', {
                    "error": "El nombre de usuario o email ya existe."
                })
        return render(request, 'signup.html', {
            "error": "Las contraseñas no coinciden."
        })

# Inicio de sesión
@never_cache
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html')
    input_value = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    usuario = Usuarios.objects.filter(username=input_value, password=password, is_active=1).first()
    if usuario:
        request.session['usuario_id'] = usuario.id
        if usuario.is_staff or usuario.is_superuser:
            return redirect('gentelella_page', page='index')
        return redirect('welcome')
    return render(request, 'signin.html', {
        "error": "Usuario o contraseña incorrectos."
    })

# Cerrar sesión
@never_cache
def signout(request):
    request.session.flush()
    return redirect('signin')




# Estimaciones de propiedades
@never_cache
@login_required_custom
def estimaciones(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('signin')

    if 'generar_reporte_individual' in request.GET and 'id_propiedad' in request.GET:
        try:
            propiedad_id = request.GET['id_propiedad']
            propiedad = Propiedades.objects.get(id_propiedad=propiedad_id)

            usuario_nombre = usuario.username if usuario else "Usuario invitado"
            usuario_correo = usuario.email if usuario else "correo@invitado.com"

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_propiedad_{propiedad_id}.pdf"'

            pdf = FPDF(orientation='L')
            pdf.add_page()
            pdf.set_auto_page_break(False)

            # Encabezado
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
            if os.path.exists(logo_path):
                pdf.image(logo_path, x=120, y=10, w=40)
            pdf.set_xy(10, 10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 8, "Altaltium Real Estate Solutions", ln=True, align='L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 6, f"Usuario: {usuario_nombre}", ln=True, align='L')
            pdf.cell(100, 6, f"Correo: {usuario_correo}", ln=True, align='L')
            pdf.ln(5)

            # Valores aproximados
            pdf.set_xy(10, 40)
            pdf.set_font("Arial", '', 10)
            pdf.cell(90, 6, f"Valor Comercial Aproximado: ${propiedad.valor_comercial or 'N/A'}", ln=True, align='L')
            pdf.cell(90, 6, f"Valor Judicial Aproximado: ${propiedad.valor_judicial or 'N/A'}", ln=True, align='L')

            # Mapa
            mapa_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'mapa.png')
            if os.path.exists(mapa_path):
                pdf.image(mapa_path, x=110, y=30, w=180)

            # Título principal
            pdf.set_xy(10, 25)
            pdf.set_text_color(0, 66, 156)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Resultados de Estimación de Propiedad", ln=True, align='C')
            pdf.ln(15)

            # Descripción del Inmueble
            pdf.set_xy(10, 90)
            pdf.set_text_color(0, 66, 156)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Descripción del Inmueble", ln=True)
            pdf.ln(10)

            # Dirección
            pdf.set_xy(10, 110)
            pdf.set_text_color(0, 66, 156)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(90, 8, "Dirección", ln=True, align='L')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 10)
            pdf.set_x(10)
            pdf.cell(90, 6, "Calle:", ln=True)
            pdf.cell(90, 6, f"{propiedad.calle or 'N/A'}", ln=True)
            pdf.cell(90, 6, "Colonia:", ln=True)
            pdf.cell(90, 6, f"{propiedad.id_colonia.nombre if propiedad.id_colonia else 'Sin colonia'}", ln=True)
            pdf.cell(90, 6, "Delegación:", ln=True)
            pdf.cell(90, 6, f"{propiedad.id_municipio.nombre if propiedad.id_municipio else 'Sin municipio'}", ln=True)
            pdf.cell(90, 6, "Estado:", ln=True)
            pdf.cell(90, 6, f"{propiedad.id_estado.nombre if propiedad.id_estado else 'Sin estado'}", ln=True)

            # Características
            pdf.set_xy(110, 110)
            pdf.set_text_color(0, 66, 156)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(90, 8, "Características", ln=True, align='L')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 10)
            pdf.set_x(110)
            pdf.cell(90, 6, "Terreno:", ln=True)
            pdf.cell(90, 6, f"{propiedad.terreno or 'N/A'} m2", ln=True)
            pdf.cell(90, 6, "Construcción:", ln=True)
            pdf.cell(90, 6, f"{propiedad.construccion or 'N/A'} m2", ln=True)
            pdf.cell(90, 6, "Recámaras:", ln=True)
            pdf.cell(90, 6, f"{propiedad.recamaras or 'N/A'}", ln=True)
            pdf.cell(90, 6, "Sanitarios:", ln=True)
            pdf.cell(90, 6, f"{propiedad.sanitarios or 'N/A'}", ln=True)
            pdf.cell(90, 6, "Estacionamiento:", ln=True)
            pdf.cell(90, 6, f"{propiedad.estacionamiento or 'N/A'}", ln=True)

            # Información adicional
            pdf.set_xy(210, 110)
            pdf.set_text_color(0, 66, 156)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(90, 8, "Información adicional", ln=True, align='L')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 10)
            pdf.set_x(210)
            pdf.cell(90, 6, "Comentarios:", ln=True)
            pdf.cell(90, 6, f"{propiedad.comentarios or 'N/A'}", ln=True)
            pdf.cell(90, 6, "Estado de conservación:", ln=True)
            pdf.cell(90, 6, f"{propiedad.estado_conservacion or 'Muy bueno'}", ln=True)

            response.write(pdf.output(dest='S').encode('latin-1'))
            return response
        except Propiedades.DoesNotExist:
            return HttpResponse("Propiedad no encontrada", status=404)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)

    if request.method == 'POST':
        tipo_propiedad = request.POST.get('tipo_propiedad')
        calle = request.POST.get('calle')
        id_colonia = request.POST.get('colonia')
        id_codigo_postal = request.POST.get('cp')
        recamaras = request.POST.get('recamaras')
        sanitarios = request.POST.get('sanitarios')
        estacionamiento = request.POST.get('estacionamiento')
        terreno = request.POST.get('terreno')
        construccion = request.POST.get('construccion')
        estado_conservacion = request.POST.get('estado_conservacion')
        comentarios = request.POST.get('comentarios', '')
        id_municipio = request.POST.get('municipio')
        id_estado = request.POST.get('estado')

        campos_requeridos = [tipo_propiedad, calle, id_colonia, id_codigo_postal, terreno, id_municipio, id_estado]
        if tipo_propiedad != 'Terreno':
            campos_requeridos.extend([recamaras, sanitarios, estacionamiento, construccion, estado_conservacion])

        if not all(campos_requeridos):
            messages.error(request, "Todos los campos obligatorios deben ser llenados.")
            context = {
                'estados': Estados.objects.all(),
                'municipios': Municipios.objects.all(),
                'colonias': Colonias.objects.all(),
                'codigos_postales': CodigosPostales.objects.all(),
                'propiedades': Propiedades.objects.all(),
                'datos_alcaldia': AlcaldiaVistas.objects.all(),
                'usuario': usuario,
            }
            return render(request, 'estimaciones.html', context)

        try:
            id_colonia = int(id_colonia)
            id_codigo_postal = int(id_codigo_postal)
            id_municipio = int(id_municipio)
            id_estado = int(id_estado)
            terreno = float(terreno)

            recamaras = int(recamaras) if recamaras and tipo_propiedad != 'Terreno' else 0
            sanitarios = float(sanitarios) if sanitarios and tipo_propiedad != 'Terreno' else 0.0
            estacionamiento = int(estacionamiento) if estacionamiento and tipo_propiedad != 'Terreno' else 0
            construccion = float(construccion) if construccion and tipo_propiedad != 'Terreno' else 0.0
            estado_conservacion = estado_conservacion if estado_conservacion and tipo_propiedad != 'Terreno' else 'N/A'

            colonia = Colonias.objects.filter(id_colonia=id_colonia).first()
            if not colonia:
                messages.error(request, "Colonia no encontrada.")
                context = {
                    'estados': Estados.objects.all(),
                    'municipios': Municipios.objects.all(),
                    'colonias': Colonias.objects.all(),
                    'codigos_postales': CodigosPostales.objects.all(),
                    'propiedades': Propiedades.objects.all(),
                    'datos_alcaldia': AlcaldiaVistas.objects.all(),
                    'usuario': usuario,
                }
                return render(request, 'estimaciones.html', context)

            precio_promedio = float(colonia.promedio_precio or 0)

            if tipo_propiedad == 'Terreno':
                valor_inicial = precio_promedio * terreno
                coef = 0.16
                valor_aprox = valor_inicial * coef
                valor_comercial = valor_inicial - valor_aprox
                valor_judicial = (2 / 3) * valor_comercial
            else:
                coef_conservacion = {
                    'Muy bueno': 0.08500,
                    'Bueno': 1,
                    'Regular': 0.08500,
                    'Malo': 0.13000,
                    'Muy malo': 0.25000
                }
                valor_inicial = precio_promedio * construccion
                coef = coef_conservacion.get(estado_conservacion, 1)
                valor_aprox = valor_inicial * coef if estado_conservacion != 'Bueno' else valor_inicial
                valor_comercial = valor_inicial + valor_aprox if estado_conservacion == 'Muy bueno' else valor_inicial - valor_aprox if estado_conservacion in ['Muy malo', 'Regular', 'Malo'] else valor_aprox
                valor_judicial = (2 / 3) * valor_comercial

            propiedad = Propiedades(
                tipo_propiedad=tipo_propiedad,
                calle=calle,
                id_colonia_id=id_colonia,
                id_codigo_postal_id=id_codigo_postal,
                recamaras=recamaras,
                sanitarios=sanitarios,
                estacionamiento=estacionamiento,
                terreno=terreno,
                construccion=construccion,
                estado_conservacion=estado_conservacion,
                comentarios=comentarios,
                valor_aprox=valor_aprox,
                id_municipio_id=id_municipio,
                id_estado_id=id_estado,
                valor_judicial=valor_judicial,
                valor_comercial=valor_comercial,
                valor_inicial=valor_inicial
            )
            propiedad.save()
            messages.success(request, "Propiedad registrada y calculada exitosamente.")
            return redirect('mostrar_resultado', propiedad_id=propiedad.id_propiedad)
        except Exception as e:
            messages.error(request, f"Ocurrió un error: {str(e)}")
            context = {
                'estados': Estados.objects.all(),
                'municipios': Municipios.objects.all(),
                'colonias': Colonias.objects.all(),
                'codigos_postales': CodigosPostales.objects.all(),
                'propiedades': Propiedades.objects.all(),
                'datos_alcaldia': AlcaldiaVistas.objects.all(),
                'usuario': usuario,
            }
            return render(request, 'estimaciones.html', context)

    context = {
        'estados': Estados.objects.all(),
        'municipios': Municipios.objects.all(),
        'colonias': Colonias.objects.all(),
        'codigos_postales': CodigosPostales.objects.all(),
        'propiedades': Propiedades.objects.all(),
        'datos_alcaldia': AlcaldiaVistas.objects.all(),
        'usuario': usuario,
    }
    return render(request, 'estimaciones.html', context)


@never_cache
@login_required_custom
def mostrar_resultado(request, propiedad_id):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('signin')
    try:
        propiedad = Propiedades.objects.get(id_propiedad=propiedad_id)
        return render(request, 'resultados_estimaciones.html', {'propiedad': propiedad, 'usuario': usuario})
    except Propiedades.DoesNotExist:
        messages.error(request, "La propiedad no existe.")
        return redirect('estimaciones')

@never_cache
@login_required_custom
def analisis(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('signin')

    alcaldias = GraficaAlcaldia.objects.values('grafica_alcaldia').distinct()
    promedios = []
    labels = []

    for alcaldia in alcaldias:
        alcaldia_nombre = alcaldia['grafica_alcaldia']
        if alcaldia_nombre:
            promedio = GraficaAlcaldia.objects.filter(grafica_alcaldia=alcaldia_nombre).aggregate(promedio=Avg('grafica_promedio'))
            if promedio['promedio'] is not None:
                promedios.append(float(promedio['promedio']))
                labels.append(alcaldia_nombre)

    if not promedios:
        return render(request, 'analisis.html', {'error': 'No hay datos disponibles para las alcaldías.', 'usuario': usuario})

    plt.figure(figsize=(10, 10))
    plt.pie(promedios, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Promedio de Datos por Alcaldía')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    grafica_base64 = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()

    return render(request, 'analisis.html', {'grafica': grafica_base64, 'usuario': usuario})

# Vista welcome corregida
@never_cache
def welcome(request):
    usuario_id = request.session.get('usuario_id')
    usuario = None
    if usuario_id:
        try:
            usuario = Usuarios.objects.get(id=usuario_id, is_active=1)
        except Usuarios.DoesNotExist:
            request.session.flush()  # Limpiar sesión si el usuario no existe o no está activo
    
    images_auth = ["casa5.png", "casa6.png", "casa1.png", "casa2.png", "casa3.png", "casa4.png"]
    images_guest = ["Altatium.png", "forbes.png"]
    
    context = {
        "usuario": usuario,
        "images_auth": images_auth,
        "images_guest": images_guest,
    }
    return render(request, "welcome.html", context)

# Vistas de alcaldías

                                            #BENITO JUAREZ
@never_cache
@login_required_custom
def vista_benito_juarez(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Benito Juárez')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Benito Juárez.")
            print("No se encontraron colonias para Benito Juárez.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Benito Juárez.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/benito.html', context)


                                            #ALVARO ABREGON 
@never_cache
@login_required_custom
def vista_alvaro(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Álvaro Obregón')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Álvaro Obregón.")
            print("No se encontraron colonias para Álvaro Obregón.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Álvaro Obregón.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/alvaro.html', context)


                                            #Coyoacán
@never_cache
@login_required_custom
def vista_coyoacan(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Coyoacán')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Coyoacán.")
            print("No se encontraron colonias para Coyoacán.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Coyoacán.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/coyoacan.html', context)

                                                #Xochimilco
@never_cache
@login_required_custom
def vista_xochimilco(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Xochimilco')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Xochimilco.")
            print("No se encontraron colonias para Xochimilcon.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles paraXochimilco.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/xochimilco.html', context)

                                        #Azcapotzalco
@never_cache
@login_required_custom
def vista_azcapotzalco(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Azcapotzalco')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Azcapotzalco.")
            print("No se encontraron colonias para Azcapotzalco.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Azcapotzalco.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/azcapotzalco.html', context)

                                            #Cuajimalpa de Morelos
@never_cache
@login_required_custom
def vista_cuajimalpa(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Cuajimalpa De Morelos')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Cuajimalpa de Morelos.")
            print("No se encontraron colonias para Cuajimalpa de Morelos.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Cuajimalpa de Morelos.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/cuajimalpa.html', context)

                                                    #Cuauhtémoc
@never_cache
@login_required_custom
def vista_cuauhtemoc(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Cuauhtémoc')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Cuauhtémoc.")
            print("No se encontraron colonias para Cuauhtémoc.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Cuauhtémoc.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/cuauhtemoc.html', context)

                                            #Miguel Hidalgo
@never_cache
@login_required_custom
def vista_miguel(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Miguel Hidalgo')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Miguel Hidalgo.")
            print("No se encontraron colonias para Miguel Hidalgo.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Miguel Hidalgo.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/miguel.html', context)

                                            #Gustavo A. Madero  
@never_cache
@login_required_custom
def vista_gustavo(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Gustavo A. Madero')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Gustavo A. Madero.")
            print("No se encontraron colonias para Gustavo A. Madero.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Gustavo A. Madero.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/gustavo.html', context)

                                            #Iztacalco
@never_cache
@login_required_custom
def vista_iztacalco(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Iztacalco')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Iztacalco.")
            print("No se encontraron colonias para Iztacalco.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Iztacalco.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/iztacalco.html', context)

                                                #Iztapalapa
@never_cache
@login_required_custom
def vista_iztapalapa(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Iztapalapa')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Iztapalapa.")
            print("No se encontraron colonias para Iztapalapa.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Iztapalapa.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/iztapalapa.html', context)

                                            #La Magdalena Contreras
@never_cache
@login_required_custom
def vista_magda(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='La Magdalena Contreras')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para La Magdalena Contreras.")
            print("No se encontraron colonias para La Magdalena Contreras.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para La Magdalena Contreras.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/magda.html', context)


                                            #Milpa Alta
@never_cache
@login_required_custom
def vista_milpa(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Milpa Alta')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Milpa Alta.")
            print("No se encontraron colonias para Milpa Alta.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Milpa Alta.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/milpa.html', context)
                    
                                            #Tláhuac
@never_cache
@login_required_custom
def vista_tlahuac(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Tláhuac')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Tláhuac.")
            print("No se encontraron colonias para Tláhuac.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Tláhuac.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/tlahuac.html', context)

                                                #Tlalpan 
@never_cache
@login_required_custom
def vista_tlalpan(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Tlalpan')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Tlalpan.")
            print("No se encontraron colonias para Tlalpan.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Tlalpan.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/tlalpan.html', context)

                                                  #Venustiano Carranza
@never_cache
@login_required_custom
def vista_venustiano(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        messages.error(request, "Debes iniciar sesión para ver esta página.")
        return redirect('signin')
    
    try:
        datos = Colonias.objects.select_related('id_municipio', 'id_estado').filter(id_municipio__nombre__iexact='Venustiano Carranza')
        if not datos.exists():
            messages.warning(request, "No se encontraron colonias para Venustiano Carranza.")
            print("No se encontraron colonias para Venustiano Carranza.")
        else:
            print(f"Colonias encontradas: {list(datos.values('id_colonia', 'nombre', 'promedio_precio', 'zona', 'id_estado__nombre', 'id_municipio__nombre'))}")
    except Exception as e:
        datos = Colonias.objects.none()
        messages.error(request, f"Error al cargar datos: {str(e)}")
        print(f"Error: {str(e)}")
    
    context = {
        'datos': datos,
        'usuario': usuario,
        'no_data_message': 'No hay datos disponibles para Venustiano Carranza.' if not datos.exists() else None
    }
    return render(request, 'alcaldias/venustiano.html', context)


# Obtener municipios por estado (AJAX)
@never_cache
def obtener_municipios(request):
    estado_id = request.GET.get('estado_id')
    if not estado_id:
        return JsonResponse({'error': 'ID de estado no proporcionado'}, status=400)
    try:
        municipios = Municipios.objects.filter(id_estado=estado_id).values('id_municipio', 'nombre')
        return JsonResponse(list(municipios), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Obtener colonias por municipio (AJAX)
@never_cache
def obtener_colonias(request):
    municipio_id = request.GET.get('municipio_id')
    if not municipio_id:
        return JsonResponse({'error': 'ID de municipio no proporcionado'}, status=400)
    try:
        colonias = Colonias.objects.filter(id_municipio=municipio_id).values('id_colonia', 'nombre')
        return JsonResponse(list(colonias), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Obtener códigos postales por colonia (AJAX)
@never_cache
def obtener_codigos_postales(request):
    colonia_id = request.GET.get('colonia_id')
    if not colonia_id:
        return JsonResponse({'error': 'ID de colonia no proporcionado'}, status=400)
    try:
        codigos_postales = CodigosPostales.objects.filter(id_colonia=colonia_id).values('id_codigo_postal', 'codigo')
        return JsonResponse(list(codigos_postales), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Vista principal para panel admin
@never_cache
@admin_required
def gentelella_view(request, page):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('signin')
    context = {'usuario': usuario}

    if page == "cal_colonia":
        colonias = Colonias.objects.all()
        municipios = Municipios.objects.all()
        estados = Estados.objects.all()

        if 'eliminar' in request.GET:
            try:
                Colonias.objects.filter(id_colonia=request.GET['eliminar']).delete()
                messages.success(request, "Colonia eliminada correctamente.")
            except Colonias.DoesNotExist:
                messages.error(request, f"No se encontró la colonia con ID {request.GET['eliminar']}.")
            return redirect('gentelella_page', page='cal_colonia')

        if request.method == 'POST' and 'editar' not in request.GET:
            nombre = request.POST.get('nombre')
            id_municipio = request.POST.get('id_municipio')
            id_estado = request.POST.get('id_estado')
            promedio_precio = request.POST.get('promedio_precio', None)
            zona = request.POST.get('zona')

            if nombre and id_municipio and id_estado:
                try:
                    municipio = Municipios.objects.get(id_municipio=id_municipio)
                    estado = Estados.objects.get(id_estado=id_estado)
                    Colonias.objects.create(
                        nombre=nombre,
                        id_municipio=municipio,
                        id_estado=estado,
                        promedio_precio=promedio_precio,
                        zona=zona
                    )
                    messages.success(request, "Colonia creada correctamente.")
                except Municipios.DoesNotExist:
                    messages.error(request, "Municipio no encontrado.")
                except Estados.DoesNotExist:
                    messages.error(request, "Estado no encontrado.")
                except IntegrityError:
                    messages.error(request, "Ya existe una colonia con ese nombre en el municipio seleccionado.")
            else:
                messages.error(request, "Faltan datos para crear la colonia.")

            return redirect('gentelella_page', page='cal_colonia')

        context.update({
            'colonias': colonias,
            'municipios': municipios,
            'estados': estados,
        })

    elif page == "editar_colonia":
        context['municipios'] = Municipios.objects.all()
        context['estados'] = Estados.objects.all()

        if 'editar' in request.GET:
            try:
                colonia_editar = Colonias.objects.get(id_colonia=request.GET['editar'])
                context['colonia_editar'] = colonia_editar
            except Colonias.DoesNotExist:
                messages.error(request, f"No se encontró la colonia con ID {request.GET['editar']}.")
                return redirect('gentelella_page', page='cal_colonia')

        if request.method == 'POST':
            id_colonia = request.POST.get('id_colonia')
            try:
                colonia = Colonias.objects.get(id_colonia=id_colonia)
                nombre = request.POST.get('nombre')
                id_municipio = request.POST.get('id_municipio')
                id_estado = request.POST.get('id_estado')
                promedio_precio = request.POST.get('promedio_precio', None)
                zona = request.POST.get('zona')
                if nombre and id_municipio and id_estado:
                    municipio = Municipios.objects.get(id_municipio=id_municipio)
                    estado = Estados.objects.get(id_estado=id_estado)
                    colonia.nombre = nombre
                    colonia.id_municipio = municipio
                    colonia.id_estado = estado
                    colonia.promedio_precio = promedio_precio if promedio_precio else None
                    colonia.zona = zona if zona else None
                    colonia.save()
                    messages.success(request, "Colonia actualizada correctamente.")
                    return redirect('gentelella_page', page='cal_colonia')
                else:
                    messages.error(request, "Faltan datos para actualizar la colonia.")
            except Colonias.DoesNotExist:
                messages.error(request, f"No se encontró la colonia con ID {id_colonia}.")
            except Municipios.DoesNotExist:
                messages.error(request, "Municipio no encontrado.")
            except IntegrityError:
                messages.error(request, "Ya existe una colonia con ese nombre.")
            except ValueError:
                messages.error(request, "El precio promedio debe ser un número válido.")
            return redirect('gentelella_page', page='editar_colonia', editar=id_colonia)

    elif page == "cal_estado":
        estados = Estados.objects.all()
        context['estados'] = estados

        if 'eliminar' in request.GET:
            try:
                estado = Estados.objects.get(id_estado=request.GET['eliminar'])
                estado.delete()
                messages.success(request, "Estado eliminado correctamente.")
            except Estados.DoesNotExist:
                messages.error(request, f"No se encontró el estado con ID {request.GET['eliminar']}.")
            return redirect('gentelella_page', page='cal_estado')

        if request.method == 'POST' and 'editar' not in request.GET:
            nombre = request.POST.get('nombre', '').strip()
            if nombre:
                try:
                    Estados.objects.create(nombre=nombre)
                    messages.success(request, "Estado creado correctamente.")
                except IntegrityError:
                    messages.error(request, "Ya existe un estado con ese nombre.")
            else:
                messages.error(request, "Faltan datos para crear el estado.")
            return redirect('gentelella_page', page='cal_estado')

    elif page == "editar_estado":
        if 'editar' in request.GET:
            try:
                estado_editar = Estados.objects.get(id_estado=request.GET['editar'])
                context['estado_editar'] = estado_editar
            except Estados.DoesNotExist:
                messages.error(request, f"No se encontró el estado con ID {request.GET['editar']}.")
                return redirect('gentelella_page', page='cal_estado')

        if request.method == 'POST':
            id_estado = request.POST.get('id_estado')
            nombre = request.POST.get('nombre')
            try:
                estado = Estados.objects.get(id_estado=id_estado)
                if nombre:
                    estado.nombre = nombre
                    estado.save()
                    messages.success(request, "Estado actualizado correctamente.")
                    return redirect('gentelella_page', page='cal_estado')
                else:
                    messages.error(request, "El nombre del estado no puede estar vacío.")
            except Estados.DoesNotExist:
                messages.error(request, f"No se encontró el estado con ID {id_estado}.")
            except IntegrityError:
                messages.error(request, "Ya existe un estado con ese nombre.")
            return redirect(f"{reverse('gentelella_page', kwargs={'page': 'editar_estado'})}?editar={id_estado}")

    elif page == "cal_municipio":
        municipios = Municipios.objects.select_related('id_estado').all()
        estados = Estados.objects.all()
        context['municipios'] = municipios
        context['estados'] = estados

        if 'eliminar' in request.GET:
            try:
                municipio = Municipios.objects.get(id_municipio=request.GET['eliminar'])
                municipio.delete()
                messages.success(request, "Municipio eliminado correctamente.")
            except Municipios.DoesNotExist:
                messages.error(request, f"No se encontró el municipio con ID {request.GET['eliminar']}.")
            return redirect('gentelella_page', page='cal_municipio')

        if request.method == 'POST' and 'editar' not in request.GET:
            nombre = request.POST.get('nombre')
            id_estado = request.POST.get('id_estado')
            if nombre and id_estado:
                try:
                    estado = Estados.objects.get(id_estado=id_estado)
                    Municipios.objects.create(nombre=nombre, id_estado=estado)
                    messages.success(request, "Municipio creado correctamente.")
                except Estados.DoesNotExist:
                    messages.error(request, "Estado no encontrado.")
                except IntegrityError:
                    messages.error(request, "Ya existe un municipio con ese nombre en el estado seleccionado.")
            else:
                messages.error(request, "Faltan datos para crear el municipio.")
            return redirect('gentelella_page', page='cal_municipio')

    elif page == "editar_municipio":
        context['estados'] = Estados.objects.all()
        if 'editar' in request.GET:
            try:
                municipio_editar = Municipios.objects.get(id_municipio=request.GET['editar'])
                context['municipio_editar'] = municipio_editar
            except Municipios.DoesNotExist:
                messages.error(request, f"No se encontró el municipio con ID {request.GET['editar']}.")
                return redirect('gentelella_page', page='cal_municipio')

        if request.method == 'POST':
            id_municipio = request.POST.get('id_municipio')
            nombre = request.POST.get('nombre')
            id_estado = request.POST.get('id_estado')
            try:
                municipio = Municipios.objects.get(id_municipio=id_municipio)
                if nombre and id_estado:
                    estado = Estados.objects.get(id_estado=id_estado)
                    municipio.nombre = nombre
                    municipio.id_estado = estado
                    municipio.save()
                    messages.success(request, "Municipio actualizado correctamente.")
                    return redirect('gentelella_page', page='cal_municipio')
                else:
                    messages.error(request, "Faltan datos para actualizar el municipio.")
            except Municipios.DoesNotExist:
                messages.error(request, f"No se encontró el municipio con ID {id_municipio}.")
            except Estados.DoesNotExist:
                messages.error(request, "Estado no encontrado.")
            except IntegrityError:
                messages.error(request, "Ya existe un municipio con ese nombre.")
            return redirect('gentelella_page', page='editar_municipio', editar=id_municipio)

    elif page == "cal_cp":
        codigos = CodigosPostales.objects.select_related('id_colonia', 'id_municipio', 'id_estado').all()
        colonias = Colonias.objects.all()
        municipios = Municipios.objects.all()
        estados = Estados.objects.all()

        context['codigos'] = codigos
        context['colonias'] = colonias
        context['municipios'] = municipios
        context['estados'] = estados

        if 'eliminar' in request.GET:
            try:
                codigo = CodigosPostales.objects.get(id_codigo_postal=request.GET['eliminar'])
                codigo.delete()
                messages.success(request, "Código eliminado correctamente.")
            except CodigosPostales.DoesNotExist:
                messages.error(request, f"No se encontró el código con ID {request.GET['eliminar']}.")
            return redirect('gentelella_page', page='cal_cp')

        if request.method == 'POST' and 'editar' not in request.GET:
            codigo_valor = request.POST.get('codigo')
            id_colonia = request.POST.get('id_colonia')
            id_municipio = request.POST.get('id_municipio')
            id_estado = request.POST.get('id_estado')

            errors = []
            if not codigo_valor:
                errors.append("El código postal es obligatorio.")
            if not id_colonia:
                errors.append("La colonia es obligatoria.")
            if len(codigo_valor) > 5:
                errors.append("El código postal no puede exceder 5 caracteres.")

            if errors:
                for error in errors:
                    messages.error(request, error)
                return redirect('gentelella_page', page='cal_cp')

            try:
                colonia = Colonias.objects.get(id_colonia=id_colonia)
                municipio = Municipios.objects.get(id_municipio=id_municipio) if id_municipio else None
                estado = Estados.objects.get(id_estado=id_estado) if id_estado else None

                CodigosPostales.objects.create(
                    codigo=codigo_valor,
                    id_colonia=colonia,
                    id_municipio=municipio,
                    id_estado=estado
                )
                messages.success(request, "Código postal creado correctamente.")
            except Colonias.DoesNotExist:
                messages.error(request, "La colonia seleccionada no existe.")
            except Municipios.DoesNotExist:
                messages.error(request, "El municipio seleccionado no existe.")
            except Estados.DoesNotExist:
                messages.error(request, "El estado seleccionado no existe.")
            except IntegrityError:
                messages.error(request, "Ya existe un código postal con ese valor para la colonia seleccionada.")
            except ValueError as e:
                messages.error(request, f"Error en los datos proporcionados: {str(e)}")
            return redirect('gentelella_page', page='cal_cp')

    elif page == "editar_cp":
        context['colonias'] = Colonias.objects.all()
        context['municipios'] = Municipios.objects.all()
        context['estados'] = Estados.objects.all()

        if 'editar' in request.GET:
            try:
                codigo_editar = CodigosPostales.objects.get(id_codigo_postal=request.GET['editar'])
                context['codigo_editar'] = codigo_editar
            except CodigosPostales.DoesNotExist:
                messages.error(request, f"No se encontró el código con ID {request.GET['editar']}.")
                return redirect('gentelella_page', page='cal_cp')

        if request.method == 'POST':
            id_codigo_postal = request.POST.get('id_codigo_postal')
            codigo_valor = request.POST.get('codigo')
            id_colonia = request.POST.get('id_colonia')
            id_municipio = request.POST.get('id_municipio')
            id_estado = request.POST.get('id_estado')

            try:
                codigo_postal = CodigosPostales.objects.get(id_codigo_postal=id_codigo_postal)
                if codigo_valor and id_colonia and id_municipio and id_estado:
                    colonia = Colonias.objects.get(id_colonia=id_colonia)
                    municipio = Municipios.objects.get(id_municipio=id_municipio)
                    estado = Estados.objects.get(id_estado=id_estado)

                    codigo_postal.codigo = codigo_valor
                    codigo_postal.id_colonia = colonia
                    codigo_postal.id_municipio = municipio
                    codigo_postal.id_estado = estado
                    codigo_postal.save()
                    messages.success(request, "Código postal actualizado correctamente.")
                    return redirect('gentelella_page', page='cal_cp')
                else:
                    messages.error(request, "Faltan datos para actualizar el código.")
            except (CodigosPostales.DoesNotExist, Colonias.DoesNotExist, Municipios.DoesNotExist, Estados.DoesNotExist):
                messages.error(request, "Datos inválidos.")
            except IntegrityError:
                messages.error(request, "Ya existe un código con ese valor.")
            return redirect('gentelella_page', page='editar_cp', editar=id_codigo_postal)

    elif page == "cal_estimaciones":
        propiedades = Propiedades.objects.select_related('id_estado', 'id_municipio', 'id_colonia', 'id_codigo_postal').all()
        context['propiedades'] = propiedades
        context['estados'] = Estados.objects.all()
        context['municipios'] = Municipios.objects.all()
        context['colonias'] = Colonias.objects.all()
        context['codigos_postales'] = CodigosPostales.objects.all()

        if 'eliminar_individual' in request.GET and 'id_propiedad' in request.GET:
            try:
                propiedad_id = request.GET['id_propiedad']
                propiedad = Propiedades.objects.get(id_propiedad=propiedad_id)
                propiedad.delete()
                messages.success(request, f"Propiedad con ID {propiedad_id} eliminada correctamente.")
            except Propiedades.DoesNotExist:
                messages.error(request, f"No se encontró la propiedad con ID {propiedad_id}.")
            except Exception as e:
                messages.error(request, f"Error al eliminar la propiedad: {str(e)}")
            return redirect('gentelella_page', page='cal_estimaciones')

        if 'eliminar' in request.GET:
            try:
                Propiedades.objects.all().delete()
                with connection.cursor() as cursor:
                    cursor.execute("ALTER TABLE propiedades AUTO_INCREMENT = 1")
                messages.success(request, "Todas las propiedades han sido eliminadas y los IDs reiniciados a 1.")
            except Exception as e:
                messages.error(request, f"Error al eliminar propiedades o reiniciar IDs: {str(e)}")
            return redirect('gentelella_page', page='cal_estimaciones')

    elif page == "cal_usuarios":
        try:
            usuarios = Usuarios.objects.all()
        except Exception as e:
            usuarios = []
            messages.error(request, f"Error al recuperar usuarios: {str(e)}")

        if 'eliminar' in request.GET:
            try:
                usuario = Usuarios.objects.get(id=request.GET['eliminar'])
                usuario.delete()
                messages.success(request, "Usuario eliminado correctamente.")
            except Usuarios.DoesNotExist:
                messages.error(request, f"No se encontró el usuario con ID {request.GET['eliminar']}.")
            return redirect('gentelella_page', page='cal_usuarios')

        if request.method == 'POST' and 'editar' not in request.GET:
            username = request.POST.get('username')
            first_name = request.POST.get('nombre')
            roles = request.POST.get('roles')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            if username and first_name and email and password1 and password2:
                if password1 == password2:
                    try:
                        usuario = Usuarios(
                            username=username,
                            first_name=first_name,
                            email=email,
                            roles=roles,
                            password=password1,  # Contraseña en texto plano
                            is_active=True,
                            date_joined=timezone.now()
                        )
                        usuario.save()
                        messages.success(request, "Usuario creado correctamente.")
                    except IntegrityError:
                        messages.error(request, "El nombre de usuario o correo ya existe.")
                else:
                    messages.error(request, "Las contraseñas no coinciden.")
            else:
                messages.error(request, "Faltan datos para crear el usuario.")

            return redirect('gentelella_page', page='cal_usuarios')

        context.update({'usuarios': usuarios})

    elif page == "editar_usuario":
        if 'editar' in request.GET:
            try:
                usuario_editar = Usuarios.objects.get(id=request.GET['editar'])
                context['usuario_editar'] = usuario_editar
            except Usuarios.DoesNotExist:
                messages.error(request, f"No se encontró el usuario con ID {request.GET['editar']}.")
                return redirect('gentelella_page', page='cal_usuarios')

        if request.method == 'POST':
            id_usuario = request.POST.get('id_usuario')
            try:
                usuario = Usuarios.objects.get(id=id_usuario)
                username = request.POST.get('username')
                first_name = request.POST.get('nombre')
                email = request.POST.get('email')
                roles = request.POST.get('roles')
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')

                if username and first_name and email:
                    usuario.username = username
                    usuario.first_name = first_name
                    usuario.email = email
                    if roles:
                        usuario.roles = roles
                    if password1 and password2 and password1 == password2:
                        usuario.password = password1  # Contraseña en texto plano
                    elif password1 or password2:
                        messages.error(request, "Las contraseñas no coinciden o están incompletas.")
                        return redirect('gentelella_page', page='editar_usuario', editar=id_usuario)

                    if 'profile_picture' in request.FILES:
                        usuario.profile_picture = request.FILES['profile_picture']

                    usuario.save()
                    messages.success(request, "Usuario actualizado correctamente.")
                    return redirect('gentelella_page', page='cal_usuarios')
                else:
                    messages.error(request, "Faltan datos para actualizar el usuario.")
            except Usuarios.DoesNotExist:
                messages.error(request, f"No se encontró el usuario con ID {id_usuario}.")
            except IntegrityError:
                messages.error(request, "El nombre de usuario o correo ya existe.")
            return redirect('gentelella_page', page='editar_usuario', editar=id_usuario)

    elif page == "cal_vista_usuarios":
        try:
            vistas = AlcaldiaVistas.objects.all()
        except Exception as e:
            vistas = []
            messages.error(request, f"Error al recuperar vistas: {str(e)}")

        if 'eliminar' in request.GET:
            try:
                vista = AlcaldiaVistas.objects.get(id=request.GET['eliminar'])
                vista.delete()
                messages.success(request, "Vista eliminada correctamente.")
            except AlcaldiaVistas.DoesNotExist:
                messages.error(request, f"No se encontró la vista con ID {request.GET['eliminar']}.")
            return redirect('gentelella_page', page='cal_vista_usuarios')

        if request.method == 'POST' and 'editar' not in request.GET:
            estado = request.POST.get('estado')
            alcaldia = request.POST.get('alcaldia')
            colonia = request.POST.get('colonia')
            promedio_mxn = request.POST.get('promedio_mxn')
            zona = request.POST.get('zona')

            try:
                promedio_mxn = float(promedio_mxn.replace('$', '').replace(',', ''))
            except (ValueError, AttributeError):
                messages.error(request, "Formato de promedio inválido. Use formato: $26,301")
                return redirect('gentelella_page', page='cal_vista_usuarios')

            if estado and alcaldia and colonia and promedio_mxn:
                try:
                    AlcaldiaVistas.objects.create(
                        estado=estado,
                        alcaldia=alcaldia,
                        colonia=colonia,
                        promedio_mxn=promedio_mxn,
                        zona=zona if zona else None
                    )
                    messages.success(request, "Vista creada correctamente.")
                except Exception as e:
                    messages.error(request, f"Error al crear vista: {str(e)}")
            else:
                messages.error(request, "Faltan datos obligatorios para crear la vista.")
            return redirect('gentelella_page', page='cal_vista_usuarios')

        context.update({'vistas': vistas})

    elif page == "editar_vistas_alcaldia":
        if 'editar' in request.GET:
            try:
                vista_editar = AlcaldiaVistas.objects.get(id=request.GET['editar'])
                context['vista_editar'] = vista_editar
            except AlcaldiaVistas.DoesNotExist:
                messages.error(request, f"No se encontró la vista con ID {request.GET['editar']}.")
                return redirect('gentelella_page', page='cal_vista_usuarios')

        if request.method == 'POST':
            id_vista = request.POST.get('id')
            try:
                vista = AlcaldiaVistas.objects.get(id=id_vista)
                estado = request.POST.get('estado')
                alcaldia = request.POST.get('alcaldia')
                colonia = request.POST.get('colonia')
                promedio_mxn = request.POST.get('promedio_mxn')
                zona = request.POST.get('zona')

                try:
                    promedio_mxn = float(promedio_mxn.replace('$', '').replace(',', ''))
                except (ValueError, AttributeError):
                    messages.error(request, "Formato de promedio inválido. Use formato: $26,301")
                    return redirect('gentelella_page', page='editar_vistas_alcaldia', editar=id_vista)

                if estado and alcaldia and colonia and promedio_mxn:
                    vista.estado = estado
                    vista.alcaldia = alcaldia
                    vista.colonia = colonia
                    vista.promedio_mxn = promedio_mxn
                    vista.zona = zona if zona else None
                    vista.save()
                    messages.success(request, "Vista actualizada correctamente.")
                    return redirect('gentelella_page', page='cal_vista_usuarios')
                else:
                    messages.error(request, "Faltan datos obligatorios para actualizar la vista.")
            except AlcaldiaVistas.DoesNotExist:
                messages.error(request, f"No se encontró la vista con ID {id_vista}.")
            except Exception as e:
                messages.error(request, f"Error al actualizar vista: {str(e)}")
            return redirect('gentelella_page', page='editar_vistas_alcaldia', editar=id_vista)

    elif page == 'index':
        total_usuarios = Usuarios.objects.count()
        total_estados = Estados.objects.count()
        total_municipios = Municipios.objects.count()
        total_colonias = Colonias.objects.count()
        total_cp = CodigosPostales.objects.count()
        total_propiedades = Propiedades.objects.count()

        estados_municipios = Estados.objects.annotate(total=Count('municipios')).order_by('-total')[:10]
        estados = [e.nombre for e in estados_municipios]
        totales = [e.total for e in estados_municipios]

        plt.figure(figsize=(8, 4))
        plt.barh(estados, totales, color='skyblue')
        plt.title('Top Estados con Más Municipios')
        plt.xlabel('Cantidad de Municipios')
        plt.tight_layout()
        plt.gca().invert_yaxis()

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        grafico_base64 = base64.b64encode(image_png).decode('utf-8')
        plt.close()

        context.update({
            'total_usuarios': total_usuarios,
            'total_estados': total_estados,
            'total_municipios': total_municipios,
            'total_colonias': total_colonias,
            'total_cp': total_cp,
            'total_propiedades': total_propiedades,
            'grafico_base64': grafico_base64,
        })

    return render(request, f'gentelella/{page}.html', context)

@never_cache
@login_required_custom
def vista_documentacion(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('signin')
    return render(request, 'documentacion/doc.html', {'usuario': usuario})

# Honorarios
def format_currency(value):
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "$0.00"

def safe_divide(a, b):
    return a / b * 100 if b > 0 else 0.0

def calcular_honorarios(calc_type, valor_comercial, precio_de_sesion):
    pendiente = 0.06
    constants = {
        'sentencia': {'hm': 435000.00, 'pc': 3000000.00},
        'adjudicado': {'hm': 390000.00, 'pc': 5060000.00}
    }
    calc_type = calc_type if calc_type in constants else 'sentencia'
    hm = constants[calc_type]['hm']
    pc = constants[calc_type]['pc']
    return hm if valor_comercial <= pc else pendiente * (valor_comercial - pc) + hm

@never_cache
@login_required_custom
def honorarios_calculator(request):
    usuario = Usuarios.objects.filter(id=request.session.get('usuario_id')).first()
    if not usuario:
        return redirect('signin')
    context = {
        'usuario': usuario,
        'calc_type': request.POST.get('calcType', 'sentencia'),
        'valor_comercial': 0.0,
        'precio_de_sesion': 0.0,
        'honorarios': 0.0,
        'pago_unico': 0.0,
        'firma': 0.0,
        'segundo_pago': 0.0,
        'entrega': 0.0,
        'total': 0.0,
        'valor_ext': 0.0,
        'cotizacion': 0.0,
        'costo_total': 0.0,
        'porcentaje_vc': 0.0,
        'ganancia': 0.0,
        'valor_judicial': 0.0,
    }

    if request.method == 'POST':
        try:
            valor_comercial = float(request.POST.get('valorComercial', 0.0))
            precio_de_sesion = float(request.POST.get('precioDeSesion', 0.0))
        except (ValueError, TypeError):
            valor_comercial = 0.0
            precio_de_sesion = 0.0

        context['valor_comercial'] = valor_comercial
        context['precio_de_sesion'] = precio_de_sesion
        context['honorarios'] = calcular_honorarios(context['calc_type'], valor_comercial, precio_de_sesion)
        context['pago_unico'] = context['honorarios'] * 0.9
        context['firma'] = context['honorarios'] * 0.75
        context['segundo_pago'] = precio_de_sesion
        context['entrega'] = context['honorarios'] * 0.25
        context['total'] = context['firma'] + context['segundo_pago'] + context['entrega']
        context['valor_ext'] = valor_comercial
        context['cotizacion'] = context['valor_ext'] * 0.5
        context['costo_total'] = precio_de_sesion + context['honorarios']
        context['porcentaje_vc'] = safe_divide(context['costo_total'], valor_comercial)
        context['ganancia'] = safe_divide(valor_comercial - context['costo_total'], valor_comercial)
        context['valor_judicial'] = (2 / 3) * valor_comercial

        for key in ['valor_comercial', 'precio_de_sesion', 'honorarios', 'pago_unico',
                    'firma', 'segundo_pago', 'entrega', 'total', 'valor_ext', 'cotizacion',
                    'costo_total', 'valor_judicial']:
            context[key] = format_currency(context[key])

        for key in ['porcentaje_vc', 'ganancia']:
            context[key] = "{:.2f}%".format(context[key])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            context_json = context.copy()
            context_json.pop('usuario', None)
            return JsonResponse(context_json)

    return render(request, 'honorarios.html', context)


