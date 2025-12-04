import re
import io
import base64
import html 
import matplotlib.pyplot as plt
from django.conf import settings

# 1. Set backend to non-interactive
plt.switch_backend('Agg')

def fix_image_paths(html_content):
    """ Converts /media/ URLs to file:// paths for WeasyPrint. """
    if not html_content: return ""
    
    media_url = settings.MEDIA_URL
    media_root = settings.MEDIA_ROOT
    media_root_str = str(media_root).replace('\\', '/')
    
    if media_url in html_content:
        base_replacement = f'file://{media_root_str}/'
        if base_replacement.endswith('//'): base_replacement = base_replacement[:-1]
        
        html_content = html_content.replace(f'src="{media_url}', f'src="{base_replacement}')
        html_content = html_content.replace(f"src='{media_url}", f"src='{base_replacement}")

    return html_content

def latex_to_base64(latex_content, style='inline'):
    """
    Renders LaTeX to a base64 image.
    """
    try:
        # 2. CONFIGURATION
        if style == 'block':
            # --- FIX IS HERE ---
            # Reduced font to 13 (closer to document text)
            # Reduced DPI to 110 (prevents image from being physically huge)
            font_size = 13  
            dpi_val = 110   
            css_class = "latex-block"
        else:
            # Inline relies on CSS height, so high quality is fine here
            font_size = 16  
            dpi_val = 150
            css_class = "latex-inline"

        # 3. CLEANING
        clean_content = html.unescape(latex_content) 
        clean_content = clean_content.replace('\xa0', ' ')

        # 4. SETUP MATPLOTLIB
        fig = plt.figure(figsize=(0.1, 0.1))
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['mathtext.fontset'] = 'dejavuserif'

        # 5. RENDER
        fig.text(0.5, 0.5, f"${clean_content}$", fontsize=font_size, ha='center', va='center')
        
        buf = io.BytesIO()
        # Keep pad_inches small to avoid extra whitespace
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.02, transparent=True, dpi=dpi_val)
        plt.close(fig)
        
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return f'<img src="data:image/png;base64,{img_str}" class="{css_class}" />'
        
    except Exception as e:
        print(f"LATEX ERROR: {e} | Content: {latex_content}")
        return f'<span style="color:red; font-weight:bold;">[Math Error]</span>'

def process_content_for_pdf(html_content):
    if not html_content: return ""
    
    html_content = fix_image_paths(html_content)
    
    pattern_block = r'\\\[(.*?)\\\]'
    def replacer_block(match):
        return latex_to_base64(match.group(1), style='block')
    html_content = re.sub(pattern_block, replacer_block, html_content, flags=re.DOTALL)

    pattern_inline = r'\#\#(.*?)\#\#'
    def replacer_inline(match):
        return latex_to_base64(match.group(1), style='inline')
    html_content = re.sub(pattern_inline, replacer_inline, html_content, flags=re.DOTALL)
    
    return html_content