"""Módulo de Constantes y Taxonomía Comercial del Sistema.

Centraliza las rutas por defecto, hojas de Excel excluidas y la estructura
jerárquica de la taxonomía comercial (Macrocategorías -> Subcategorías -> Tags/Exclusiones).

Principios aplicados:
    - Single Responsibility (SRP): Definición pura de datos y constantes del sistema.
    - DRY: Evita duplicación de categorías y arregla sobreescrituras en diccionarios.
"""

from pathlib import Path
from typing import Any, Dict, List

DEFAULT_EXCEL_FOLDER: str = str(
    (Path(__file__).resolve().parent.parent.parent / "data").as_posix()
)

# Taxonomía comercial completa del sistema
MACRO_CATEGORIAS: Dict[str, Dict[str, Any]] = {
    "Artículos de Hogar y Cocina": {
        "global_exclude": [],
        "subcategorias": {
            "textiles de hogar y limpieza": [
                {"tags": ["almohada", "almohadas", "almohada de viaje", "almoada inflable"], "exclude": []},
                {"tags": ["ambientador"], "exclude": []},
                {"tags": ["aromatizador"], "exclude": []},
                {"tags": ["cepillo"], "exclude": []},
                {"tags": ["cojin", "cojines"], "exclude": []},
                {"tags": ["costurero"], "exclude": []},
                {"tags": ["espejo"], "exclude": []},
                {"tags": ["franela"], "exclude": []},
                {"tags": ["lustrador"], "exclude": []},
                {"tags": ["mopa"], "exclude": []},
                {"tags": ["paño", "paños"], "exclude": []},
                {"tags": ["set de baño"], "exclude": []},
                {"tags": ["set de brochas"], "exclude": []},
                {"tags": ["set de costura"], "exclude": []},
                {"tags": ["set de manicure"], "exclude": []},
                {"tags": ["toalla", "toallas", "toallon", "toallones", "toalla de mano", "toalla de baño"], "exclude": []},
            ],
            "utensilios y cocina": [
                {"tags": ["bandeja"], "exclude": []},
                {"tags": ["cafetera", "cafeteras", "prensa francesa"], "exclude": []},
                {"tags": ["cubierto", "cubiertos"], "exclude": []},
                {"tags": ["cuchara", "cucharas"], "exclude": []},
                {"tags": ["dispensador"], "exclude": []},
                {"tags": ["parrilla"], "exclude": []},
                {"tags": ["sacacorcho"], "exclude": []},
                {"tags": ["servilleta", "servilletas"], "exclude": []},
                {"tags": ["set de vino", "set de vinos"], "exclude": []},
                {"tags": ["utensilio", "utensilios"], "exclude": []},
            ],
            "tomatodos y botellas": [
                {"tags": ["botella", "botellas", "caramañola", "caramañolas"], "exclude": []},
                {"tags": ["shaker", "shakers"], "exclude": []},
                {"tags": ["termo", "termos", "termito", "termo bullet", "thermo", "thermos"], "exclude": []},
                {"tags": ["tomatodo", "tomatodos", "tomatodo ergo", "toma todo", "toma todo ergo"], "exclude": []},
            ],
            "vasos, tazas y mugs": [
                {"tags": ["calentador tazas"], "exclude": []},
                {"tags": ["chop", "chopp"], "exclude": []},
                {"tags": ["copa", "copas", "copa champagne", "copa vino"], "exclude": []},
                {"tags": ["drinkware"], "exclude": []},
                {"tags": ["jarro", "jarros", "jarro mug", "jarro mug moka", "jarro mug fibra de trigo", "moke", "mokes"], "exclude": []},
                {"tags": ["mug", "mugs", "mug moka", "mug fibra de trigo", "travel mug", "electronic mug", "cofee mug", "mug briel", "mug acero", "mug doble pared", "mug rainbow", "mug transparente", "super mug"], "exclude": []},
                {"tags": ["pocillo"], "exclude": []},
                {"tags": ["taza", "tazas", "taza blanca", "taza cónica", "taza bombeada", "tazas bombeadas"], "exclude": []},
                {"tags": ["vaso", "vasos", "vaso termico", "vasos termicos", "vaso cervecero", "vaso kero", "vaso tecnopor", "vaso aleman"], "exclude": []},
            ],
        },
    },
    "Artículos de Oficina y Escritorio": {
        "global_exclude": [],
        "subcategorias": {
            "agendas y planificadores": [
                {"tags": ["agenda", "agendas"], "exclude": []},
                {"tags": ["diario", "diarios"], "exclude": []},
                {"tags": ["planificador", "planificadores"], "exclude": []},
            ],
            "credenciales y displays": [
                {"tags": ["fotocheck", "fotochecks"], "exclude": []},
                {"tags": ["gafete", "gafetes", "gafete bronce"], "exclude": []},
                {"tags": ["identificador", "identificadores"], "exclude": []},
                {"tags": ["jalavista pvc"], "exclude": []},
                {"tags": ["marbete"], "exclude": []},
                {"tags": ["marco foto", "marcos foto", "marco de foto", "marco de fotometal", "marco de fotoplastico", "marco de fotos", "marco para foto importad.", "marco"], "exclude": []},
                {"tags": ["porta afiche"], "exclude": []},
                {"tags": ["porta carnet", "porta carnets"], "exclude": []},
                {"tags": ["porta credencial", "porta credenciales"], "exclude": []},
                {"tags": ["porta flyer", "porta flyers"], "exclude": []},
                {"tags": ["porta foto", "porta fotos", "portafoto", "porta foto madera"], "exclude": []},
                {"tags": ["porta nombre", "porta nombres"], "exclude": []},
                {"tags": ["portafotochecks", "yoyo porta fotocheck"], "exclude": []},
                {"tags": ["portaretrato", "porta retrato", "portarretrato", "porta retratos"], "exclude": []},
                {"tags": ["tarjeta personal", "tarjetas personales"], "exclude": []},
            ],
            "cuadernos y libretas": [
                {"tags": ["anillado", "anillados"], "exclude": []},
                {"tags": ["bloc de notas"], "exclude": []},
                {"tags": ["block", "blocks", "mini block"], "exclude": []},
                {"tags": ["cuadernillo", "cuadernillos"], "exclude": []},
                {"tags": ["cuaderno", "cuadernos", "cudernos", "cuadernos empresariales", "mini cuaderno"], "exclude": []},
                {"tags": ["libreta", "libretas", "eco libreta", "mini libreta", "libreta eco", "libreta ecoligica", "libreta post it", "libreta tapa imantada"], "exclude": []},
                {"tags": ["notebook", "journal", "journals"], "exclude": []},
                {"tags": ["notepad", "notepads"], "exclude": []},
                {"tags": ["taco de notas", "taco", "taco encolado", "tacos", "tacos pegados"], "exclude": []},
            ],
            "escritorio y organizacion": [
                {"tags": ["calculadora"], "exclude": []},
                {"tags": ["calendario", "caledndario"], "exclude": []},
                {"tags": ["clip"], "exclude": []},
                {"tags": ["engrapador", "engrampador"], "exclude": []},
                {"tags": ["escritorio"], "exclude": []},
                {"tags": ["escultura imantada", "escultura magnética"], "exclude": []},
                {"tags": ["kit ejecutivo"], "exclude": []},
                {"tags": ["kit escolar"], "exclude": []},
                {"tags": ["kit escritorio", "mini set escritorio", "set de escritorio"], "exclude": []},
                {"tags": ["mouse pad", "mousepad", "mini mouse pad", "alfombrilla", "alfombrillas", "tapete de escritorio"], "exclude": []},
                {"tags": ["organizador", "organizadores"], "exclude": []},
                {"tags": ["porta celular", "soporte celular", "portacelular", "silla porta celular"], "exclude": []},
                {"tags": ["porta clip", "portaclip"], "exclude": []},
                {"tags": ["porta documentos", "portadocumentos"], "exclude": []},
                {"tags": ["porta lapiz", "portalapicero", "porta lapicero", "portaboligrafo"], "exclude": []},
                {"tags": ["porta nota", "porta notas", "portanota", "portanotas", "memo pad", "memo clip", "memoclip", "porta memo"], "exclude": []},
                {"tags": ["porta papel"], "exclude": []},
                {"tags": ["porta post it", "post it poster"], "exclude": []},
                {"tags": ["porta taco", "portataco"], "exclude": []},
                {"tags": ["porta tarjeta", "porta tarjetas", "portatarjeta", "portatarjetas", "set portatarjeta", "set porta tarjetas", "set portatarjetas"], "exclude": []},
                {"tags": ["porta usb"], "exclude": []},
                {"tags": ["posavaso", "posavasos"], "exclude": []},
                {"tags": ["regla", "reglas", "regla escolar", "regla poliestireno", "regla calculadora", "regla lupa", "reglas promocionales"], "exclude": []},
                {"tags": ["reloj digital con tarjetero", "mini reloj digital con tarjetero"], "exclude": []},
                {"tags": ["repisa", "repisas"], "exclude": []},
                {"tags": ["separador"], "exclude": []},
                {"tags": ["sujetador"], "exclude": []},
                {"tags": ["tablero"], "exclude": []},
                {"tags": ["tarjetero", "tarjeteros", "tarjetero importados"], "exclude": []},
            ],
            "lapiceros y escritura": [
                {"tags": ["boligrafo", "boligrafos", "boligraforesaltador"], "exclude": []},
                {"tags": ["esfero", "esferos"], "exclude": []},
                {"tags": ["lapicero", "lapiceros", "lap-", "lap.", "lap. plast.", "lapicero aguja", "lapicero madera", "lapicero bamboo", "lapicero atomizador", "lapicero linterna", "lapicero puntero laser", "lapicero con punta de goma", "lapicero resaltador", "lapicero jeringa", "lap usb"], "exclude": []},
                {"tags": ["lapiz", "lapices", "lapiz eco", "lapiz natural", "lapiz blanco"], "exclude": []},
                {"tags": ["marcador", "marcadores", "marcadores de texto"], "exclude": []},
                {"tags": ["pluma", "plumas"], "exclude": []},
                {"tags": ["plumon", "plumones"], "exclude": []},
                {"tags": ["resaltador", "resaltadores", "set resaltador"], "exclude": []},
                {"tags": ["rollerball"], "exclude": []},
            ],
        },
    },
    "Bolsos y Equipaje": {
        "global_exclude": [],
        "subcategorias": {
            "bolsos, canguros y maletines": [
                {"tags": ["bolso", "bolsos", "bandolera", "bandoleras"], "exclude": []},
                {"tags": ["canguro", "canguros", "riñonera", "riñoneras", "koala", "koalas", "kit canguro"], "exclude": []},
                {"tags": ["chimpunera", "chimpuneras", "portacalzado", "portacalzados"], "exclude": []},
                {"tags": ["lonchera", "loncheras"], "exclude": []},
                {"tags": ["maleta", "maletas"], "exclude": []},
                {"tags": ["maletin", "maletines"], "exclude": []},
            ],
            "mochilas y morrales": [
                {"tags": ["mochila", "mochilas", "backpack", "backpacks", "mochila navideña", "mochila funcional", "mochila portalaptop"], "exclude": []},
                {"tags": ["morral", "morrales", "morral de espalda"], "exclude": []},
            ],
            "estuches, cartucheras y neceseres": [
                {"tags": ["billetera"], "exclude": []},
                {"tags": ["cartuchera", "cartucheras", "portautiles"], "exclude": []},
                {"tags": ["estuche", "estuches", "esctuche", "estuche vino", "kit estuche"], "exclude": []},
                {"tags": ["monedero", "monederos", "monederos promocionales"], "exclude": []},
                {"tags": ["neceser", "neceseres", "bolso de aseo", "porta cosméticos"], "exclude": []},
                {"tags": ["portafolio calculadora"], "exclude": []},
                {"tags": ["sencillera"], "exclude": []},
            ],
        },
    },
    "Empaques y Packaging": {
        "global_exclude": [],
        "subcategorias": {
            "bolsas y packaging": [
                {"tags": ["bolsa", "bolsas", "bolsa papel"], "exclude": []},
                {"tags": ["funda", "fundas", "funda cartón", "funda pana"], "exclude": []},
                {"tags": ["papel de regalo"], "exclude": []},
                {"tags": ["tote", "totes"], "exclude": []},
            ],
            "cajas y empaques": [
                {"tags": ["bombonera", "bomboneras"], "exclude": []},
                {"tags": ["caja", "cajas"], "exclude": []},
                {"tags": ["canasta", "canastas", "canasta navideña"], "exclude": []},
                {"tags": ["cinta lazo"], "exclude": []},
                {"tags": ["empaque", "empaques", "packaging"], "exclude": []},
            ],
        },
    },
    "Imprenta y Papelería Corporativa": {
        "global_exclude": [],
        "subcategorias": {
            "catalogos y revistas": [
                {"tags": ["catalogo", "catalogos"], "exclude": []},
                {"tags": ["manual corporativo", "reglamento"], "exclude": []},
                {"tags": ["revista", "revistas"], "exclude": []},
            ],
            "folders y carpetas": [
                {"tags": ["carpeta"], "exclude": []},
                {"tags": ["folder", "folderes", "folder corp."], "exclude": []},
                {"tags": ["pionner"], "exclude": []},
            ],
            "hojas y papeleria corporativa": [
                {"tags": ["hoja membretada", "hojas", "hoja corporativas", "hoja informativa", "carta"], "exclude": []},
                {"tags": ["sobre", "sobres", "sobres con fondo blanco", "sobre carta blanca", "sobre oficio"], "exclude": []},
                {"tags": ["tarjeta", "tarjetas", "tarjeta usb", "tarjeta invitacion", "tarjeta navidad", "tarjetas navideñas", "tarjetas personales", "tarjetas presentacion", "tarjeton"], "exclude": []},
                {"tags": ["ticket", "tickets bond"], "exclude": []},
            ],
            "impresos y piezas promocionales": [
                {"tags": ["afiche", "afiches", "afiche pvc"], "exclude": []},
                {"tags": ["almanaque"], "exclude": []},
                {"tags": ["banner", "banderola", "bandera"], "exclude": []},
                {"tags": ["brochure", "diptico", "triptico", "tripticos"], "exclude": []},
                {"tags": ["cinta metrica"], "exclude": []},
                {"tags": ["corporeo", "letrero"], "exclude": []},
                {"tags": ["flyer", "flyers", "volante", "volantes"], "exclude": []},
                {"tags": ["individual", "individuales"], "exclude": []},
                {"tags": ["table tents"], "exclude": []},
            ],
        },
    },
    "Merchandising y Promocionales": {
        "global_exclude": [],
        "subcategorias": {
            "llaveros": [
                {"tags": ["llavero", "llaveros", "keychain", "keychains", "mini llavero", "llavero destapador", "llavero linterna", "llavero casco", "llavero antiestrés", "llavero pvc", "llavero espejo", "llavero visual", "llavero inyectable", "llavero microinyectable", "llavero lapicero", "llavero microporoso", "llavero multiusos", "llavero pill box", "llavero laser", "llavero puntero laser", "llavero silver", "llavero wincha"], "exclude": []},
            ],
            "pines y prendedores": [
                {"tags": ["boton", "botones", "botones publicitarios"], "exclude": []},
                {"tags": ["insignia", "insignias"], "exclude": []},
                {"tags": ["pin", "pines"], "exclude": []},
                {"tags": ["prendedor", "prendedores", "broche", "broches"], "exclude": []},
                {"tags": ["pulsera", "pulseras", "pulsera caucho", "pulsera silicona", "pulsera usb"], "exclude": []},
            ],
            "placas y reconocimientos": [
                {"tags": ["imantado", "imantados", "imantal promocional", "mariposa con iman"], "exclude": []},
                {"tags": ["placa", "placas", "placa grabada", "plaquita"], "exclude": []},
                {"tags": ["reconocimiento", "reconocimientos"], "exclude": []},
            ],
            "stickers y adhesivos": [
                {"tags": ["etiqueta", "etiquetas"], "exclude": []},
                {"tags": ["sticker", "stickers", "sticker vinil", "sticker publicitarios"], "exclude": []},
            ],
            "trofeos y medallas": [
                {"tags": ["alcancia"], "exclude": []},
                {"tags": ["antiestres", "antistress", "bolas antiestress", "dr antiestres", "muneco antiestres", "masajeador estrella"], "exclude": []},
                {"tags": ["arbolito"], "exclude": []},
                {"tags": ["basemetalicos"], "exclude": []},
                {"tags": ["brush pocket set"], "exclude": []},
                {"tags": ["bugucela", "corneta", "matracones", "pandereta"], "exclude": []},
                {"tags": ["clips porta lente"], "exclude": []},
                {"tags": ["colgadores", "colgantes"], "exclude": []},
                {"tags": ["copa", "copas"], "exclude": []},
                {"tags": ["corta puros"], "exclude": []},
                {"tags": ["destapador", "destapadores"], "exclude": []},
                {"tags": ["flor sol"], "exclude": []},
                {"tags": ["fosforos"], "exclude": []},
                {"tags": ["galardon", "galardones", "premio", "premios", "condecoracion", "condecoraciones", "muñecos navideños", "muñecos", "bombones", "caramelos", "chocolates", "galletas de la fortuna", "kekes publicitarios", "kekes", "huevos de pascua", "pack muffins", "pack potpourri", "paneton", "panetones", "kit ecológico", "kit viajero", "pack ecológico", "set viajero"], "exclude": []},
                {"tags": ["gancho"], "exclude": []},
                {"tags": ["gel antibacterial"], "exclude": []},
                {"tags": ["globo", "globos", "globo publicitarios", "globos con helio", "paliglobo"], "exclude": []},
                {"tags": ["gondola"], "exclude": []},
                {"tags": ["herramientero", "casco", "multiherramientero", "mini herramientero", "mini kit multiherramiententa", "set de herramientas", "set herramientero", "navaja", "navajas"], "exclude": []},
                {"tags": ["juego", "juegos", "michi", "desestresante", "jenga", "jenga madera", "jenga mdf", "ajedrez", "cubo", "frisbee", "pelota", "rompecabeza", "rompecabezas"], "exclude": []},
                {"tags": ["limpia"], "exclude": []},
                {"tags": ["medalla", "medallas", "presea", "preseas"], "exclude": []},
                {"tags": ["medidor de aire para neumaticos", "medidor de aire para neumáticos plasticos"], "exclude": []},
                {"tags": ["mini mug", "mini stickies", "pocket stickies", "notas adhesivas"], "exclude": []},
                {"tags": ["pack estuche montacarga", "pack para autos"], "exclude": []},
                {"tags": ["paletas"], "exclude": []},
                {"tags": ["paraguas", "sombrilla", "sombrillas", "cooler", "radio cooler", "flotador", "mesa de playa", "mesita de playa", "silla de playa"], "exclude": []},
                {"tags": ["pases"], "exclude": []},
                {"tags": ["pastillero"], "exclude": []},
                {"tags": ["pisapapel"], "exclude": []},
                {"tags": ["pizarra"], "exclude": []},
                {"tags": ["tapasol", "tapasol colapsible", "tapasol para autos"], "exclude": []},
                {"tags": ["tapizon"], "exclude": []},
                {"tags": ["trofeo", "trofeos", "trofeos de vidrio"], "exclude": []},
                {"tags": ["wincha", "wincha cuadrada", "wincha multiusos", "wincha redonda"], "exclude": []},
            ],
        },
    },
    "Prendas de Vestir y Textil": {
        "global_exclude": ["audifono", "bolso", "cargador", "identificador", "lapicero", "paño", "pañuelo", "auto"],
        "subcategorias": {
            "camisas y blusas": [
                {"tags": ["blusa", "blusas", "camisas / blusas happyland"], "exclude": []},
                {"tags": ["camisa", "camisas", "camisa manga larga"], "exclude": []},
            ],
            "casacas, chamarras y abrigos": [
                {"tags": ["abrigo", "abrigos", "parka", "parkas", "sobretodo", "sobretodos", "gabardina", "gabardinas", "prendas de invierno"], "exclude": []},
                {"tags": ["casaca", "casacas", "chamarra", "chamarras", "jacket", "jackets", "chaqueta", "chaquetas", "cortavientos", "casaca cortavientos", "rompevientos"], "exclude": []},
                {"tags": ["poncho", "poncho impermeable"], "exclude": []},
            ],
            "chalecos": [
                {"tags": ["chaleco", "chalecos", "gilet", "gilets", "chalecos tacticos", "chaleco corporativo", "chaleco corporativo acolchado", "chalecos polar", "chalecos promocional"], "exclude": []},
            ],
            "chalinas y accesorios de frio": [
                {"tags": ["chalina", "chalinas", "bufanda", "bufandas"], "exclude": []},
                {"tags": ["cuello polar"], "exclude": []},
                {"tags": ["pañuelo", "pañueleta"], "exclude": []},
            ],
            "gorros, vinchas y viseras": [
                {"tags": ["gorro", "gorros", "gorra", "gorras", "beanie", "beanies", "gorro carbonero", "gorrodrill", "gorro trucker", "gorros bull", "gorros safari", "gorros tapanuca", "chullo", "chullos"], "exclude": []},
                {"tags": ["pasamontaña", "pasamontañas", "balaclava"], "exclude": []},
                {"tags": ["vincha", "vinchas"], "exclude": []},
                {"tags": ["visera", "vicera", "viseras", "viceras", "viseras deportivas", "visera promocional"], "exclude": []},
            ],
            "mamelucos y overoles": [
                {"tags": ["disfraz", "disfraz duende", "disfraz papa noel", "disfraz papa Noel"], "exclude": []},
                {"tags": ["mameluco", "mamelucos", "overol", "overoles", "overall", "enterizo", "enterizos", "uniforme"], "exclude": []},
            ],
            "mandiles y delantales": [
                {"tags": ["mandil", "mandiles", "delantal", "delantales", "tablier", "tabliers"], "exclude": []},
            ],
            "pantalones, shorts y bermudas": [
                {"tags": ["bermuda", "bermudas"], "exclude": []},
                {"tags": ["pantalon", "pantalones", "pantalon jean", "pantaloneta"], "exclude": []},
                {"tags": ["short", "shorts"], "exclude": []},
            ],
            "poleras, buzos y sudaderas": [
                {"tags": ["buzo", "buzos"], "exclude": []},
                {"tags": ["polera", "poleras", "polera polar", "sudadera", "sudaderas", "hoodie", "hoodies"], "exclude": []},
            ],
            "polos y camisetas": [
                {"tags": ["bividi"], "exclude": []},
                {"tags": ["camiseta", "camise", "polo algodon cuello camisero", "polo algodon cuello redondo", "polo algodon cuello v", "polo algodon cuello pique", "polos camisero", "polo deportivo", "polos cuello camisero", "polos cuello redondo", "polos cuello v", "polos cuello pique", "polo algodón", "polo algodón cuello camisero", "polo algodón cuello redondo", "polo algodón cuello v", "polo algodón cuello pique"], "exclude": []},
            ],
        },
    },
    "Tecnología y Gadgets": {
        "global_exclude": [],
        "subcategorias": {
            "tecnologia y gadgets": [
                {"tags": ["adaptador", "adaptadores", "mini bluetooth"], "exclude": []},
                {"tags": ["audifono", "audifonos"], "exclude": []},
                {"tags": ["cargador", "cargadores", "cargador para auto"], "exclude": []},
                {"tags": ["dvd"], "exclude": []},
                {"tags": ["encendedor"], "exclude": []},
                {"tags": ["laser"], "exclude": []},
                {"tags": ["linterna", "limterna", "mini linterna"], "exclude": []},
                {"tags": ["memoria usb", "usb", "memorias usb"], "exclude": []},
                {"tags": ["mouse"], "exclude": []},
                {"tags": ["parlante", "parlantes", "parlante bluetooth", "speake bluetooth"], "exclude": []},
                {"tags": ["power bank"], "exclude": []},
                {"tags": ["puntero laser", "punteros laser"], "exclude": []},
                {"tags": ["radio"], "exclude": []},
                {"tags": ["robot usb"], "exclude": []},
                {"tags": ["set de accesorios de pc"], "exclude": []},
            ],
            "relojes": [
                {"tags": ["reloj", "relojes", "reloj de pared", "reloj digital", "reloj promocional", "reloj escritorio", "reloj multiuso", "reloj porta", "reloj rompecabezas", "reloj swarovski", "reloj vip"], "exclude": []},
            ],
        },
    },
}

# Hojas de Excel omitidas por defecto durante la inspección
HOJAS_EXCLUIDAS: List[str] = [
    "criterios",
    "tallas",
    "cronograma",
    "datos",
    "deuda",
    "produccion",
    "proveedor",
    "proveedores",
    "costo de proyecto",
]