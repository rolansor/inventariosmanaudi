from django.shortcuts import render
from bs4 import BeautifulSoup
import requests
import re
from django.http import JsonResponse
from usuarios.templatetags.tags import control_acceso


@control_acceso('contabilidad')
def consulta_id(request):
    if request.method == 'POST':
        identification = request.POST.get('identification')
        if not identification:
            return JsonResponse({'error': 'El campo identificación es requerido'}, status=400)

        # URL base de la API del SRI
        base_url = "https://srienlinea.sri.gob.ec/movil-servicios/api/v1.0/deudas/porIdentificacion/"

        url = f"{base_url}{identification}"

        try:
            # Realizar la solicitud a la API del SRI
            response = requests.get(url)
            response.raise_for_status()  # Verifica si hay algún error en la respuesta

            dataInfo = response.json()  # Convertir la respuesta a JSON
            # Verificar si la respuesta tiene un contribuyente con RUC
            if 'contribuyente' in dataInfo:
                contribuyente = dataInfo['contribuyente']

                if contribuyente.get('tipoIdentificacion') == 'R':
                    try:
                        # Llamada a la función de scrapeo
                        ruc_data = scrape_ruc_data(identification)
                        dataInfo['infoRuc'] = ruc_data  # Añadir la información scrapeada
                    except Exception as e:
                        print(e)
                        dataInfo['infoRuc'] = {'error': 'Error al acceder a la página. Ruc no valido'}

            return JsonResponse({'data': dataInfo}, status=200)

        except requests.exceptions.HTTPError as http_err:
            return JsonResponse({'error': f'HTTP error: {http_err}'}, status=500)
        except Exception as err:
            return JsonResponse({'error': f'Error inesperado: {err}'}, status=500)
    else:
        return render(request, 'consulta_id.html')


# Función para reemplazar entidades HTML
def replace_html_entities(text):
    return text.replace('&aacute;', 'á').replace('&eacute;', 'é').replace('&iacute;', 'í') \
        .replace('&oacute;', 'ó').replace('&uacute;', 'ú').replace('&ntilde;', 'ñ') \
        .replace('&Aacute;', 'Á').replace('&Eacute;', 'É').replace('&Iacute;', 'Í') \
        .replace('&Oacute;', 'Ó').replace('&Uacute;', 'Ú').replace('&Ntilde;', 'Ñ')


# Función para normalizar texto
def normalize_text(text):
    return re.sub(r'[\u0300-\u036f]', '', text).replace('ñ', 'n').replace('Ñ', 'N')


# Función para extraer datos de una tabla
def extract_table_data(soup, selector):
    data = {}
    rows = soup.select(f'{selector} tr.impar')
    for index, row in enumerate(rows):
        columns = row.find_all('th') + row.find_all('td')
        if len(columns) == 4:
            row_data = {
                'numero_establecimiento': normalize_text(replace_html_entities(columns[0].get_text().strip())),
                'nombre_comercial': normalize_text(replace_html_entities(columns[1].get_text().strip())),
                'ubicacion_establecimiento': normalize_text(replace_html_entities(columns[2].get_text().strip())),
                'estado_establecimiento': normalize_text(replace_html_entities(columns[3].get_text().strip()))
            }
            data[f'establecimiento_{index}'] = row_data
    return data


# Función para hacer scraping
def scrape_ruc_data(ruc):
    base_url = f'https://srienlinea.sri.gob.ec/facturacion-internet/consultas/publico/ruc-datos2.jspa?ruc={ruc}'

    try:
        # Solicitar la página web
        response = requests.get(base_url)
        response.raise_for_status()

        # Analizar el contenido con BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')

        # Regex para extraer los datos de la tabla
        data = {}
        regex = re.compile(r'<th.*?>(.*?)<\/th>\s*<td.*?>(.*?)<\/td>', re.S)
        for match in regex.finditer(str(soup)):
            key = normalize_text(replace_html_entities(match.group(1).strip()))
            value = normalize_text(replace_html_entities(match.group(2).strip()))
            data[key] = value

        # Verificar si se encontraron datos
        if not data:
            raise ValueError('No se encontró la información del contribuyente.')

        # Extraer datos adicionales de la segunda tabla
        data['establecimientos'] = extract_table_data(soup, '.reporte')

        return data

    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error: {http_err}'}
    except Exception as err:
        return {'error': f'Error inesperado: {err}'}
