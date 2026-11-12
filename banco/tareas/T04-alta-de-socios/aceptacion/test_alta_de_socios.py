from apoyo import auth
from pulso import db


def alta(cliente, nombre='Ana Pérez', email='ana@example.com', plan='basico'):
    return cliente.post('/socios', json={'nombre': nombre, 'email': email, 'plan': plan})


def test_alta_basico(cliente):
    r = alta(cliente)
    assert r.status_code == 201
    cuerpo = r.json()
    assert {k: cuerpo[k] for k in ('nombre', 'email', 'plan', 'creditos')} == {
        'nombre': 'Ana Pérez', 'email': 'ana@example.com', 'plan': 'basico', 'creditos': 8}
    assert isinstance(cuerpo['id'], int)


def test_alta_premium(cliente):
    assert alta(cliente, plan='premium').json()['creditos'] == 20


def test_el_token_sirve_para_autenticarse(cliente):
    cuerpo = alta(cliente).json()
    assert len(cuerpo['token']) >= 32
    r = cliente.get('/yo', headers=auth(cuerpo))
    assert r.status_code == 200
    assert r.json()['email'] == 'ana@example.com'
    assert r.json()['creditos'] == 8


def test_tokens_distintos(cliente):
    a = alta(cliente, email='a@example.com').json()['token']
    b = alta(cliente, email='b@example.com').json()['token']
    assert a != b


def test_normaliza_nombre_y_email(cliente):
    cuerpo = alta(cliente, nombre='  Ana Pérez  ', email='  Ana.Perez@Example.COM ').json()
    assert cuerpo['nombre'] == 'Ana Pérez'
    assert cuerpo['email'] == 'ana.perez@example.com'
    assert db.socio(cuerpo['id'])['email'] == 'ana.perez@example.com'


def test_email_repetido(cliente):
    assert alta(cliente, email='ana@example.com').status_code == 201
    assert alta(cliente, nombre='Otra Ana', email='ANA@example.com ').status_code == 409
    db.crear_socio('Juan Gómez', 'juan@example.com')
    assert alta(cliente, nombre='Juan', email='Juan@Example.com').status_code == 409


def test_emails_invalidos(cliente):
    for email in ['ana', 'ana@', '@example.com', 'ana@example', 'ana@@example.com', 'ana@b@example.com',
                  'ana@.example.com', 'ana@example.', 'ana perez@example.com', '']:
        assert alta(cliente, email=email).status_code == 422, email


def test_emails_validos_en_el_borde(cliente):
    for i, email in enumerate(['a@b.co', 'ana.perez+gym@mail.example.com', 'x_1@sub.dominio.uy']):
        assert alta(cliente, nombre=f'Socio {i}', email=email).status_code == 201, email


def test_largo_del_nombre(cliente):
    for i, nombre in enumerate(['', '   ', 'A', ' A ', 'x' * 81]):
        assert alta(cliente, nombre=nombre, email=f'{i}@example.com').status_code == 422, repr(nombre)
    assert alta(cliente, nombre='Al', email='al@example.com').status_code == 201
    assert alta(cliente, nombre='x' * 80, email='largo@example.com').status_code == 201


def test_plan_invalido(cliente):
    for plan in ['gold', 'Premium', '']:
        assert alta(cliente, plan=plan).status_code == 422, plan


def test_faltan_datos(cliente):
    for faltante in ('nombre', 'email', 'plan'):
        datos = {'nombre': 'Ana Pérez', 'email': 'ana@example.com', 'plan': 'basico'}
        del datos[faltante]
        assert cliente.post('/socios', json=datos).status_code == 422, faltante


def test_correo_de_bienvenida(cliente):
    alta(cliente, email=' Ana@Example.com')
    [enviado] = db.correos()
    assert enviado['para'] == 'ana@example.com'
    assert enviado['asunto'] == 'Te damos la bienvenida a Pulso'


def test_un_alta_rechazada_no_crea_socio_ni_manda_correo(cliente):
    alta(cliente, email='ana@example')
    alta(cliente, plan='gold')
    assert db.correos() == []
    with db.conexion() as con:
        assert con.execute('SELECT COUNT(*) FROM socios').fetchone()[0] == 0
