# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Usuarios(models.Model):
    id = models.AutoField(primary_key=True)
    password = models.CharField(max_length=150, default='12345678')
    last_login = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, default='')
    last_name = models.CharField(max_length=150, default='')
    email = models.EmailField(max_length=254)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    roles = models.CharField(max_length=50)

    class Meta:
        db_table = 'usuarios' # Asegura que Django use tu tabla ya creada
        managed = True 

    def __str__(self):
        return self.username

class AlcaldiaVistas(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    estado = models.CharField(db_column='Estado', max_length=100)  # Field name made lowercase.
    alcaldia = models.CharField(db_column='Alcaldia', max_length=100)  # Field name made lowercase.
    colonia = models.CharField(db_column='Colonia', max_length=100)  # Field name made lowercase.
    promedio_mxn = models.CharField(db_column='Promedio_MXN', max_length=30)  # Field name made lowercase.
    zona = models.CharField(db_column='Zona', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'alcaldia_vistas'

def __str__(self):
        return f"{self.alcaldia} - {self.colonia}"


class Estados(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'estados'
        managed = True
        ordering = ['nombre']  # 👈 Esto aplica el orden alfabético SIEMPRE

    def __str__(self):
        return self.nombre


class Municipios(models.Model):
    id_municipio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    id_estado = models.ForeignKey(Estados, models.DO_NOTHING, db_column='id_estado')

    class Meta:
        db_table = 'municipios'
        unique_together = (('nombre', 'id_estado'),)
        managed = True
        ordering = ['nombre']  # 👈 Esto aplica el orden alfabético SIEMPRE

    def __str__(self):
        return self.nombre


class Colonias(models.Model):
    id_colonia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    id_municipio = models.ForeignKey(Municipios, models.DO_NOTHING, db_column='id_municipio')
    id_estado = models.ForeignKey(Estados, models.DO_NOTHING, db_column='id_estado', null=True, blank=True)
    promedio_precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    zona = models.CharField(max_length=50)

    class Meta:
        db_table = 'colonias'
        unique_together = (('nombre', 'id_municipio'),)
        managed = True
        ordering = ['nombre']  # 👈 Esto aplica el orden alfabético SIEMPRE

    def __str__(self):
        return self.nombre


class CodigosPostales(models.Model):
    id_codigo_postal = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=5)
    id_colonia = models.ForeignKey(Colonias, models.DO_NOTHING, db_column='id_colonia')
    id_municipio = models.ForeignKey(Municipios, models.DO_NOTHING, db_column='id_municipio', null=True, blank=True)
    id_estado = models.ForeignKey(Estados, models.DO_NOTHING, db_column='id_estado', null=True, blank=True)

    class Meta:
        db_table = 'codigos_postales'
        unique_together = (('codigo', 'id_colonia'),)
        managed = True  # ponlo en True si deseas que Django lo administre

    def __str__(self):
        return self.codigo



class Propiedades(models.Model):
    id_propiedad = models.AutoField(primary_key=True)
    tipo_propiedad = models.CharField(max_length=50)
    calle = models.CharField(max_length=100)
    id_codigo_postal = models.ForeignKey(CodigosPostales, models.DO_NOTHING, db_column='id_codigo_postal')
    recamaras = models.IntegerField()
    sanitarios = models.DecimalField(max_digits=3, decimal_places=1)
    estacionamiento = models.IntegerField()
    terreno = models.DecimalField(max_digits=10, decimal_places=2)
    construccion = models.DecimalField(max_digits=10, decimal_places=2)
    estado_conservacion = models.CharField(max_length=50)
    comentarios = models.TextField(blank=True, null=True)
    valor_aprox = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_judicial = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_comercial = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)  # <-- este faltaba
    valor_inicial = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)  # <-- este faltaba
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    id_colonia = models.ForeignKey(Colonias, models.DO_NOTHING, db_column='id_colonia', null=True, blank=True)
    id_municipio = models.ForeignKey(Municipios, models.DO_NOTHING, db_column='id_municipio', null=True, blank=True)
    id_estado = models.ForeignKey(Estados, models.DO_NOTHING, db_column='id_estado', null=True, blank=True)


    class Meta:
        db_table = 'propiedades'
        managed = True  # Cambia a True si puedes gestionar la tabla con Django

    def __str__(self):
        return f'{self.tipo_propiedad} en {self.calle}'
    

class GraficaAlcaldia(models.Model):
    id_grafica = models.AutoField(primary_key=True)
    grafica_alcaldia = models.CharField(max_length=100, null=True)
    grafica_nombre = models.CharField(max_length=100, null=True)
    grafica_cp = models.IntegerField(null=True)
    grafica_prom_prop = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    grafica_prom_hey = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    grafica_prom_clau = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    grafica_prom_mud = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    grafica_prom_altal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    grafica_promedio = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"{self.grafica_alcaldia} - {self.grafica_promedio}"

    class Meta:
        db_table = 'graficas_alcaldias'
        managed = True