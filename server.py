from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import sqlite3

def init_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE usuarios (id INTEGER PRIMARY KEY, usuario TEXT, clave TEXT, rol TEXT)')
    cursor.execute('CREATE TABLE productos (id INTEGER PRIMARY KEY, nombre TEXT, precio REAL, stock INTEGER)')
    cursor.executemany('INSERT INTO usuarios (usuario, clave, rol) VALUES (?, ?, ?)', [
        ('admin', 'admin123', 'administrador'),
        ('comprador1', 'user123', 'cliente')
    ])
    cursor.executemany('INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)', [
        ('Teclado Mecánico RGB 75%', 85.00, 15),
        ('Mouse Gamer Inalámbrico', 45.50, 22),
        ('Monitor 24" 144Hz', 180.00, 8),
        ('Alfombrilla XL', 15.00, 50)
    ])
    conn.commit()
    return conn

db_conn = init_db()
SESION = {"usuario": None, "rol": None}

class TiendaHandler(BaseHTTPRequestHandler):

    def responder_archivo(self, nombre_archivo, content_type):
        """Lee y sirve cualquier tipo de archivo externo desde el disco"""
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header('Content-type', f'{content_type}; charset=utf-8')
            self.end_headers()
            self.wfile.write(contenido.encode('utf-8'))
            return contenido
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            return None

    def do_GET(self):
        url_parseada = urlparse(self.path)
        ruta = url_parseada.path
        parametros = parse_qs(url_parseada.query)

        # Enrutamiento de archivos estáticos de diseño y comportamiento
        if ruta == '/estilos.css':
            self.responder_archivo('estilos.css', 'text/css')
            return
        elif ruta == '/app.js':
            self.responder_archivo('app.js', 'application/javascript')
            return

        if ruta == '/logout':
            SESION['usuario'] = None
            SESION['rol'] = None
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
            return

        if ruta == '/':
            if SESION['usuario']:
                self.send_response(303)
                self.send_header('Location', '/dashboard')
                self.end_headers()
                return

            # Cargar y procesar HTML de Login
            try:
                with open('login.html', 'r', encoding='utf-8') as f:
                    html = f.read()
                
                error_html = ""
                if "error" in parametros:
                    error_html = f'<div class="error">{parametros["error"][0]}</div>'
                
                html = html.replace('<!-- {{ERROR_PLACEHOLDER}} -->', error_html)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()

        elif ruta == '/dashboard':
            if not SESION['usuario']:
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
                return

            # Obtener los productos desde la Base de Datos
            cursor = db_conn.cursor()
            cursor.execute("SELECT * FROM productos")
            productos = cursor.fetchall()

            tabla_productos = ""
            for p in productos:
                tabla_productos += f'''
                <tr>
                    <td>{p[0]}</td>
                    <td>{p[1]}</td>
                    <td>${p[2]:.2f}</td>
                    <td>{p[3]}</td>
                </tr>
                '''

            # Cargar y renderizar dinámicamente el HTML del Dashboard
            try:
                with open('dashboard.html', 'r', encoding='utf-8') as f:
                    html = f.read()
                
                # Inyección de variables en las etiquetas ficticias creadas en el HTML
                html = html.replace('{{ROL_USUARIO}}', str(SESION['rol']))
                html = html.replace('<!-- {{TABLA_PRODUCTOS}} -->', tabla_productos)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        ruta = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        datos = parse_qs(post_data)

        if ruta == '/login-procesar':
            username = datos.get('username')[0] if 'username' in datos else ''
            password = datos.get('password')[0] if 'password' in datos else ''
            cursor = db_conn.cursor()
            query = "SELECT usuario, rol FROM usuarios WHERE usuario = ? AND clave = ?"
            
            try:
                cursor.execute(query, (username, password))
                user = cursor.fetchone()
                if user:
                    SESION['usuario'] = user[0]
                    SESION['rol'] = user[1]
                    self.send_response(303)
                    self.send_header('Location', '/dashboard')
                    self.end_headers()
                else:
                    self.send_response(303)
                    self.send_header('Location', '/?error=Credenciales+incorrectas')
                    self.end_headers()
            except Exception as e:
                self.send_response(303)
                self.send_header('Location', f'/?error=Error+SQL:+{str(e)}')
                self.end_headers()

        elif ruta == '/crear':
            nombre = datos.get('nombre')[0] if 'nombre' in datos else ''
            precio = datos.get('precio')[0] if 'precio' in datos else '0'
            stock = datos.get('stock')[0] if 'stock' in datos else '0'

            cursor = db_conn.cursor()
            cursor.execute("INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)", (nombre, float(precio), int(stock)))
            db_conn.commit()
            self.send_response(303)
            self.send_header('Location', '/dashboard')
            self.end_headers()           

        elif ruta == '/actualizar':
            id_producto = datos.get('id')[0] if 'id' in datos else None
            nombre = datos.get('nombre')[0] if 'nombre' in datos else ''
            precio = datos.get('precio')[0] if 'precio' in datos else '0'
            stock = datos.get('stock')[0] if 'stock' in datos else '0'

            if id_producto:
                cursor = db_conn.cursor()
                cursor.execute(
                    "UPDATE productos SET nombre = ?, precio = ?, stock = ? WHERE id = ?",
                    (nombre, float(precio), int(stock), int(id_producto))
                )
                db_conn.commit()
            self.send_response(303)
            self.send_header('Location', '/dashboard')
            self.end_headers()

        elif ruta == '/eliminar':
            id_producto = datos.get('id')[0] if 'id' in datos else None
            if id_producto:
                cursor = db_conn.cursor()
                cursor.execute("DELETE FROM productos WHERE id = ?", (int(id_producto),))
                db_conn.commit()
            self.send_response(303)
            self.send_header('Location', '/dashboard')
            self.end_headers()

if __name__ == '__main__':
    puerto = 8000
    server = HTTPServer(('localhost', puerto), TiendaHandler)
    print(f"Servidor ejecutándose en http://localhost:{puerto}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor apagado con éxito.")