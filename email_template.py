#!/usr/bin/python
"""
Email template generator for Wallabot alerts.

This module provides functions to generate HTML and plain text email templates 
for Wallapop product alerts. It handles the formatting of product information
in a clean, responsive layout optimized for email clients.
"""

def generate_text_body(offers):
    """Generate plain text email body for offers.
    
    Args:
        offers: List of offer dictionaries containing product information
        
    Returns:
        String containing plain text email content
    """
    offers_text_array = [
        '{}\nprecio: {}\nlink: {}\nEstado: {}\nVendedor: {}\nValoraciones: {}\nNúm. Valoraciones: {}\nVentas: {}\nUbicación: {}\nEnvío: {}\nEstadísticas: Actualizado {}, {} visitas, {} favoritos\n\n'.format(
            n['titulo'], 
            n['precio'], 
            n['enlace'], 
            "Reservada" if n['reservada'] else "Disponible",
            n.get('seller_name', 'Sin nombre'),
            n.get('seller_rate', '0'),
            n.get('seller_number_of_rates', '0'),
            n.get('seller_sales', '0'),
            n.get('location', 'Ubicación desconocida'),
            n.get('shipping', 'No'),
            n.get('last_update', 'Desconocido'),
            n.get('views', '0'),
            n.get('favorites', '0')
        ) for n in offers
    ]
    
    return "".join([str(item) for item in offers_text_array])

def generate_html_item(item):
    """Generate HTML for a single offer item.
    
    Args:
        item: Dictionary containing product information
        
    Returns:
        String containing HTML for a single product card
    """
    return f'''<div style="border: 1px solid #e0e0e0; padding: 10px; margin: 8px 0; background-color: #fff;">
        <div style="display: flex; align-items: center;">
            <div style="flex: 0 0 120px; margin-right: 12px; display: flex; align-items: center; justify-content: center;">
                {f'<img src="{item.get("image_url")}" alt="{item["titulo"]}" style="max-width: 120px; max-height: 120px; object-fit: contain; border: 1px solid #f0f0f0;">' if item.get("image_url") else '<div style="width: 120px; height: 120px; background-color: #f7f7f7; display: flex; align-items: center; justify-content: center; text-align: center; color: #777; font-size: 12px;">No imagen</div>'}
            </div>
            <div style="flex: 1;">
                <h2 style="margin-top: 0; margin-bottom: 4px; color: #000; font-size: 15px;"><a href="{item['enlace']}">{item['titulo']}</a></h2>
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <p style="font-size: 16px; font-weight: bold; color: #e4545e; margin: 0 12px 0 0;">{item['precio']}</p>
                    <span style="font-size: 12px; color: {'"#555"' if item['reservada'] else '"#2e7d32"'};">{"Reservada" if item['reservada'] else "Disponible"}</span>
                </div>
                <div style="margin-top: 4px;">
                    <p style="margin: 2px 0; font-size: 12px;"><strong>👤 {item.get('seller_name', 'Sin nombre')}</strong> | 📍 {item.get('location', 'Ubicación desconocida')}</p>
                    <p style="margin: 2px 0; font-size: 12px;"><strong>⭐ {item.get('seller_rate', '0')}</strong> {item.get('seller_number_of_rates', '0')} valoraciones | 📊 {item.get('seller_sales', '0')}</p>
                    <p style="margin: 2px 0; font-size: 12px;"><strong>🚚 Envío:</strong> {item.get('shipping', 'No')}</p>
                    <p style="margin: 2px 0; font-size: 12px;">📈 {item.get('last_update', 'Desconocido')} | 👁️ {item.get('views', '0')} | ❤️ {item.get('favorites', '0')}</p>
                </div>
            </div>
        </div>
    </div>'''

def generate_html_body(offers, title="Nuevas ofertas en Wallapop", intro="Se han encontrado las siguientes ofertas:", footer=""):
    """Generate HTML email body for offers with custom title and intro.
    
    Args:
        offers: List of offer dictionaries containing product information
        title: Custom title for the email
        intro: Introduction text for the email
        footer: Optional footer text
        
    Returns:
        String containing complete HTML email body
    """
    # Generate HTML for each offer
    offers_html = "".join([generate_html_item(offer) for offer in offers])
    
    # Combine with header and footer
    html = f"""
    <html>
    <head>
        <meta name="color-scheme" content="light">
        <meta name="supported-color-schemes" content="light">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.3; color: #000; max-width: 700px; margin: 0 auto; padding: 12px; background-color: #fff !important;">
        <div style="background-color: #fff !important; padding: 15px; border-radius: 8px;">
            <h1 style="color: #000; border-bottom: 1px solid #e0e0e0; padding-bottom: 6px; font-size: 18px; margin-bottom: 8px; background-color: #fff !important;">{title}</h1>
            <p style="font-size: 13px; margin-bottom: 10px; background-color: #fff !important;">{intro}</p>
            <div style="background-color: #fff !important;">
                {offers_html}
            </div>
            {f'<p style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #e0e0e0; font-size: 11px; color: #777; background-color: #fff !important;">{footer}</p>' if footer else ''}
        </div>
    </body>
    </html>
    """
    
    return html 