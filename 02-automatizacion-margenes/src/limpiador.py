"""Módulo de Limpieza Textual y Clasificación Dinámica de Arquetipos.

Clasifica los productos según la taxonomía comercial de 30 subcategorías,
evaluando tokens de prenda, variantes de material y costo base del proveedor.
"""

from typing import Any, Dict, List, Optional
import pandas as pd

CONFIG_PRODUCTOS: Dict[str, Dict[str, Any]] = {
    # --- TEXTIL: CAMISAS ---
    "CAMISA_DENIM": {
        "nombre_comercial": "Camisa Denim / Jean",
        "macro_categoria": "TEXTIL", "subcategoria": "CAMISAS",
        "filtros_prenda": ["camisa", "blusa"],
        "filtros_material": ["denim", "jean", "gamarza", "rustico"]
    },
    "CAMISA_POPELINA": {
        "nombre_comercial": "Camisa Popelina",
        "macro_categoria": "TEXTIL", "subcategoria": "CAMISAS",
        "filtros_prenda": ["camisa", "blusa"],
        "filtros_material": ["popelina", "popeline", "popelin"]
    },
    "CAMISA_OXFORD": {
        "nombre_comercial": "Camisa Oxford",
        "macro_categoria": "TEXTIL", "subcategoria": "CAMISAS",
        "filtros_prenda": ["camisa", "blusa"],
        "filtros_material": ["oxford", "oxfor", "paracas", "san jacinto"]
    },

    # --- TEXTIL: CASACAS ---
    "CASACA_NYLON": {
        "nombre_comercial": "Casaca Nylon",
        "macro_categoria": "TEXTIL", "subcategoria": "CASACAS",
        "filtros_prenda": ["casaca", "chamarra"],
        "filtros_material": ["nylon", "nailon", "nailom"]
    },
    "CASACA_SOFTSHELL": {
        "nombre_comercial": "Casaca Softshell",
        "macro_categoria": "TEXTIL", "subcategoria": "CASACAS",
        "filtros_prenda": ["casaca", "chamarra"],
        "filtros_material": ["softshell", "softsel", "sofsel"]
    },
    "CASACA_TASLAN": {
        "nombre_comercial": "Casaca Taslan",
        "macro_categoria": "TEXTIL", "subcategoria": "CASACAS",
        "filtros_prenda": ["casaca", "chamarra", "corta viento", "impermeable"],
        "filtros_material": ["taslan", "taslam", "tazlan"]
    },

    # --- TEXTIL: POLOS ---
    "POLO_20_1": {
        "nombre_comercial": "Polo 20/1 / Camisero",
        "macro_categoria": "TEXTIL", "subcategoria": "POLOS",
        "filtros_prenda": ["polo"],
        "filtros_material": ["20/1", "20 o 1", "pique", "camisero"]
    },
    "POLO_24_1": {
        "nombre_comercial": "Polo 24/1",
        "macro_categoria": "TEXTIL", "subcategoria": "POLOS",
        "filtros_prenda": ["polo"],
        "filtros_material": ["24/1", "24 o 1", "jersey 24"]
    },
    "POLO_40_1": {
        "nombre_comercial": "Polo 40/1 Pima",
        "macro_categoria": "TEXTIL", "subcategoria": "POLOS",
        "filtros_prenda": ["polo"],
        "filtros_material": ["40/1", "pyma", "pima"]
    },
    "POLO_30_1": {
        "nombre_comercial": "Polo 30/1",
        "macro_categoria": "TEXTIL", "subcategoria": "POLOS",
        "filtros_prenda": ["polo", "remera"],
        "filtros_material": ["30/1", "jersey 30", "algodon"]
    },

    # --- TEXTIL: GORROS Y CHALECOS ---
    "GORRO_TASLAN": {
        "nombre_comercial": "Gorro Taslan",
        "macro_categoria": "TEXTIL", "subcategoria": "GORROS",
        "filtros_prenda": ["gorro", "gorra"],
        "filtros_material": ["taslan", "taslam", "tazlan"]
    },
    "GORRO_DRILL": {
        "nombre_comercial": "Gorro Drill",
        "macro_categoria": "TEXTIL", "subcategoria": "GORROS",
        "filtros_prenda": ["gorro", "gorra", "chavito", "visera"],
        "filtros_material": ["drill", "dril"]
    },
    "CHALECO": {
        "nombre_comercial": "Chaleco",
        "macro_categoria": "TEXTIL", "subcategoria": "CHALECOS",
        "filtros_prenda": ["chaleco"],
        "filtros_material": ["drill", "taslan", "puffer", "geologo", "reportero"]
    },

    # --- TEXTIL: PANTALONES Y OVERALLS ---
    "PANTALON_DENIM": {
        "nombre_comercial": "Pantalón Denim / Jean",
        "macro_categoria": "TEXTIL", "subcategoria": "PANTALONES",
        "filtros_prenda": ["pantalon", "pantalones", "jean"],
        "filtros_material": ["denim", "jean", "14 onzas"]
    },
    "PANTALON_DRILL": {
        "nombre_comercial": "Pantalón Drill",
        "macro_categoria": "TEXTIL", "subcategoria": "PANTALONES",
        "filtros_prenda": ["pantalon", "pantalones", "cargo"],
        "filtros_material": ["drill", "dril"]
    },
    "OVERALL_MAMELUCO": {
        "nombre_comercial": "Overall / Mameluco",
        "macro_categoria": "TEXTIL", "subcategoria": "INDUSTRIAL",
        "filtros_prenda": ["overall", "mameluco", "overol"],
        "filtros_material": []
    },
    "MANDIL": {
        "nombre_comercial": "Mandil / Delantal",
        "macro_categoria": "TEXTIL", "subcategoria": "INDUMENTARIA",
        "filtros_prenda": ["mandil", "delantal"],
        "filtros_material": []
    },
    "POLERA": {
        "nombre_comercial": "Polera / Hoodie",
        "macro_categoria": "TEXTIL", "subcategoria": "POLERAS",
        "filtros_prenda": ["polera", "hoodie", "sudadera"],
        "filtros_material": []
    },

    # --- MERCHANDISING Y BOLSAS ---
    "MERCH_KITS": {
        "nombre_comercial": "Kits y Welcome Packs",
        "macro_categoria": "MERCHANDISING", "subcategoria": "KITS",
        "filtros_prenda": ["kit", "pack", "set", "welcome pack"], "filtros_material": []
    },
    "MERCH_BOLSA_NOTEX": {
        "nombre_comercial": "Bolsas de Notex",
        "macro_categoria": "MERCHANDISING", "subcategoria": "BOLSAS",
        "filtros_prenda": ["notex", "cambrell"], "filtros_material": []
    },
    "MERCH_BOLSA_TOCUYO": {
        "nombre_comercial": "Bolsas de Tocuyo",
        "macro_categoria": "MERCHANDISING", "subcategoria": "BOLSAS",
        "filtros_prenda": ["tocuyo"], "filtros_material": []
    },
    "MERCH_BOLSA_PAPEL_OTROS": {
        "nombre_comercial": "Bolsas de Papel / Plástico",
        "macro_categoria": "MERCHANDISING", "subcategoria": "BOLSAS",
        "filtros_prenda": ["bolsa de papel", "bolsa de plastico", "bolsa couche", "bolsa rpet", "bolsa lyner"], "filtros_material": []
    },
    "MERCH_MOCHILAS_MALETINES": {
        "nombre_comercial": "Mochilas y Maletines",
        "macro_categoria": "MERCHANDISING", "subcategoria": "MOCHILAS",
        "filtros_prenda": ["mochila", "maletin", "canguro", "mochirrueda", "morral", "cooler"], "filtros_material": []
    },
    "MERCH_TOMATODO_TERMO_COMERCIAL": {
        "nombre_comercial": "Tomatodos y Termos Comerciales",
        "macro_categoria": "MERCHANDISING", "subcategoria": "DRINKWARE",
        "filtros_prenda": ["tomatodo", "termo", "thermo", "mug", "vaso termico"], "filtros_material": []
    },
    "MERCH_TOMATODO_TERMO": {
        "nombre_comercial": "Tomatodos y Termos",
        "macro_categoria": "MERCHANDISING", "subcategoria": "DRINKWARE",
        "filtros_prenda": ["tomatodo", "termo", "thermo", "mug", "vaso termico"], "filtros_material": []
    },
    "MERCH_TAZA_VASO": {
        "nombre_comercial": "Tazas y Vasos",
        "macro_categoria": "MERCHANDISING", "subcategoria": "TAZAS",
        "filtros_prenda": ["taza", "vaso", "chopp", "jarro"], "filtros_material": []
    },
    "MERCH_ALMOHADA_VIAJE": {
        "nombre_comercial": "Almohadillas de Viaje",
        "macro_categoria": "MERCHANDISING", "subcategoria": "VIAJE",
        "filtros_prenda": ["almohada", "almoada", "collarin", "antifaz"], "filtros_material": []
    },
    "MERCH_CARTUCHERA_NECESER": {
        "nombre_comercial": "Cartucheras y Neceseres",
        "macro_categoria": "MERCHANDISING", "subcategoria": "ORGANIZADORES",
        "filtros_prenda": ["cartuchera", "neceser", "organizador", "chimpunera"], "filtros_material": []
    },
    "MERCH_CUADERNO_LIBRETA": {
        "nombre_comercial": "Cuadernos y Libretas",
        "macro_categoria": "MERCHANDISING", "subcategoria": "PAPELERIA",
        "filtros_prenda": ["cuaderno", "libreta", "notebook", "agenda", "block"], "filtros_material": []
    },
    "MERCH_LAPICERO_UTILES": {
        "nombre_comercial": "Lapiceros y Útiles",
        "macro_categoria": "MERCHANDISING", "subcategoria": "ESCRITORIO",
        "filtros_prenda": ["lapicero", "lapiz", "boligrafo", "portapost it"], "filtros_material": []
    },
    "MERCH_LLAVERO_PIN": {
        "nombre_comercial": "Llaveros y Pines",
        "macro_categoria": "MERCHANDISING", "subcategoria": "ACCESORIOS",
        "filtros_prenda": ["llavero", "pin", "pines", "solapero", "parche bordado"], "filtros_material": []
    },
    "MERCH_ANTIESTRES": {
        "nombre_comercial": "Antiestrés",
        "macro_categoria": "MERCHANDISING", "subcategoria": "VARIOS",
        "filtros_prenda": ["antiestres", "antistress", "pelota antiestres"], "filtros_material": []
    },
    "MERCH_RESALTADOR": {
        "nombre_comercial": "Resaltadores",
        "macro_categoria": "MERCHANDISING", "subcategoria": "ESCRITORIO",
        "filtros_prenda": ["resaltador", "resaltadores"], "filtros_material": []
    },
    "MERCH_PUBLICIDAD_VISUAL": {
        "nombre_comercial": "Publicidad Visual",
        "macro_categoria": "MERCHANDISING", "subcategoria": "VISUAL",
        "filtros_prenda": ["banner", "roll screen", "backing", "afiche", "gigantografia"], "filtros_material": []
    },
    "MERCH_TECNOLOGIA_GADGETS": {
        "nombre_comercial": "Tecnología y Gadgets",
        "macro_categoria": "MERCHANDISING", "subcategoria": "TECNOLOGIA",
        "filtros_prenda": ["power bank", "powerbank", "cargador", "cable", "parlante", "usb", "memoria", "pop socket", "mouse pad"], "filtros_material": []
    },
    "MERCH_TROFEOS_PLACAS": {
        "nombre_comercial": "Trofeos y Placas",
        "macro_categoria": "MERCHANDISING", "subcategoria": "RECONOCIMIENTO",
        "filtros_prenda": ["trofeo", "placa", "reconocimiento"], "filtros_material": []
    },
    "MERCH_TOALLAS_TEXTIL_PROMO": {
        "nombre_comercial": "Toallas Promocionales",
        "macro_categoria": "MERCHANDISING", "subcategoria": "TEXTIL_PROMO",
        "filtros_prenda": ["toalla", "manta"], "filtros_material": []
    },
    "MERCH_RECREACION_Y_VARIOS": {
        "nombre_comercial": "Recreación y Varios",
        "macro_categoria": "MERCHANDISING", "subcategoria": "VARIOS",
        "filtros_prenda": ["funko", "peluche", "rompecabezas", "pastillero", "pisco", "lentes", "delantal", "cepillo", "paraguas", "wincha"], "filtros_material": []
    },
    "LOGISTICA_Y_SERVICIOS": {
        "nombre_comercial": "Servicios y Logística",
        "macro_categoria": "SERVICIOS", "subcategoria": "LOGISTICA",
        "filtros_prenda": ["servicio", "serv.", "envio", "instalacion", "movilidad"], "filtros_material": []
    },
    "MERCHANDISING_GENERAL": {
        "nombre_comercial": "Merchandising General",
        "macro_categoria": "MERCHANDISING", "subcategoria": "GENERAL",
        "filtros_prenda": ["caja", "tarjeta", "estuche"], "filtros_material": []
    }
}


