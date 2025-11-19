from django.contrib import admin
from django.urls import path
from tasks import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin y autenticación
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.signout, name='signout'),  # Mantenemos el nombre 'signout' como en el original

    # Rutas de recuperación de contraseña
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='recuperacion/forgotpassword.html',
        email_template_name='recuperacion/password_reset_email.html',
        subject_template_name='recuperacion/password_reset_subject.txt'
    ), name='password_reset'),
    path('reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='recuperacion/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='recuperacion/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='recuperacion/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Página de bienvenida y estimaciones
    path('', views.welcome, name='welcome'),
    path('estimaciones/', views.estimaciones, name='estimaciones'),
    path('analisis/', views.analisis, name='analisis'),
    path('honorarios/', views.honorarios_calculator, name='honorarios_calculator'),
    path('resultados/<int:propiedad_id>/', views.mostrar_resultado, name='mostrar_resultado'),
    # Rutas añadidas para reportes
    path('reporte_individual/<int:propiedad_id>/', views.reporte_individual, name='reporte_individual'),
    path('reporte_completo/<int:propiedad_id>/', views.generar_reporte_completo, name='reporte_completo'),

    # Ajax para colonias y CP
    path('obtener_colonias/', views.obtener_colonias, name='obtener_colonias'),
    path('obtener_municipios/', views.obtener_municipios, name='obtener_municipios'),
    path('obtener_codigos_postales/', views.obtener_codigos_postales, name='obtener_codigos_postales'),

    # Alcaldías
    path('benito/', views.vista_benito_juarez, name='benito'),
    path('alvaro/', views.vista_alvaro, name='alvaro'),
    path('coyoacan/', views.vista_coyoacan, name='coyoacan'),
    path('xochimilco/', views.vista_xochimilco, name='xochimilco'),
    path('azcapotzalco/', views.vista_azcapotzalco, name='azcapotzalco'),
    path('cuajimalpa/', views.vista_cuajimalpa, name='cuajimalpa'),
    path('cuauhtemoc/', views.vista_cuauhtemoc, name='cuauhtemoc'),
    path('miguel/', views.vista_miguel, name='miguel'),
    path('gustavo/', views.vista_gustavo, name='gustavo'),
    path('iztacalco/', views.vista_iztacalco, name='iztacalco'),
    path('iztapalapa/', views.vista_iztapalapa, name='iztapalapa'),
    path('magda/', views.vista_magda, name='magda'),
    path('milpa/', views.vista_milpa, name='milpa'),
    path('tlahuac/', views.vista_tlahuac, name='tlahuac'),
    path('tlalpan/', views.vista_tlalpan, name='tlalpan'),
    path('venustiano/', views.vista_venustiano, name='venustiano'),

    # Panel admin Gentelella
    path('admin-panel/<str:page>/', views.gentelella_view, name='gentelella_page'),

    # URL para el acceso de vista de la documentación
    path('doc/', views.vista_documentacion, name='documentacion'),

    # Nuevas URLs para las categorías

      # CV corporativo
    path('cv_corporativo/', views.cv_corporativo, name='cv_corporativo'),

    # CV horizontal
    path('cv_horizontal/', views.cv_horizontal, name='cv_horizontal'),

    # CV vertical
    path('cv_vertical/', views.cv_vertical, name='cv_vertical'),

    # CV horizontal ingles
    path('cv_horizontal_ingles/', views.cv_horizontal_ingles, name='cv_horizontal_ingles'),

     # CV vertical ingles
    path('cv_vertical_ingles/', views.cv_vertical_ingles, name='cv_vertical_ingles'),

    # Materiales
    
    # Materiales General Apoyos
    path('generalA/', views.generalA, name='generalA'),
    path('acceso_oficinas/', views.acceso_oficinas, name='acceso_oficinas'),
    path('buyer/', views.buyer, name='buyer'),
    path('lineamientos/', views.lineamientos, name='lineamientos'),
    path('redes/', views.redes, name='redes'),
    path('meta/', views.meta, name='meta'),
    path('whatsapp/', views.whatsapp, name='whatsapp'),
    path('speech/', views.speech, name='speech'),
    path('estacionamiento/', views.estacionamiento, name='estacionamiento'),

    # Datos de Pago
     # Nueva ruta para BBVA
    path('bbva_pagos/', views.bbva_pagos, name='bbva_pagos'), 
    path('bbva/', views.bbva, name='bbva'), 
    path('p_recover/', views.p_recover, name='p_recover'), 
    path('recu_ban/', views.recu_ban, name='recu_ban'),
    path('ticket/', views.ticket, name='ticket'),

    # Nueva ruta para Santander,
    path('santander_pagos/', views.santander_pagos, name='santander_pagos'),  
    path('SANTANDER_BBVA/', views.SANTANDER_BBVA, name='SANTANDER_BBVA'),
    path('SANTANDER_BBVA_RECOVER/', views.SANTANDER_BBVA_RECOVER, name='SANTANDER_BBVA_RECOVER'),
    path('recu_ban_2/', views.recu_ban_2, name='recu_ban_2'),
    path('ticket2/', views.ticket2, name='ticket2'),

    #Presentaciones de Producto
    path('Presentaciones_de_Producto/', views.Presentaciones_de_Producto, name='Presentaciones_de_Producto'),
    path('Exclusiva_CLASSIC_ALTALTIUM/', views.Exclusiva_CLASSIC_ALTALTIUM, name='Exclusiva_CLASSIC_ALTALTIUM'),
    path('FLIPPING_2024/', views.FLIPPING_2024, name='FLIPPING_2024'),

    #Academia Altaltium
    path('Academia_Altaltium/', views.Academia_Altaltium, name='Academia_Altaltium'),
    path('Fases_Juicio/', views.Fases_Juicio, name='Fases_Juicio'),




    path('documentos_destacados/', views.documentos_destacados, name='documentos_destacados'),
    path('como_llegar/', views.como_llegar, name='como_llegar'),
    path('logos/', views.logos, name='logos'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)