def clasificar_producto_estricto(descripcion: Any, costo_prov: float = 0.0) -> Optional[str]:
    """Clasifica un producto evaluando tokens de prenda, variantes de material y costo base.

    Args:
        descripcion: Texto descriptivo del artículo.
        costo_prov: Costo unitario reportado por el proveedor o taller.

    Returns:
        Clave técnica del arquetipo comercial coincidente o None si la descripción es nula.
    """
    if not descripcion or pd.isna(descripcion):
        return None

    desc_lower = str(descripcion).lower().strip()
    desc_head = " ".join(desc_lower[:250].split()[:8])

    # Colador financiero especial para Drinkware
    if any(kw in desc_head for kw in ["tomatodo", "termo", "thermo", "mug", "vaso termico"]):
        return "MERCH_TOMATODO_TERMO_COMERCIAL" if float(costo_prov) < 8.0 else "MERCH_TOMATODO_TERMO"

    for arquetipo, config in CONFIG_PRODUCTOS.items():
        if arquetipo in ["MERCH_TOMATODO_TERMO_COMERCIAL", "MERCH_TOMATODO_TERMO", "MERCHANDISING_GENERAL"]:
            continue

        filtros_p: List[str] = config.get("filtros_prenda", [])
        filtros_m: List[str] = config.get("filtros_material", [])

        if filtros_p and any(p in desc_head for p in filtros_p):
            if filtros_m:
                if any(m in desc_lower for m in filtros_m):
                    return arquetipo
            else:
                return arquetipo

    if any(kw in desc_lower[:30] for kw in ["caja", "tarjeta", "estuche"]):
        return "MERCHANDISING_GENERAL"

    return "MERCHANDISING_GENERAL"